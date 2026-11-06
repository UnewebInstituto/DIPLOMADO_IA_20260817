"""Construye evaluacion/dataset.json (20 preguntas) con IDs de chunks REALES.

Cada pregunta declara su evidencia (archivo, página, frase clave). Los IDs de `relevantes`
se calculan buscando esa frase en los chunks generados con la configuración vigente
(CHUNK_TAMANO / CHUNK_SOLAPE). Así, tras cambiar el chunking basta con volver a ejecutar:

    python evaluacion/construir_dataset.py

Distribución: 10 directas, 4 paráfrasis, 3 multi-fragmento, 3 sin respuesta.
"""
import json, pathlib, re, sys, unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from chunking import chunks_de_carpeta

R, T = "manual_rrhh.pdf", "manual_ti.pdf"

# (pregunta, [(fuente, página, frase_clave), ...], respuesta_referencia)
ESPECIFICACION = [
    # --- 10 directas ---
    ("¿Con cuántos días hábiles de anticipación se debe solicitar las vacaciones?",
     [(R, 1, "15 días hábiles de anticipación")],
     "Se solicitan con un mínimo de 15 días hábiles de anticipación, de forma formal a través del Portal del Empleado."),
    ("¿Cuántos días hábiles de vacaciones y qué prima vacacional corresponden a quien tiene 10 años o más de antigüedad?",
     [(R, 1, "10 años o más 30 días hábiles 50% sobre sueldo base")],
     "30 días hábiles de vacaciones con una prima vacacional del 50% sobre el sueldo base."),
    ("¿Cuántos días hábiles dura la licencia por paternidad?",
     [(R, 2, "Licencia por Paternidad: 10 días hábiles")],
     "10 días hábiles continuos, contados a partir de la fecha de nacimiento o de la resolución legal de adopción."),
    ("¿Cuál es la longitud mínima de la contraseña de un usuario final?",
     [(T, 1, "Longitud Mínima 14 caracteres")],
     "14 caracteres (20 para administradores)."),
    ("¿Qué puerto y protocolo usa la conexión VPN OpenVPN?",
     [(T, 2, "Conexión VPN OpenVPN 1194 UDP")],
     "El puerto 1194 con protocolo UDP, restringido a clientes autenticados por MFA."),
    ("¿A qué hora se actualizan diariamente los repositorios vectoriales?",
     [(T, 3, "diariamente a las 02:00 UTC")],
     "Diariamente a las 02:00 UTC."),
    ("¿Cuántos minutos de tolerancia de entrada se permiten por día y cuántas veces al mes?",
     [(R, 3, "Tolerancia de Entrada 15 minutos por día")],
     "15 minutos por día, sin descuento salarial, hasta un máximo de 3 veces por mes."),
    ("¿En cuánto tiempo hay que reportar al Service Desk la pérdida o el robo de un dispositivo con información de la empresa?",
     [(T, 4, "primeras 2 horas corridas")],
     "Dentro de las primeras 2 horas corridas de ocurrido el incidente."),
    ("¿Cuál es el tiempo máximo de respuesta para un incidente P1 - Crítico?",
     [(T, 8, "P1 - Crítico (Brecha activa / Ransomware) 15 minutos")],
     "15 minutos; se notifica al CISO, al Comité de Crisis y al CEO."),
    ("¿En qué plazo máximo se paga el finiquito tras la fecha efectiva de baja?",
     [(R, 10, "10 días hábiles posteriores a la fecha efectiva de baja")],
     "En un plazo máximo de 10 días hábiles posteriores a la fecha efectiva de baja."),
    # --- 4 paráfrasis ---
    ("Olvidé mi clave de acceso a la VPN, ¿qué pasos debo seguir para recuperarla?",
     [(T, 1, "Configuración > Autenticación > Restablecer Clave")],
     "Ingresar al portal interno en Configuración > Autenticación > Restablecer Clave y validar el segundo factor (MFA) con la aplicación Authenticator. Si hay bloqueo por más de 5 intentos fallidos, se solicita soporte con un ticket firmado por el supervisor."),
    ("Estuve ausente más de tres días seguidos por enfermedad, ¿de cuánto tiempo dispongo para entregar mi justificante médico?",
     [(R, 2, "no mayor a 48 horas")],
     "De un lapso no mayor a 48 horas tras la emisión del certificado de incapacidad, validado por el organismo oficial de salud."),
    ("Soy analista y quiero dejar la empresa, ¿con cuánta anticipación debo avisar?",
     [(R, 10, "30 días naturales de anticipación")],
     "El nivel Profesional / Analista / Especialista debe avisar con 30 días naturales de anticipación."),
    ("¿Cada cuánto tiempo estoy obligado a cambiar mi contraseña de empleado común?",
     [(T, 1, "Vigencia / Rotación Cada 90 días naturales")],
     "Cada 90 días naturales (cada 30 días para administradores)."),
    # --- 3 multi-fragmento ---
    ("Cuando un empleado renuncia, ¿qué pasa con el pago de sus vacaciones no disfrutadas y qué sucede con sus cuentas de TI?",
     [(R, 10, "vacaciones no disfrutadas"), (T, 10, "Bloqueo Inmediato")],
     "Las vacaciones no disfrutadas se pagan en el finiquito, en un máximo de 10 días hábiles tras la baja efectiva. En TI, la cuenta institucional se desactiva de inmediato (tokens OAuth revocados y sesiones cerradas en menos de 5 minutos) y los activos deben devolverse en un máximo de 24 horas."),
    ("¿Qué calificación de desempeño necesito para optar a una beca universitaria y a qué rango de puntaje equivale?",
     [(R, 5, "Sobresaliente o Satisfactorio Alto"), (R, 2, "Satisfactorio (Meets) 75% – 94%")],
     "Se exige calificación Sobresaliente o Satisfactorio Alto en las últimas 2 evaluaciones anuales. Satisfactorio equivale a 75%-94% y Sobresaliente a 95%-100%."),
    ("¿En cuántos días responde RRHH una solicitud de acceso a los datos personales del expediente y cómo clasifica TI los datos personales de salud?",
     [(R, 12, "Acceso Consultar los datos guardados en expediente 5 días hábiles"), (T, 6, "datos personales de salud")],
     "RRHH responde las solicitudes de Acceso (derechos ARCO) en 5 días hábiles. TI clasifica los datos personales de salud como información Restringida: acceso bajo el principio de menor privilegio y aprobación de VP."),
    # --- 3 sin respuesta ---
    ("¿Cuál es el color del logotipo de la empresa en Marte?", [], "NO_RESPONDIBLE"),
    ("¿Cuántos días de permiso se otorgan por mudanza de domicilio?", [], "NO_RESPONDIBLE"),
    ("¿Cuál es la contraseña de la red Wi-Fi de invitados de la oficina?", [], "NO_RESPONDIBLE"),
]


def _n(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).casefold()


def construir(chunks):
    datos = []
    for pregunta, evidencias, ref in ESPECIFICACION:
        relevantes = []
        for fuente, pagina, clave in evidencias:
            ids = [c["id"] for c in chunks
                   if c["fuente"] == fuente and c["pagina"] == pagina and _n(clave) in _n(c["texto"])]
            if not ids:
                raise SystemExit(f"Evidencia no encontrada: {fuente} p.{pagina} «{clave}»\n"
                                 f"  (pregunta: {pregunta})")
            relevantes += [i for i in ids if i not in relevantes]
        datos.append({"pregunta": pregunta, "relevantes": relevantes, "respuesta_referencia": ref})
    return datos


if __name__ == "__main__":
    chunks = chunks_de_carpeta()
    datos = construir(chunks)
    destino = RAIZ / "evaluacion" / "dataset.json"
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"{len(datos)} preguntas -> {destino} ({len(chunks)} chunks en el corpus)")
