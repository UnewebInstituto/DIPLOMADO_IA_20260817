import json, os, sys, time, pathlib

# Raíz del proyecto (rag_nivel9/): permite ejecutar desde cualquier carpeta
RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.chdir(RAIZ)

from google import genai
from google.genai import types
from rag import RAG

MODELO_JUEZ = "gemini-3.5-flash-lite"   # verificar el ID vigente
K = 4                                    # mismo k que usa rag.responder
CRITERIOS = ("fidelidad", "relevancia", "correccion")

rag = RAG()
juez = genai.Client()

RUBRICA = """Eres un evaluador estricto de sistemas RAG. Recibirás una PREGUNTA, el CONTEXTO
recuperado, la RESPUESTA del sistema y una RESPUESTA_REFERENCIA.
Califica de 1 a 5 cada criterio (números enteros):
- fidelidad: 5 = todas las afirmaciones están respaldadas por el CONTEXTO; 1 = inventa datos.
- relevancia: 5 = responde exactamente lo preguntado; 1 = no responde.
- correccion: 5 = coincide con la RESPUESTA_REFERENCIA; 1 = contradice.
Si la RESPUESTA_REFERENCIA es NO_RESPONDIBLE, la respuesta correcta es abstenerse:
pon correccion = 5 solo si el sistema dice que no encontró la información.
Responde ÚNICAMENTE con JSON: {"fidelidad": n, "relevancia": n, "correccion": n, "comentario": "..."}"""


def con_reintentos(fn, intentos=4, espera=5):
    for i in range(intentos):
        try:
            return fn()
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(espera * 2 ** i)


def juzgar(caso, salida):
    contexto = "\n---\n".join(f["texto"] for f in salida["fragmentos"])
    msg = (f"PREGUNTA: {caso['pregunta']}\n\nCONTEXTO:\n{contexto}\n\n"
           f"RESPUESTA: {salida['respuesta']}\n\n"
           f"RESPUESTA_REFERENCIA: {caso['respuesta_referencia']}")

    def llamar():
        r = juez.models.generate_content(
            model=MODELO_JUEZ,
            contents=msg,
            config=types.GenerateContentConfig(
                system_instruction=RUBRICA,
                response_mime_type="application/json",
                max_output_tokens=1500,
            ),
        )
        nota = json.loads(r.text)
        for m in CRITERIOS:
            if not (isinstance(nota.get(m), int) and 1 <= nota[m] <= 5):
                raise ValueError(f"Nota inválida en '{m}': {nota.get(m)!r}")
        return nota

    return con_reintentos(llamar)


def diagnosticar(caso, ids_contexto, nota):
    if not caso["relevantes"]:
        return "abstencion_correcta" if nota["correccion"] >= 4 else "no_se_abstuvo"
    if nota["correccion"] >= 4:
        return "ok"
    return ("fallo_generacion" if set(caso["relevantes"]) & set(ids_contexto)
            else "fallo_recuperacion")


with open("evaluacion/dataset.json", encoding="utf-8") as f:
    casos = json.load(f)

resultados = []
for c in casos:
    try:
        # IDs de lo que verá el LLM (misma consulta y k que responder())
        q = rag.emb.encode([c["pregunta"]], normalize_embeddings=True).tolist()
        ids_ctx = rag.col.query(query_embeddings=q, n_results=K)["ids"][0]

        salida = con_reintentos(lambda: rag.responder(c["pregunta"], k=K))
        nota = juzgar(c, salida)
        resultados.append({**c, "respuesta": salida["respuesta"],
                           "ids_contexto": ids_ctx, **nota,
                           "diagnostico": diagnosticar(c, ids_ctx, nota)})
        print(c["pregunta"][:60], "->", nota)
    except Exception as e:
        resultados.append({**c, "error": str(e)})
        print(c["pregunta"][:60], "-> ERROR:", e)

with open("evaluacion/resultados.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

# --- Resumen ---
ok = [x for x in resultados if "error" not in x]
resp = [x for x in ok if x["relevantes"]]
noresp = [x for x in ok if not x["relevantes"]]

print(f"\nEvaluadas: {len(ok)}/{len(resultados)}")
print(f"\nPreguntas respondibles (n={len(resp)}):")
for m in CRITERIOS:
    print(f"  {m}: {sum(x[m] for x in resp) / len(resp):.2f}")
if noresp:
    bien = sum(1 for x in noresp if x["diagnostico"] == "abstencion_correcta")
    print(f"\nAbstención correcta en no respondibles: {bien}/{len(noresp)}")

print("\nDiagnóstico:")
for d in sorted({x["diagnostico"] for x in ok}):
    print(f"  {d}: {sum(1 for x in ok if x['diagnostico'] == d)}")
    