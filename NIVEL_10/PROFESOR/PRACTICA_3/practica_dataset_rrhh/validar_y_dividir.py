"""Paso 7 — Validación y división 80/10/10 del dataset de fine-tuning (formato chat, JSONL).

Validaciones (cualquier error detiene el proceso y NO escribe los archivos):
  estructura   system -> user -> assistant, contenidos no vacíos, un mismo system prompt en todos
  guía de estilo  cierre "Fuente: ... sección N." (N existente) o "Derivación: ...", ≤ 100 palabras,
                  texto plano (sin markdown ni emojis)
  privacidad   solo marcadores válidos; sin correos, teléfonos, IDs, documentos ni nombres residuales
  calidad      sin preguntas duplicadas
División: estratificada por tipo de caso (normal / fuera_alcance / ambigua / mal_escrita), semilla fija;
val y test reciben al menos un caso de cada tipo difícil.

    python validar_y_dividir.py            # anonimizado.jsonl -> train/val/test.jsonl + split_manifest.csv
"""
import collections, csv, json, pathlib, random, re, sys

from anonimizar import APELLIDOS_DICC, MARCADORES, NOMBRES_DICC, RE_FECHA
from datos_simulados import NOMBRES

BASE = pathlib.Path(__file__).parent
SEMILLA = 42
MAX_PALABRAS = 100
SECCIONES = {"1", "2", "3", "4", "5", "6", "6.1", "6.2", "7", "7.1", "8", "8.1", "8.2", "9", "9.1", "10", "10.1",
             "10.2", "11", "11.1", "12", "12.1", "12.2", "13", "13.1", "14", "14.1", "14.2", "15", "15.1", "16",
             "16.1", "16.2", "17", "17.1", "18", "18.1"}
CORREOS_INSTITUCIONALES = {"codigo.etica@empresa.com"}
NOMBRES_PROHIBIDOS = sorted({p for par in NOMBRES for p in par} | set(NOMBRES_DICC) | set(APELLIDOS_DICC))

RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_TEL = re.compile(r"[+(]?\d[\d\s().-]{5,}\d")
RE_ID = re.compile(r"\bEMP-?\d{3,}\b")
RE_DOC = re.compile(r"\b[VEJGvejg]-?\d{1,2}\.?\d{3}\.?\d{3}\b")
RE_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")
RE_MARKDOWN = re.compile(r"\*\*|__|`|^#{1,6}\s|^\s*[-*•]\s", re.M)
RE_CORCHETE = re.compile(r"\[[^\]]+\]")
RE_FUENTE = re.compile(r"Fuente: Reglamento de RRHH, secci(?:ón|ones) (\d+(?:\.\d+)?(?:(?:, | y )\d+(?:\.\d+)?)*)\.")


def buscar_pii(texto):
    hallazgos = []
    hallazgos += [f"correo {c}" for c in RE_CORREO.findall(texto) if c not in CORREOS_INSTITUCIONALES]
    for m in RE_TEL.findall(texto):
        if sum(ch.isdigit() for ch in m) >= 7 and not RE_FECHA.fullmatch(m.strip()):
            hallazgos.append(f"teléfono {m.strip()}")
    hallazgos += [f"id {x}" for x in RE_ID.findall(texto)] + [f"documento {x}" for x in RE_DOC.findall(texto)]
    hallazgos += [f"nombre {n}" for n in NOMBRES_PROHIBIDOS if re.search(rf"\b{n}\b", texto)]
    return hallazgos


