"""Valida dataset_completo.jsonl y lo divide en train/val/test (80/10/10).
Si hay errores no escribe nada. Estratifica por 'dificil' para que los casos
difíciles aparezcan en los tres conjuntos."""
import json, re, random, sys, collections

ENTRADA, SEED = "dataset_completo.jsonl", 42
MAX_PALABRAS, MIN_EJEMPLOS, MIN_DIFICILES = 80, 100, 10

RX_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RX_TEL = re.compile(r"(?<![\w-])\+?\d[\d\s\-().]{7,}\d(?!\w)")
RX_DOC = re.compile(r"(?i)\b(dni|cédula|cedula|pasaporte|legajo)\s*(?:es\s+)?[:#]?\s*[A-Z]?-?\d{3,}")
RX_NOMBRE = re.compile(r"\b(?i:soy|me llamo|mi nombre es|le escribe|mi jefe|mi jefa|mi compañera|mi compañero|teléfono de|correo de)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+")
RX_CIERRE = re.compile(r"(?i)(ayud|duda|consulta)[^.?!]*[.?!]?\s*$")
RX_PRH_OK = re.compile(r"PRH-\d{2}\b")


def pii_residual(texto):
    return [n for n, rx in (("correo", RX_CORREO), ("teléfono", RX_TEL),
                            ("documento/ID", RX_DOC), ("nombre", RX_NOMBRE)) if rx.search(texto)]


def validar(ej, i, system_ref):
    errs = []
    m = ej.get("messages")
    if not isinstance(m, list) or [x.get("role") for x in m] != ["system", "user", "assistant"]:
        return [f"#{i}: la estructura debe ser system → user → assistant"]
    if any(not isinstance(x.get("content"), str) or not x["content"].strip() for x in m):
        errs.append(f"#{i}: contenido vacío o no textual")
        return errs
    if m[0]["content"] != system_ref:
        errs.append(f"#{i}: mensaje de sistema distinto al de referencia")
    user, asis = m[1]["content"], m[2]["content"]
    meta = ej.get("meta", {})
    if not asis.startswith("Hola"):
        errs.append(f"#{i}: R1 la respuesta debe iniciar con saludo 'Hola'")
    if ("Hola [NOMBRE]," in asis) != bool(meta.get("se_identifica")):
        errs.append(f"#{i}: R1 uso incorrecto de [NOMBRE] en el saludo")
    palabras = len(re.findall(r"\S+", asis))
    if palabras > MAX_PALABRAS:
        errs.append(f"#{i}: R2 {palabras} palabras (máx. {MAX_PALABRAS})")
    if "PRH-" in asis and len(RX_PRH_OK.findall(asis)) != asis.count("PRH-"):
        errs.append(f"#{i}: R3 código de política con formato inválido")
    for rol, txt in (("usuario", user), ("asistente", asis)):
        p = pii_residual(txt)
        if p:
            errs.append(f"#{i}: R4 posible dato personal sin anonimizar en {rol}: {p}")
    if not RX_CIERRE.search(asis):
        errs.append(f"#{i}: R5 falta cierre con oferta de ayuda")
    return errs


def main():
    filas = [json.loads(l) for l in open(ENTRADA, encoding="utf-8") if l.strip()]
    system_ref = filas[0]["messages"][0]["content"]
    errores = [e for i, f in enumerate(filas, 1) for e in validar(f, i, system_ref)]
    vistos = collections.Counter(f["messages"][1]["content"].strip().lower() for f in filas)
    errores += [f"duplicado: {q[:50]!r}" for q, n in vistos.items() if n > 1]
    dificiles = sum(bool(f["meta"]["dificil"]) for f in filas)
    if len(filas) < MIN_EJEMPLOS:
        errores.append(f"se requieren ≥{MIN_EJEMPLOS} ejemplos y hay {len(filas)}")
    if dificiles < MIN_DIFICILES:
        errores.append(f"se requieren ≥{MIN_DIFICILES} casos difíciles y hay {dificiles}")
    if errores:
        print("VALIDACIÓN FALLIDA:"); [print(" -", e) for e in errores]; sys.exit(1)

    rnd = random.Random(SEED)
    split = {"train": [], "val": [], "test": []}
    for flag in (False, True):
        grupo = [f for f in filas if bool(f["meta"]["dificil"]) == flag]
        rnd.shuffle(grupo)
        n_val = n_test = round(len(grupo) * 0.10)
        split["val"] += grupo[:n_val]
        split["test"] += grupo[n_val:n_val + n_test]
        split["train"] += grupo[n_val + n_test:]
    for nombre, lote in split.items():
        rnd.shuffle(lote)
        with open(f"{nombre}.jsonl", "w", encoding="utf-8") as f:
            for r in lote:
                f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")

    pal = [len(re.findall(r"\S+", f["messages"][2]["content"])) for f in filas]
    print(f"VALIDACIÓN OK · {len(filas)} ejemplos ({dificiles} difíciles) · sin duplicados · sin PII residual")
    print(f"Palabras por respuesta: mín {min(pal)} · media {sum(pal)/len(pal):.1f} · máx {max(pal)}")
    for nombre, lote in split.items():
        d = sum(bool(r['meta']['dificil']) for r in lote)
        print(f"  {nombre}.jsonl: {len(lote)} ejemplos ({100*len(lote)/len(filas):.0f} %), difíciles: {d}")


if __name__ == "__main__":
    main()
