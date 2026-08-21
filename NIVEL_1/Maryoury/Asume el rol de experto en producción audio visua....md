

Python  
import os  
from weasyprint import HTML

html\_content \= """\<\!DOCTYPE html\>  
\<html lang="es"\>  
\<head\>  
    \<meta charset="UTF-8"\>  
    \<title\>Guión Audiovisual: Campaña de Lanzamiento Agente de IA para Beneficios\</title\>  
    \<style\>  
        @page {  
            size: A4;  
            margin: 15mm 12mm;  
            background-color: \#f4f6f9;  
        }

        \*, \*::before, \*::after {  
            box-sizing: border-box;  
        }

        body {  
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;  
            font-size: 9.5pt;  
            line-height: 1.4;  
            color: \#1e293b;  
            margin: 0;  
            padding: 0;  
        }

        /\* Header section \*/  
        .header-card {  
            background: linear-gradient(135deg, \#0f172a 0%, \#1e3a8a 100%);  
            color: \#ffffff;  
            padding: 20px 24px;  
            border-radius: 8px;  
            margin-bottom: 20px;  
        }

        .header-card h1 {  
            font-size: 18pt;  
            margin: 0 0 6px 0;  
            font-weight: 700;  
            letter-spacing: \-0.5px;  
            color: \#ffffff;  
        }

        .header-card .subtitle {  
            font-size: 11pt;  
            color: \#93c5fd;  
            margin: 0 0 16px 0;  
            font-weight: 500;  
        }

        .meta-grid {  
            width: 100%;  
            border-collapse: collapse;  
            margin-top: 10px;  
            border-top: 1px solid rgba(255, 255, 255, 0.2);  
            padding-top: 10px;  
        }

        .meta-grid td {  
            font-size: 8.5pt;  
            color: \#cbd5e1;  
            padding: 3px 0;  
            vertical-align: top;  
        }

        .meta-grid td strong {  
            color: \#ffffff;  
        }

        /\* Section titles \*/  
        h2 {  
            font-size: 13pt;  
            color: \#0f172a;  
            border-left: 4px solid \#2563eb;  
            padding-left: 10px;  
            margin: 22px 0 12px 0;  
            text-transform: uppercase;  
            letter-spacing: 0.5px;  
            page-break-after: avoid;  
        }

        /\* Table styling \*/  
        table.script-table {  
            width: 100%;  
            border-collapse: collapse;  
            margin-bottom: 20px;  
            background-color: \#ffffff;  
            border-radius: 6px;  
            overflow: hidden;  
            border: 1px solid \#e2e8f0;  
        }

        table.script-table th {  
            background-color: \#1e293b;  
            color: \#ffffff;  
            text-align: left;  
            padding: 8px 10px;  
            font-size: 8.5pt;  
            text-transform: uppercase;  
            letter-spacing: 0.5px;  
        }

        table.script-table td {  
            padding: 10px;  
            border-bottom: 1px solid \#f1f5f9;  
            vertical-align: top;  
            font-size: 9pt;  
        }

        table.script-table tr:nth-child(even) {  
            background-color: \#f8fafc;  
        }

        .scene-header {  
            background-color: \#eff6ff \!important;  
            font-weight: bold;  
            color: \#1e40af;  
            border-top: 2px solid \#2563eb;  
            border-bottom: 1px solid \#bfdbfe \!important;  
        }

        .scene-header td {  
            padding: 6px 10px \!important;  
            font-size: 8.5pt \!important;  
            text-transform: uppercase;  
        }

        /\* Formatting elements inside table \*/  
        .audio-speaker {  
            font-weight: bold;  
            color: \#0f172a;  
            display: block;  
            margin-bottom: 3px;  
            text-transform: uppercase;  
            font-size: 8pt;  
            letter-spacing: 0.3px;  
        }

        .audio-dialogue {  
            color: \#334155;  
            font-style: normal;  
        }

        .visual-desc {  
            color: \#1e293b;  
            margin-bottom: 4px;  
        }

        .tech-note {  
            font-size: 7.5pt;  
            color: \#64748b;  
            font-style: italic;  
            display: block;  
            margin-top: 4px;  
            background-color: \#f1f5f9;  
            padding: 3px 6px;  
            border-radius: 3px;  
        }

        .badge-scene {  
            background-color: \#2563eb;  
            color: white;  
            padding: 2px 6px;  
            border-radius: 3px;  
            font-size: 7.5pt;  
            margin-right: 6px;  
        }

        /\* Technical summary cards \*/  
        .info-grid {  
            width: 100%;  
            border-collapse: collapse;  
            margin-bottom: 15px;  
        }

        .info-card {  
            background-color: \#ffffff;  
            border: 1px solid \#cbd5e1;  
            border-radius: 6px;  
            padding: 12px;  
            vertical-align: top;  
        }

        .info-card h3 {  
            margin: 0 0 6px 0;  
            font-size: 10pt;  
            color: \#1e3a8a;  
            border-bottom: 1px solid \#e2e8f0;  
            padding-bottom: 4px;  
        }

        .info-card ul {  
            margin: 0;  
            padding-left: 16px;  
            font-size: 8.5pt;  
            color: \#475569;  
        }

        .info-card li {  
            margin-bottom: 4px;  
        }

        /\* Callout box \*/  
        .callout {  
            background-color: \#f0fdf4;  
            border: 1px solid \#bbf7d0;  
            border-left: 4px solid \#16a34a;  
            padding: 10px 12px;  
            border-radius: 4px;  
            margin-top: 15px;  
            font-size: 8.5pt;  
            color: \#14532d;  
        }

        .callout strong {  
            color: \#15803d;  
        }  
    \</style\>  
\</head\>  
\<body\>

    \<div class="header-card"\>  
        \<h1\>GUIÓN TÉCNICO AUDIOVISUAL\</h1\>  
        \<div class="subtitle"\>Campaña de Comunicación Interna: Lanzamiento Agente de IA para Gestión de Beneficios\</div\>  
          
        \<table class="meta-grid"\>  
            \<tr\>  
                \<td width="33%"\>\<strong\>Formato:\</strong\> Video Promocional / Tutorial Motion Graphics\</td\>  
                \<td width="33%"\>\<strong\>Duración Estimada:\</strong\> 2 minutos (120 segundos)\</td\>  
                \<td width="33%"\>\<strong\>Público Objetivo:\</strong\> Colaboradores de la Entidad Financiera\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>Tono:\</strong\> Cercano, Dinámico, Tecnológico, Institucional\</td\>  
                \<td\>\<strong\>Locución:\</strong\> Voz Off (Cálida y profesional) \+ Personaje real/3D\</td\>  
                \<td\>\<strong\>Objetivo:\</strong\> Socializar el uso del nuevo Agente de IA para RRHH\</td\>  
            \</tr\>  
        \</table\>  
    \</div\>

    \<h2\>I. Estructura de Producción y Recomendaciones Técnicas\</h2\>  
      
    \<table class="info-grid"\>  
        \<tr\>  
            \<td class="info-card" width="50%" style="padding-right: 6px;"\>  
                \<h3\>Estilo Visual y Gráfico\</h3\>  
                \<ul\>  
                    \<li\>\<strong\>Mix Live-Action & Motion Graphics:\</strong\> Tomas de colaboradores usando laptop/smartphone integradas con overlays animados de la interfaz del agente.\</li\>  
                    \<li\>\<strong\>Paleta de Color:\</strong\> Azul Institucional (\#1e3a8a), Blanco, y Verde Éxito (\#16a34a) para estados de aprobación.\</li\>  
                    \<li\>\<strong\>Screencasts UI:\</strong\> Animación vectorial limpia simulando la experiencia en Teams/Slack/Intranet.\</li\>  
                \</ul\>  
            \</td\>  
            \<td class="info-card" width="50%" style="padding-left: 6px;"\>  
                \<h3\>Diseño Sonoro y MÚSICA\</h3\>  
                \<ul\>  
                    \<li\>\<strong\>Música de Fondo:\</strong\> Track de estilo \*Corporate Tech\* / \*Uplifting Modern\* (tempo medio, pulso moderno pero no invasivo).\</li\>  
                    \<li\>\<strong\>Efectos de Audio (SFX):\</strong\> Pop de mensajes recibidos, swishes suaves en transiciones, chime sutil para confirmación exitosa de trámites.\</li\>  
                \</ul\>  
            \</td\>  
        \</tr\>  
    \</table\>

    \<h2\>II. Guión Literario y Técnico Dos Columnas\</h2\>

    \<table class="script-table"\>  
        \<thead\>  
            \<tr\>  
                \<th width="8%"\>Toma\</th\>  
                \<th width="42%"\>Video / Planos / Arte / On-Screen Text\</th\>  
                \<th width="50%"\>Audio / Locución (VO) / SFX / Música\</th\>  
            \</tr\>  
        \</thead\>  
        \<tbody\>  
            \<\!-- ESCENA 1 \--\>  
            \<tr class="scene-header"\>  
                \<td colspan="3"\>\<span class="badge-scene"\>ESCENA 1\</span\> INTRODUCCIÓN Y PUNTOS DE DOLOR (00:00 \- 00:18)\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>01\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>PLANO MEDIO:\</strong\> Colaborador en la oficina mirando su laptop con expresión de duda. Hace un clic y suspira suavemente.\</div\>  
                    \<div class="visual-desc"\>\<strong\>TEXTO EN PANTALLA:\</strong\> "¿Necesitas gestionar tus beneficios?"\</div\>  
                    \<span class="tech-note"\>Corte rápido a otro colaborador revisando el celular en una cafetería.\</span\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Música:\</span\> Entra música tech rítmica y ligera.\<br\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "¿Necesitas saber cuántos días de vacaciones te quedan, pedir un reembolso o solicitar un anticipo de sueldo, pero no sabes por dónde empezar o cuánto va a tardar?"  
                \</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>02\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>GRAPHIC OVERLAY:\</strong\> Iconos de correos acumulados, formularios de papel y un reloj marcando el paso del tiempo. Reducción a cero con efecto \*dissolve\*.\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "Olvídate de los correos interminables y los tiempos de espera. ¡Llegó la forma más rápida y fácil de gestionar tus beneficios corporativos\!"  
                \</td\>  
            \</tr\>

            \<\!-- ESCENA 2 \--\>  
            \<tr class="scene-header"\>  
                \<td colspan="3"\>\<span class="badge-scene"\>ESCENA 2\</span\> PRESENTACIÓN DEL AGENTE DE IA Y AUTENTICACIÓN (00:18 \- 00:35)\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>03\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>ANIMACIÓN / SCREENCAST:\</strong\> Aparece en pantalla la interfaz de Microsoft Teams / Slack / App Móvil con un avatar dinámico e inteligente cargando.\</div\>  
                    \<div class="visual-desc"\>\<strong\>TEXTO EN PANTALLA:\</strong\> "Tu nuevo Agente de IA para Beneficios"\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>SFX:\</span\> Chime digital de inicio de sesión.\<br\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "Te presentamos a nuestro nuevo Agente de Inteligencia Artificial de Gente y Cultura. Tu asistente personal disponible las 24 horas, los 7 días de la semana."  
                \</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>04\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>CLOSE-UP INTERFAZ:\</strong\> El colaborador hace clic en el chat. Se muestra un gráfico animado que simboliza \*\*SSO (Single Sign-On)\*\* conectando con la ficha del empleado (Workday/SAP).\</div\>  
                    \<div class="visual-desc"\>\<strong\>TEXTO EN PANTALLA:\</strong\> "Acceso Seguro \- SSO | Tu Perfil Integrado"\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "Ingresar es tan simple como abrir tu canal corporativo preferido. Gracias al inicio de sesión único, la IA te reconoce al instante, con acceso seguro a tu perfil, saldo de días y tipo de contrato."  
                \</td\>  
            \</tr\>

            \<\!-- ESCENA 3 \--\>  
            \<tr class="scene-header"\>  
                \<td colspan="3"\>\<span class="badge-scene"\>ESCENA 3\</span\> CASO 1: CONSULTA INFORMATIVA Y REGLAS DE NEGOCIO (00:35 \- 00:55)\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>05\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>ANIMACIÓN INTERFAZ:\</strong\> El usuario escribe en lenguaje natural: \<em\>"¿Cuántos días de vacaciones tengo y cómo pido días de estudio?"\</em\>.\</div\>  
                    \<div class="visual-desc"\>El agente responde en menos de un segundo mostrando el saldo exacto y la política destacada en un cuadro limpio.\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>SFX:\</span\> Tecleo rápido y pop de mensaje instantáneo.\<br\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "Hazle preguntas en tu propio lenguaje. Por ejemplo: consulta tus días disponibles de vacaciones o las políticas para tus días de estudio. El agente busca la regla exacta para ti y te responde en segundos."  
                \</td\>  
            \</tr\>

            \<\!-- ESCENA 4 \--\>  
            \<tr class="scene-header"\>  
                \<td colspan="3"\>\<span class="badge-scene"\>ESCENA 4\</span\> CASO 2: SOLICITUD TRANSACCIONAL Y DOCUMENTOS (00:55 \- 01:20)\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>06\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>ANIMACIÓN INTERFAZ:\</strong\> El usuario escribe: \<em\>"Quiero inscribir a mi cónyuge en el seguro complementario"\</em\>.\</div\>  
                    \<div class="visual-desc"\>El agente despliega una ventana guiada para adjuntar el Certificado de Matrimonio. El usuario arrastra el archivo.\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "¿Necesitas realizar un trámite? El agente valida tus requisitos de elegibilidad automáticamente. Solo sigue los pasos, adjunta tus documentos en el mismo chat..."  
                \</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>07\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>ANIMACIÓN SISTEMAS:\</strong\> Gráfico animado mostrando la integración de la IA enviando la firma digital e integrando el registro directo en el ERP/HRIS. Aparece un checklist en verde.\</div\>  
                    \<div class="visual-desc"\>\<strong\>TEXTO EN PANTALLA:\</strong\> "Procesamiento Automático \+ Integración ERP"\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>SFX:\</span\> Tono suave de éxito / Checkmark.\<br\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "...y ¡listo\! La IA tramita las aprobaciones y actualiza el sistema de manera automática, sin papeleos innecesarios."  
                \</td\>  
            \</tr\>

            \<\!-- ESCENA 5 \--\>  
            \<tr class="scene-header"\>  
                \<td colspan="3"\>\<span class="badge-scene"\>ESCENA 5\</span\> DERIVACIÓN HUMANA Y SEGUIMIENTO (01:20 \- 01:40)\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>08\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>SPLIT SCREEN:\</strong\> A la izquierda, la pantalla con el mensaje del agente: \<em\>"Transferiendo con especialista de RRHH..."\</em\>. A la derecha, un ejecutivo de RRHH sonriente en su puesto de trabajo con una tablet viendo el historial.\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "¿Tienes una situación especial o un caso complejo? No te preocupes. El agente derivará tu caso con un especialista humano de RRHH, transfiriéndole todo el historial para que no tengas que repetir nada."  
                \</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>09\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>ANIMACIÓN NOTIFICACIÓN & CSAT:\</strong\> Aparece una notificación Push en el teléfono con el comprobante de ticket. Luego, una pantalla rápida con 5 estrellas interactivas siendo evaluadas con 5/5.\</div\>  
                    \<div class="visual-desc"\>\<strong\>TEXTO EN PANTALLA:\</strong\> "Notificaciones en Vivo | Califica tu Experiencia ⭐⭐⭐⭐⭐"\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "Recibirás actualizaciones de estado en tiempo real y podrás calificar tu experiencia para ayudarnos a seguir mejorando."  
                \</td\>  
            \</tr\>

            \<\!-- ESCENA 6 \--\>  
            \<tr class="scene-header"\>  
                \<td colspan="3"\>\<span class="badge-scene"\>ESCENA 6\</span\> CIERRE Y LLAMADO A LA ACCIÓN (01:40 \- 02:00)\</td\>  
            \</tr\>  
            \<tr\>  
                \<td\>\<strong\>10\</strong\>\</td\>  
                \<td\>  
                    \<div class="visual-desc"\>\<strong\>PLANO GENERAL:\</strong\> Varios colaboradores en la oficina trabajando de forma fluida y relajada.\</div\>  
                    \<div class="visual-desc"\>Cierre a pantalla con el logo de la Entidad Financiera y el icono del Agente de IA.\</div\>  
                    \<div class="visual-desc"\>\<strong\>TEXTO EN PANTALLA:\</strong\> "¡Inicia tu consulta hoy en Teams/Slack/Intranet\! | Tu tiempo importa"\</div\>  
                \</td\>  
                \<td\>  
                    \<span class="audio-speaker"\>Música:\</span\> In crescendo armónico, directo hacia la nota final de cierre.\<br\>  
                    \<span class="audio-speaker"\>Locutora (VO):\</span\> "Más ágil, más simple y siempre a tu disposición. Comienza a gestionar tus beneficios hoy mismo buscando a nuestro Agente de IA en tu plataforma corporativa. ¡Tus beneficios, al alcance de un clic\!"\<br\>  
                    \<span class="audio-speaker"\>SFX:\</span\> Cierre institucional corporativo.  
                \</td\>  
            \</tr\>  
        \</tbody\>  
    \</table\>

    \<div class="callout"\>  
        \<strong\>Notas de Post-Producción:\</strong\> Se sugiere que la versión masterizada del video incluya subtítulos en español (CC) para su reproducción en pantallas informativas de los pisos corporativos y sucursales donde el audio pueda estar desactivado.  
    \</div\>

\</body\>  
\</html\>  
"""

