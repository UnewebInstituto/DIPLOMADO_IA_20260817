#!/usr/bin/env python
"""Comparativa de rendimiento: Ollama (local, Llama 3) vs Gemini (nube) sobre un PDF.

Ambos motores reciben EXACTAMENTE el mismo prompt (un solo mensaje de usuario), con
temperatura 0.2 y el mismo tope de tokens de salida. Se mide el tiempo de cada llamada.

Uso:
    python benchmark_ollama_vs_gemini.py --pdf cien_anios_de_soledad.pdf
    python benchmark_ollama_vs_gemini.py --pdf novela.pdf --fragmentos 1      # prueba rápida
"""
import argparse, csv, json, os, pathlib, re, statistics, sys, time, unicodedata

from pypdf import PdfReader

TEMPERATURA = 0.2
NUM_CTX = 8192            # ventana de Ollama: debe caber el prompt (un fragmento de ~4000 caracteres usa ~1500 tokens)

TAREAS = [
    ("resumen",
     "Resume en 3 líneas el siguiente fragmento de una novela:\n\n{frag}"),
    ("personajes",
     "Lista los personajes que aparecen en el siguiente fragmento y, en una frase, su rol o relación "
     "con los demás. Responde solo con la lista.\n\n{frag}"),
    ("comprension",
     "Lee el siguiente fragmento y responde en máximo 2 oraciones: ¿qué evento principal ocurre y qué "
     "consecuencia tiene?\n\n{frag}"),
    ("estilo",
     "Describe en un párrafo de máximo 5 líneas el tono y los recursos literarios más notables del "
     "siguiente fragmento:\n\n{frag}"),
    ("extraccion_json",
     "Del siguiente fragmento extrae los datos y devuélvelos SOLO como JSON válido, sin texto adicional "
     "ni bloques de código, con las claves: \"personajes\" (lista de nombres), \"lugares\" (lista) y "
     "\"tiempo\" (texto breve, o null si no se indica).\n\n{frag}"),
]

COLUMNAS = ["id", "tarea", "modelo", "segundos", "fragmento", "repeticion", "modelo_id",
            "tokens_entrada", "tokens_salida", "tokens_razonamiento", "tokens_por_seg",
            "carga_s", "temperatura_enviada", "json_valido", "respuesta"]


# ---------------------------------------------------------------- PDF -> fragmentos
def extraer_texto(ruta):
    lector = PdfReader(str(ruta))
    texto = "\n".join((p.extract_text() or "") for p in lector.pages)
    texto = unicodedata.normalize("NFKC", texto)
    texto = re.sub(r"-\n(\w)", r"\1", texto)           # une palabras cortadas por guion
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip(), len(lector.pages)


def seleccionar_fragmentos(texto, n, chars, desde=0.10, hasta=0.90):
    """n fragmentos de ~chars caracteres, repartidos de forma uniforme y determinista en el cuerpo del libro."""
    fragmentos = []
    for i in range(n):
        frac = desde + (hasta - desde) * (i + 0.5) / n
        ini = int(len(texto) * frac)
        m = re.search(r"[.!?»\"]\s+|\n", texto[ini:ini + 400])      # empieza en un límite de oración
        if m:
            ini += m.end()
        fin = min(ini + chars, len(texto))
        corte = max(texto.rfind(". ", ini, fin), texto.rfind("\n", ini, fin))
        if corte > ini + chars * 0.6:                               # termina en un límite de oración
            fin = corte + 1
        fragmentos.append(texto[ini:fin].strip())
    return fragmentos


def construir_casos(fragmentos):
    casos, n = [], 1
    for f_idx, frag in enumerate(fragmentos, start=1):
        for tarea, plantilla in TAREAS:
            casos.append({"id": n, "tarea": tarea, "fragmento": f_idx, "prompt": plantilla.format(frag=frag)})
            n += 1
    return casos


# ---------------------------------------------------------------- motores
def _campo(r, nombre):
    try:
        return r[nombre]
    except (KeyError, TypeError, AttributeError):
        return getattr(r, nombre, None)