def validar(ejemplos):
    errores, systems, vistos = [], set(), {}
    for e in ejemplos:
        i, m = e["id"], e.get("messages")
        if not isinstance(m, list) or [x.get("role") for x in m] != ["system", "user", "assistant"]:
            errores.append(f"{i}: estructura distinta de system/user/assistant")
            continue
        sis, usr, asi = (x.get("content") for x in m)
        if not all(isinstance(t, str) and t.strip() for t in (sis, usr, asi)):
            errores.append(f"{i}: contenido vacío o no textual")
            continue
        systems.add(sis)
        if len(usr.strip()) < 5:
            errores.append(f"{i}: pregunta demasiado corta")
        # --- guía de estilo ---
        ultima = asi.strip().split("\n")[-1]
        if ultima.startswith("Fuente:"):
            m_fuente = RE_FUENTE.fullmatch(ultima)
            citadas = re.findall(r"\d+(?:\.\d+)?", m_fuente.group(1)) if m_fuente else []
            if not citadas or any(c not in SECCIONES for c in citadas):
                errores.append(f"{i}: cierre 'Fuente' mal formado o con sección inexistente: {ultima!r}")
        elif not ultima.startswith("Derivación:"):
            errores.append(f"{i}: la respuesta no cierra con 'Fuente:' ni 'Derivación:'")
        palabras = len(asi.split())
        if palabras > MAX_PALABRAS:
            errores.append(f"{i}: respuesta de {palabras} palabras (máx. {MAX_PALABRAS})")
        if RE_EMOJI.search(asi) or RE_MARKDOWN.search(asi):
            errores.append(f"{i}: la respuesta debe ser texto plano (sin markdown ni emojis)")
        # --- privacidad ---
        for rol, texto in (("system", sis), ("user", usr), ("assistant", asi)):
            for h in buscar_pii(texto):
                errores.append(f"{i}: dato personal residual en {rol}: {h}")
            for c in RE_CORCHETE.findall(texto):
                if c not in MARCADORES:
                    errores.append(f"{i}: marcador desconocido {c} en {rol}")
        if RE_CORCHETE.search(asi):
            errores.append(f"{i}: la respuesta no debe contener marcadores de anonimización")
        # --- duplicados ---
        clave = re.sub(r"\W+", " ", usr.lower()).strip()
        if clave in vistos:
            errores.append(f"{i}: pregunta duplicada de {vistos[clave]}")
        vistos[clave] = i
    if len(systems) > 1:
        errores.append(f"hay {len(systems)} system prompts distintos; debe ser uno solo")
    return errores


def dividir(ejemplos):
    rng = random.Random(SEMILLA)
    total = len(ejemplos)
    n_val = n_test = round(0.10 * total)
    estratos = collections.defaultdict(list)
    for e in ejemplos:
        estratos[e["tipo"]].append(e)
    cuota = {}
    for tipo, lista in estratos.items():
        if tipo != "normal":
            cuota[tipo] = max(1, round(0.10 * len(lista)))          # cobertura mínima de casos difíciles
    resto = n_val - sum(cuota.values())
    if "normal" in estratos:
        cuota["normal"] = max(1, resto)
    split = {"train": [], "val": [], "test": []}
    for tipo, lista in estratos.items():
        lista = lista[:]
        rng.shuffle(lista)
        q = cuota[tipo]
        split["test"] += lista[:q]
        split["val"] += lista[q:2 * q]
        split["train"] += lista[2 * q:]
    for s in split.values():
        rng.shuffle(s)
    return split


def main():
    ejemplos = [json.loads(l) for l in open(BASE / "anonimizado.jsonl", encoding="utf-8")]
    errores = validar(ejemplos)
    informe = [f"Ejemplos leídos: {len(ejemplos)}"]
    if errores:
        print(f"VALIDACIÓN FALLIDA: {len(errores)} error(es)")
        for e in errores[:50]:
            print(" -", e)
        sys.exit(1)
    informe.append("Validación: OK (estructura, guía de estilo, privacidad, duplicados)")

    split = dividir(ejemplos)
    with open(BASE / "split_manifest.csv", "w", newline="", encoding="utf-8") as fm:
        w = csv.writer(fm)
        w.writerow(["id", "split", "tipo", "categoria"])
        for nombre, lista in split.items():
            with open(BASE / f"{nombre}.jsonl", "w", encoding="utf-8") as f:
                for e in lista:
                    f.write(json.dumps({"messages": e["messages"]}, ensure_ascii=False) + "\n")
                    w.writerow([e["id"], nombre, e["tipo"], e["categoria"]])

    total = len(ejemplos)
    informe.append(f"\n{'split':<7}{'n':>5}{'%':>7}   " + "  ".join(f"{t}" for t in ("normal", "fuera_alcance", "ambigua", "mal_escrita")))
    for nombre, lista in split.items():
        c = collections.Counter(e["tipo"] for e in lista)
        informe.append(f"{nombre:<7}{len(lista):>5}{100 * len(lista) / total:>6.1f}%   " +
                       "  ".join(f"{c.get(t, 0):>{len(t)}}" for t in ("normal", "fuera_alcance", "ambigua", "mal_escrita")))
    todos_usr = [e["messages"][1]["content"] for e in ejemplos]
    marc = collections.Counter(m for t in todos_usr for m in RE_CORCHETE.findall(t))
    palabras = [len(e["messages"][2]["content"].split()) for e in ejemplos]
    informe.append(f"\nMarcadores en preguntas: {dict(marc)}")
    informe.append(f"Palabras por respuesta: media {sum(palabras) / len(palabras):.1f}, máx. {max(palabras)}")
    informe.append(f"Categorías distintas: {len({e['categoria'] for e in ejemplos})} | semilla: {SEMILLA}")
    texto = "\n".join(informe)
    print(texto)
    (BASE / "reporte_validacion.txt").write_text(texto + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
