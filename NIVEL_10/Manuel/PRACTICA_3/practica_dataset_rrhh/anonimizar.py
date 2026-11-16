"""Paso 3 — Anonimización por reglas (determinista y auditable).

Orden de aplicación (de lo más específico a lo más general):
  1. [CORREO]       direcciones de correo electrónico.
  2. [DOCUMENTO]    cédula / documento de identidad (V-12.345.678, "cédula 12345678").
  3. [ID_EMPLEADO]  códigos de empleado (EMP-48213, "ID de empleado 4821").
  4. [TELÉFONO]     extensiones ("ext. 4521") y números con 7 o más dígitos (cualquier formato).
  5. [NOMBRE]       (a) nombres que siguen a una frase gatillo ("soy", "me llamo", "habla", "Atentamente,",
                    "mi jefe", "Ing.", ...); (b) cualquier nombre o apellido del diccionario.
                    Nombres consecutivos se funden en un solo marcador.
Solo se anonimiza el turno del USUARIO; las respuestas ideales se redactan sin datos personales y el
validador lo comprueba. Los canales institucionales (Línea Ética) no son datos personales.

    python anonimizar.py            # crudo.jsonl -> anonimizado.jsonl
"""
import collections, json, pathlib, re

MARCADORES = ["[NOMBRE]", "[CORREO]", "[TELÉFONO]", "[ID_EMPLEADO]", "[DOCUMENTO]"]

NOMBRES_DICC = """Ana Andrés Camila Carlos Daniela Karen Luis Marcela María Patricia Pedro Roberto Sofía José Juan
Miguel Laura Carmen Rafael Elena Javier Fernando Gabriela Alejandra Ricardo Verónica Héctor Mónica Diego Valentina""".split()
APELLIDOS_DICC = """Rojas Fernández Beltrán Gómez Díaz Navarro Reyes Molina García Rodríguez Martínez López Pérez
Sánchez Ramírez Torres Flores Herrera Castillo Mendoza Vargas Morales Ortega Silva Romero Castro""".split()

_CAP = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
_GATILLOS = (r"soy|me llamo|mi nombre es|habla|le escribe|me escribe|atentamente,?|saludos,?|gracias,?|att\.?,?|"
             r"mi (?:jefe|jefa|supervisor|supervisora|gerente|compañero|compañera|colega)|"
             r"(?:ing|lic|dr|dra|sr|sra|srta|arq)\.?")
RE_GATILLO = re.compile(rf"(?i:\b(?:{_GATILLOS}))\s+({_CAP}(?:\s+(?:de\s+|del\s+|la\s+)?{_CAP}){{0,2}})")
NO_NOMBRES = {"Analista", "Gerente", "Supervisor", "Supervisora", "Jefe", "Jefa", "Recursos", "Nuevo", "Nueva",
              "Operativo", "Operativa", "Personal", "Empleado", "Empleada", "Colaborador", "Colaboradora",
              "Director", "Directora", "Ingeniero", "Contador", "Contadora", "Especialista"}
_PALABRAS = sorted(NOMBRES_DICC + APELLIDOS_DICC, key=len, reverse=True)
RE_DICC = re.compile(rf"\b(?:{'|'.join(_PALABRAS)})(?:\s+(?:{'|'.join(_PALABRAS)})){{0,3}}\b")

RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_DOC = re.compile(r"\b[VEJGvejg]-?\d{1,2}\.?\d{3}\.?\d{3}\b|(?i:c[eé]dula|dni|documento de identidad)\s*(?:n[°º.o]*\s*)?[:#]?\s*\d[\d.\-]{5,}")
RE_ID = re.compile(r"\bEMP-?\d{3,}\b|(?i:id de empleado|n[úu]mero de empleado|c[oó]digo de empleado)\s*:?\s*\d+")
RE_EXT = re.compile(r"(?i:\bext(?:ensi[oó]n)?\.?)\s*\d{2,6}\b")
RE_DIGITOS = re.compile(r"[+(]?\d[\d\s().-]{5,}\d")


RE_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}")


def _tel(m):
    g = m.group()
    if RE_FECHA.fullmatch(g.strip()):                       # las fechas no son teléfonos
        return g
    return "[TELÉFONO]" if sum(c.isdigit() for c in g) >= 7 else g


def _nombre_gatillo(m):
    nombre = m.group(1)
    if nombre.split()[0] in NO_NOMBRES:
        return m.group(0)
    return m.group(0)[: m.start(1) - m.start(0)] + "[NOMBRE]"


def anonimizar(texto):
    """Devuelve (texto_anonimizado, Counter de marcadores aplicados)."""
    cuenta = collections.Counter()

    def sub(patron, reemplazo, t, marcador):
        t, n = patron.subn(reemplazo, t)
        cuenta[marcador] += n
        return t

    t = sub(RE_CORREO, "[CORREO]", texto, "[CORREO]")
    t = sub(RE_DOC, "[DOCUMENTO]", t, "[DOCUMENTO]")
    t = sub(RE_ID, "[ID_EMPLEADO]", t, "[ID_EMPLEADO]")
    t = sub(RE_EXT, "[TELÉFONO]", t, "[TELÉFONO]")
    t = sub(RE_DIGITOS, _tel, t, "[TELÉFONO]")
    t = RE_GATILLO.sub(_nombre_gatillo, t)
    t = RE_DICC.sub("[NOMBRE]", t)
    t = re.sub(r"\[NOMBRE\](?:\s+\[NOMBRE\])+", "[NOMBRE]", t)         # un solo marcador por nombre completo
    cuenta = collections.Counter({m: t.count(m) for m in MARCADORES if t.count(m)})
    return t, cuenta


def main():
    base = pathlib.Path(__file__).parent
    from datos_simulados import SISTEMA
    entrada = [json.loads(l) for l in open(base / "crudo.jsonl", encoding="utf-8")]
    total = collections.Counter()
    fugas, inyectados_total = [], 0
    with open(base / "anonimizado.jsonl", "w", encoding="utf-8") as f:
        for e in entrada:
            q, c = anonimizar(e["pregunta_cruda"])
            total.update(c)
            for tipo, valor in e["pii_inyectada"]:                      # medición de recall con datos conocidos
                inyectados_total += 1
                partes = valor.split() if tipo == "NOMBRE" else [valor]
                if any(p in q for p in partes):
                    fugas.append((e["id"], tipo, valor))
            f.write(json.dumps({
                "id": e["id"], "tipo": e["tipo"], "categoria": e["categoria"],
                "messages": [{"role": "system", "content": SISTEMA},
                             {"role": "user", "content": q},
                             {"role": "assistant", "content": e["respuesta"]}]}, ensure_ascii=False) + "\n")
    print(f"{len(entrada)} ejemplos anonimizados -> anonimizado.jsonl")
    print("Marcadores aplicados:", dict(total))
    print(f"Datos personales inyectados: {inyectados_total} | eliminados: {inyectados_total - len(fugas)} "
          f"({100 * (inyectados_total - len(fugas)) / max(inyectados_total, 1):.1f}%)")
    for f_ in fugas:
        print("  FUGA:", f_)
    print("\nEjemplos antes -> después:")
    mostrados = 0
    for e, l in zip(entrada, open(base / "anonimizado.jsonl", encoding="utf-8")):
        despues = json.loads(l)["messages"][1]["content"]
        if despues != e["pregunta_cruda"] and mostrados < 6:
            print(f"  ANTES:   {e['pregunta_cruda']}\n  DESPUÉS: {despues}\n")
            mostrados += 1


if __name__ == "__main__":
    main()