def consultar_local(prompt, modelo, max_tokens):
    """Ollama. Devuelve dict con texto, segundos y métricas."""
    import ollama
    t0 = time.perf_counter()
    r = ollama.chat(model=modelo,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": TEMPERATURA, "num_ctx": NUM_CTX, "num_predict": max_tokens})
    seg = time.perf_counter() - t0
    carga = _campo(r, "load_duration")
    return {"texto": r["message"]["content"], "seg": seg,
            "tin": _campo(r, "prompt_eval_count"), "tout": _campo(r, "eval_count"), "razon": None,
            "carga": round(carga / 1e9, 2) if carga else None, "temp": TEMPERATURA}


class Nube:
    """Gemini. Si el modelo ya no admite `temperature` (parámetro de muestreo deprecado en los
    modelos Gemini 3.5/3.6), se reintenta sin él y se deja constancia en el CSV."""
    def __init__(self, modelo, thinking_level=None):
        from google import genai
        self.genai, self.modelo = genai, modelo
        self.cliente = genai.Client()                   # lee GEMINI_API_KEY o GOOGLE_API_KEY
        self.thinking_level = thinking_level
        self.enviar_temp = True

    def _llamar(self, prompt, max_tokens, con_temp):
        from google.genai import types
        cfg = {"max_output_tokens": max_tokens + 1000}  # margen: el razonamiento interno consume del tope
        if con_temp:
            cfg["temperature"] = TEMPERATURA
        if self.thinking_level:
            cfg["thinking_config"] = types.ThinkingConfig(thinking_level=self.thinking_level)
        t0 = time.perf_counter()
        r = self.cliente.models.generate_content(model=self.modelo, contents=prompt,
                                                 config=types.GenerateContentConfig(**cfg))
        return r, time.perf_counter() - t0

    def consultar(self, prompt, max_tokens):
        for intento in range(4):                         # reintentos ante límites de velocidad (429)
            try:
                try:
                    r, seg = self._llamar(prompt, max_tokens, self.enviar_temp)
                except Exception as e:
                    if self.enviar_temp and "temperature" in str(e).lower():
                        print("\n[AVISO] Gemini rechazó 'temperature'; se continúa sin ella (queda registrado en el CSV).")
                        self.enviar_temp = False
                        r, seg = self._llamar(prompt, max_tokens, False)
                    else:
                        raise
                break
            except Exception as e:
                if intento == 3 or not any(s in str(e) for s in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                    raise
                time.sleep(5 * 2 ** intento)
        u = r.usage_metadata
        cand = getattr(u, "candidates_token_count", None) or 0
        razon = getattr(u, "thoughts_token_count", None) or 0
        return {"texto": r.text or "", "seg": seg, "tin": getattr(u, "prompt_token_count", None),
                "tout": cand + razon, "razon": razon, "carga": None,
                "temp": TEMPERATURA if self.enviar_temp else "ignorada"}


def construir_motores(args):
    """Verifica requisitos y devuelve [(etiqueta, modelo_id, funcion)]."""
    import ollama
    try:
        ollama.show(args.modelo_local)
    except Exception as e:
        sys.exit(f"No se pudo usar el modelo local '{args.modelo_local}' en Ollama: {e}\n"
                 f"¿Está Ollama en ejecución y ejecutó 'ollama pull {args.modelo_local}'?")
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        sys.exit("Falta la variable de entorno GEMINI_API_KEY (clave de Google AI Studio).")
    nube = Nube(args.modelo_nube, args.pensamiento)
    return [("local", args.modelo_local, lambda p: consultar_local(p, args.modelo_local, args.max_tokens)),
            ("nube", args.modelo_nube, lambda p: nube.consultar(p, args.max_tokens))]


# ---------------------------------------------------------------- utilidades
def json_valido(texto):
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        json.loads(t)
        return True
    except ValueError:
        return False


def resumen(filas):
    ok = [f for f in filas if f["segundos"] != ""]
    print("\n" + "=" * 72 + "\nRESUMEN\n" + "=" * 72)
    print(f"{'motor':<8}{'llamadas':>9}{'errores':>9}{'media (s)':>11}{'mediana (s)':>13}{'tok/s':>9}{'JSON ok':>10}")
    for motor in ("local", "nube"):
        todas = [f for f in filas if f["modelo"] == motor]
        buenas = [f for f in ok if f["modelo"] == motor]
        if not todas:
            continue
        segs = [f["segundos"] for f in buenas]
        tps = [f["tokens_por_seg"] for f in buenas if f["tokens_por_seg"] != ""]
        js = [f["json_valido"] for f in buenas if f["json_valido"] != ""]
        print(f"{motor:<8}{len(todas):>9}{len(todas) - len(buenas):>9}"
              f"{(statistics.mean(segs) if segs else float('nan')):>11.2f}"
              f"{(statistics.median(segs) if segs else float('nan')):>13.2f}"
              f"{(statistics.mean(tps) if tps else float('nan')):>9.1f}"
              f"{(f'{sum(js)}/{len(js)}' if js else '—'):>10}")
    print(f"\n{'tarea':<18}{'local (s)':>11}{'nube (s)':>10}{'local/nube':>12}")
    for tarea, _ in TAREAS:
        v = {m: [f["segundos"] for f in ok if f["tarea"] == tarea and f["modelo"] == m] for m in ("local", "nube")}
        if v["local"] and v["nube"]:
            a, b = statistics.mean(v["local"]), statistics.mean(v["nube"])
            print(f"{tarea:<18}{a:>11.2f}{b:>10.2f}{(a / b if b else float('nan')):>11.1f}x")
    sin_temp = [f for f in filas if f["modelo"] == "nube" and f["temperatura_enviada"] == "ignorada"]
    if sin_temp:
        print("\n(!) Gemini no aplicó temperature=0.2: la comparación de temperatura NO es idéntica.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True, help="ruta del PDF (la novela)")
    ap.add_argument("--fragmentos", type=int, default=3, help="fragmentos distintos del libro (por defecto 3)")
    ap.add_argument("--chars", type=int, default=4000, help="tamaño de cada fragmento en caracteres")
    ap.add_argument("--repeticiones", type=int, default=1, help="veces que se repite cada caso por motor")
    ap.add_argument("--max-tokens", type=int, default=600, help="tope de tokens de respuesta")
    ap.add_argument("--modelo-local", default="llama3")
    ap.add_argument("--modelo-nube", default=os.environ.get("GEMINI_MODELO", "gemini-3.5-flash-lite"))
    ap.add_argument("--pensamiento", default=os.environ.get("GEMINI_THINKING_LEVEL"),
                    help="thinking_level de Gemini (ej.: minimal, low). Por defecto, el del modelo")
    ap.add_argument("--salida", default="resultados.csv")
    ap.add_argument("--sin-calentamiento", action="store_true")
    a = ap.parse_args(argv)

    ruta = pathlib.Path(a.pdf)
    if not ruta.exists():
        sys.exit(f"No existe el archivo: {ruta}")
    texto, npag = extraer_texto(ruta)
    if len(texto) < a.chars * a.fragmentos:
        sys.exit(f"Texto extraído insuficiente ({len(texto)} caracteres en {npag} páginas). "
                 "Si el PDF es una imagen escaneada, necesita OCR.")
    casos = construir_casos(seleccionar_fragmentos(texto, a.fragmentos, a.chars))
    motores = construir_motores(a)

    print(f"PDF: {ruta.name} · {npag} páginas · {len(texto):,} caracteres")
    print(f"Casos: {len(casos)} ({a.fragmentos} fragmentos × {len(TAREAS)} tareas) × {len(motores)} motores × {a.repeticiones} repetición(es)")
    print(f"Local: {a.modelo_local} (Ollama) | Nube: {a.modelo_nube} (Gemini) | temperatura {TEMPERATURA} | tope {a.max_tokens} tokens")

    if not a.sin_calentamiento:
        print("Calentando motores (carga del modelo local; no se registra)...")
        for _, _, fn in motores:
            try:
                fn("Responde solo: ok")
            except Exception as e:
                print("  aviso en el calentamiento:", e)

    filas = []
    total = len(casos) * a.repeticiones * len(motores)
    hecho = 0
    with open(a.salida, "w", newline="", encoding="utf-8-sig") as f:       # utf-8-sig: Excel muestra bien las tildes
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for c in casos:
            for rep in range(1, a.repeticiones + 1):
                for etiqueta, modelo_id, fn in motores:
                    hecho += 1
                    fila = {k: "" for k in COLUMNAS}
                    fila.update(id=c["id"], tarea=c["tarea"], modelo=etiqueta, fragmento=c["fragmento"],
                                repeticion=rep, modelo_id=modelo_id)
                    try:
                        r = fn(c["prompt"])
                        seg = r["seg"]
                        fila.update(segundos=round(seg, 2), tokens_entrada=r["tin"] or "", tokens_salida=r["tout"] or "",
                                    tokens_razonamiento=r["razon"] if r["razon"] is not None else "",
                                    tokens_por_seg=round(r["tout"] / seg, 1) if r["tout"] and seg else "",
                                    carga_s=r["carga"] if r["carga"] is not None else "",
                                    temperatura_enviada=r["temp"], respuesta=r["texto"])
                        if c["tarea"] == "extraccion_json":
                            fila["json_valido"] = json_valido(r["texto"])
                        print(f"[{hecho}/{total}] {etiqueta:<5} {c['tarea']:<16} f{c['fragmento']} {seg:6.2f} s")
                    except Exception as e:
                        fila["respuesta"] = f"ERROR: {e}"
                        print(f"[{hecho}/{total}] {etiqueta:<5} {c['tarea']:<16} f{c['fragmento']} ERROR: {str(e)[:80]}")
                    w.writerow(fila)
                    f.flush()                                              # conserva resultados parciales
                    filas.append(fila)
    resumen(filas)
    print(f"\nResultados completos en: {a.salida}")


if __name__ == "__main__":
    main()