with open("guion\_campana\_agente\_ia.html", "w", encoding="utf-8") as f:  
    f.write(html\_content)

HTML("guion\_campana\_agente\_ia.html").write\_pdf("guion\_campana\_agente\_ia.pdf")  
print("PDF generado con éxito: guion\_campana\_agente\_ia.pdf")

Resultado de código

PDF generado con éxito: guion\_campana\_agente\_ia.pdf

Tu guión audiovisual para la campaña informativa del Agente de IA está listo.

![Ícono de PDF][image1]

guion\_campana\_agente\_ia  
PDF

Abrir

### **Resumen del Contenido del Guión Audiovisual**

* **Formato y Estilo:** Video Promocional / Tutorial Dinámico que combina escenas *Live-Action* de colaboradores en la entidad financiera con animaciones *Motion Graphics* que simulan la pantalla del agente.  
* **Estructura Narrativa (2 Minutos / 6 Escenas):**  
  1. **Escena 1 (Problema/Gancho):** Se conecta con la frustración típica de no saber cómo solicitar un beneficio o el tiempo que toman las gestiones.  
  2. **Escena 2 (Presentación y SSO):** Muestra el acceso fácil vía canales corporativos (Teams, Slack, Intranet) y la autenticación automática con la ficha del empleado.  
  3. **Escena 3 (Consultas Informativas):** Demuestra cómo hacer preguntas en lenguaje natural sobre políticas y saldos de vacaciones.  
  4. **Escena 4 (Operaciones Transaccionales):** Ejemplifica la solicitud de beneficios (como seguro complementario o anticipos), adjunto de documentos e integración en segundo plano con el ERP/HRIS.  
  5. **Escena 5 (Derivación Humana y Seguimiento):** Destaca la transferencia sin fricción a un especialista humano de RRHH manteniendo el historial y la medición de satisfacción (CSAT).  
  6. **Escena 6 (Cierre y Call to Action):** Cierre institucional invitando al personal a utilizar la herramienta.

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABaklEQVR4Xu2XO0/DMBSF/Z+g/QE1M2TuxATMFayVOoIEWxc2Fpg6MTGxMCKVFYmVlj6gbcJLQAk+ETdyrkNxCnIXH+lITu6N/cXXtmQhlHqyHPRlqa0cO/GKGqtSWsfYAg0jwZF7cikQA7ns7s+ZB2omBH/p2h7AA3gAA+BhoxqHe42MR7WtTM6otvlrzri+Y+SQh9XVnwEejw7jPL3fXMfDtUqS83J2ysOJnlvHaT9vV5c8nCrcbRQHgKLm/kwACLPzbwAYMGoepM+IcQBM6VPrxMghgM8oNEpwb1sC1ArJpDwAPKP+PIcAPrqdTP/cMwGmd53EpHkAIOqHSmgNwEVTVxSAx6wBsPLR0evFeWabFQVAG9YXnxWAvl91G4tQ+4YD/GkN2ABwTerbiwPAe8qZG0A/iunk4x7bHMXfORN1JPPvdRsAru0BPIAHAMDCrmbKbYELYk7Aibt0Q0aj7/KSqi6lt7IcYOwvVnl9HqNTU2QAAAAASUVORK5CYII=>