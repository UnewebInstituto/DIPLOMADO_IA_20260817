"""Evalúa la generación con LLM como juez (P4). Usa el proveedor configurado (Ollama o Gemini).

    python evaluacion/eval_generacion.py
Variable opcional JUEZ_PROVEEDOR=gemini|ollama para usar un juez distinto del generador.
"""
import json, os, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from generacion import LLM
from motor import RAG

CRITERIOS = ("fidelidad", "relevancia", "correccion")
RUBRICA = """Eres un evaluador estricto de sistemas RAG. Recibirás una PREGUNTA, el CONTEXTO
recuperado, la RESPUESTA del sistema y una RESPUESTA_REFERENCIA.
Califica de 1 a 5 cada criterio (números enteros):
- fidelidad: 5 = todas las afirmaciones están respaldadas por el CONTEXTO; 1 = inventa datos.
- relevancia: 5 = responde exactamente lo preguntado; 1 = no responde.
- correccion: 5 = coincide con la RESPUESTA_REFERENCIA; 1 = contradice.
Si la RESPUESTA_REFERENCIA es NO_RESPONDIBLE, la respuesta correcta es abstenerse:
pon correccion = 5 solo si el sistema dice que no encontró la información.
Responde ÚNICAMENTE con JSON: {"fidelidad": n, "relevancia": n, "correccion": n, "comentario": "..."}"""


def juzgar(juez, caso, salida):
    contexto = "\n---\n".join(f["texto"] for f in salida["fragmentos"])
    msg = (f"PREGUNTA: {caso['pregunta']}\n\nCONTEXTO:\n{contexto}\n\n"
           f"RESPUESTA: {salida['respuesta']}\n\nRESPUESTA_REFERENCIA: {caso['respuesta_referencia']}")
    texto = juez.generar(RUBRICA, msg, json_mode=True, max_tokens=500, temperatura=0)
    nota = json.loads(texto.replace("```json", "").replace("```", "").strip())
    for m in CRITERIOS:
        if not (isinstance(nota.get(m), int) and 1 <= nota[m] <= 5):
            raise ValueError(f"Nota inválida en '{m}': {nota.get(m)!r}")
    return nota


def diagnosticar(caso, ids_ctx, nota):
    if not caso["relevantes"]:
        return "abstencion_correcta" if nota["correccion"] >= 4 else "no_se_abstuvo"
    if nota["correccion"] >= 4:
        return "ok"
    return "fallo_generacion" if set(caso["relevantes"]) & set(ids_ctx) else "fallo_recuperacion"


def main():
    rag = RAG()
    if rag.almacen.contar() == 0:
        sys.exit("Índice vacío. Ejecute: python cli.py sincronizar")
    juez = LLM(os.environ.get("JUEZ_PROVEEDOR"))
    with open(RAIZ / "evaluacion" / "dataset.json", encoding="utf-8") as f:
        casos = json.load(f)

    resultados = []
    for c in casos:
        try:
            salida = rag.responder(c["pregunta"])
            ids_ctx = [f["id"] for f in salida["fragmentos"]]
            nota = juzgar(juez, c, salida)
            resultados.append({**c, "respuesta": salida["respuesta"], "ids_contexto": ids_ctx, **nota,
                               "diagnostico": diagnosticar(c, ids_ctx, nota)})
            print(c["pregunta"][:60], "->", nota)
        except Exception as e:
            resultados.append({**c, "error": str(e)})
            print(c["pregunta"][:60], "-> ERROR:", e)

    with open(RAIZ / "evaluacion" / "resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    ok = [x for x in resultados if "error" not in x]
    resp = [x for x in ok if x["relevantes"]]
    noresp = [x for x in ok if not x["relevantes"]]
    print(f"\nEvaluadas: {len(ok)}/{len(resultados)}")
    if resp:
        print(f"\nPreguntas respondibles (n={len(resp)}):")
        for m in CRITERIOS:
            print(f"  {m}: {sum(x[m] for x in resp) / len(resp):.2f}")
    if noresp:
        bien = sum(1 for x in noresp if x["diagnostico"] == "abstencion_correcta")
        print(f"\nAbstención correcta en no respondibles: {bien}/{len(noresp)}")
    print("\nDiagnóstico:")
    for d in sorted({x["diagnostico"] for x in ok}):
        print(f"  {d}: {sum(1 for x in ok if x['diagnostico'] == d)}")


if __name__ == "__main__":
    main()
