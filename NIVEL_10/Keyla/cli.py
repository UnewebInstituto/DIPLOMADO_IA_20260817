"""Línea de comandos: python cli.py {sincronizar|reindexar|estado|preguntar|chat}"""
import argparse, json, sys
from motor import RAG
from registro import registrar


def _imprimir(salida):
    print("\nRESPUESTA:\n", salida["respuesta"])
    if salida.get("aviso"):
        print("\n(!)", salida["aviso"])
    print("\nFUENTES:")
    for n, f in enumerate(salida["fragmentos"], 1):
        d = f"{f['distancia']:.3f}" if f["distancia"] is not None else "—"
        print(f" [{n}] {f['fuente']} p.{f['pagina']} (distancia {d})")
    print(f"\n[{salida['modo']}{' + rerank' if salida['rerank'] else ''} | {salida['tiempos']}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sincronizar", help="agrega/actualiza/elimina según la carpeta de documentos")
    sub.add_parser("reindexar", help="reconstruye todo el índice desde cero")
    sub.add_parser("estado", help="muestra chunks y fuentes indexadas")
    
    for nombre in ("preguntar", "chat"):
        p = sub.add_parser(nombre)
        if nombre == "preguntar":
            # Usamos nargs="?" y default="" para que la consulta sea opcional en la terminal
            p.add_argument("consulta", nargs="?", default="", help="Texto de la pregunta a realizar")
        p.add_argument("--k", type=int)
        p.add_argument("--modo", choices=["hibrida", "vectorial"])
        g = p.add_mutually_exclusive_group()
        g.add_argument("--rerank", dest="rerank", action="store_true", default=None)
        g.add_argument("--no-rerank", dest="rerank", action="store_false")
        
    a = ap.parse_args()

    rag = RAG()
    if a.cmd == "sincronizar":
        print(json.dumps(rag.sincronizar(), ensure_ascii=False, indent=2))
    elif a.cmd == "reindexar":
        print(json.dumps(rag.reindexar(), ensure_ascii=False, indent=2))
    elif a.cmd == "estado":
        print(json.dumps(rag.estado(), ensure_ascii=False, indent=2))
    elif a.cmd == "preguntar":
        # Si no se pasó la consulta por la terminal, la solicitamos mediante input()
        consulta_texto = a.consulta
        if not consulta_texto:
            consulta_texto = input("\nEscribe tu pregunta: ").strip()
            
        if consulta_texto:
            s = rag.responder(consulta_texto, k=a.k, modo=a.modo, rerank=a.rerank)
            registrar(consulta_texto, s)
            _imprimir(s)
        else:
            print("No se ingresó ninguna pregunta.")
    elif a.cmd == "chat":
        if rag.almacen.contar() == 0:
            print("Índice vacío; sincronizando...", rag.sincronizar())
        historial = []
        while True:
            p = input("\nPreguntar (vacío para salir): ").strip()
            if not p:
                break
            s = rag.responder(p, k=a.k, modo=a.modo, rerank=a.rerank, historial=historial, reescribir=True)
            registrar(p, s)
            _imprimir(s)
            historial += [("user", p), ("assistant", s["respuesta"])]


if __name__ == "__main__":
    sys.exit(main())
