

Python  
import os  
from weasyprint import HTML

html\_content \= """\<\!DOCTYPE html\>  
\<html lang="es"\>  
\<head\>  
    \<meta charset="UTF-8"\>  
    \<title\>Guión Técnico Audio Visual \- Agente IA RRHH\</title\>  
    \<style\>  
        @page {  
            size: A4 portrait;  
            margin: 18mm 15mm;  
            background-color: \#f8fafc;  
            @bottom-right {  
                content: "Página " counter(page) " de " counter(pages);  
                font-family: 'Helvetica Neue', Arial, sans-serif;  
                font-size: 8pt;  
                color: \#64748b;  
            }  
            @bottom-left {  
                content: "Campaña Informativa Institucional | Gestión de Beneficios IA";  
                font-family: 'Helvetica Neue', Arial, sans-serif;  
                font-size: 8pt;  
                color: \#64748b;  
            }  
        }

        \*, \*::before, \*::after {  
            box-sizing: border-box;  
        }

        body {  
            font-family: 'Helvetica Neue', Arial, sans-serif;  
            margin: 0;  
            padding: 0;  
            color: \#1e293b;  
            background-color: \#f8fafc;  
            font-size: 10pt;  
            line-height: 1.5;  
        }

        /\* Header Layout using Table \*/  
        .header-table {  
            width: 100%;  
            border-collapse: collapse;  
            background: linear-gradient(135deg, \#0f172a 0%, \#1e3a8a 100%);  
            color: \#ffffff;  
            border-radius: 8px;  
            margin-bottom: 20px;  
        }

        .header-table td {  
            padding: 20px 24px;  
            vertical-align: middle;  
        }

        .header-title {  
            font-size: 18pt;  
            font-weight: 700;  
            margin: 0 0 6px 0;  
            letter-spacing: \-0.5px;  
            color: \#ffffff;  
        }

        .header-subtitle {  
            font-size: 10.5pt;  
            color: \#93c5fd;  
            margin: 0;  
            font-weight: 400;  
        }

        .badge-table {  
            text-align: right;  
            vertical-align: top \!important;  
            padding-top: 20px \!important;  
            padding-right: 24px \!important;  
        }

        .badge {  
            display: inline-block;  
            background-color: rgba(255, 255, 255, 0.15);  
            border: 1px solid rgba(255, 255, 255, 0.25);  
            color: \#ffffff;  
            padding: 4px 12px;  
            border-radius: 20px;  
            font-size: 8.5pt;  
            font-weight: 600;  
            text-transform: uppercase;  
            letter-spacing: 0.5px;  
        }

        /\* Meta Spec Box \*/  
        .specs-table {  
            width: 100%;  
            border-collapse: collapse;  
            background-color: \#ffffff;  
            border: 1px solid \#e2e8f0;  
            border-radius: 8px;  
            margin-bottom: 22px;  
        }

        .specs-table td {  
            padding: 10px 14px;  
            width: 25%;  
            font-size: 9pt;  
            border-right: 1px solid \#e2e8f0;  
        }

        .specs-table td:last-child {  
            border-right: none;  
        }

        .spec-label {  
            font-weight: 700;  
            color: \#475569;  
            text-transform: uppercase;  
            font-size: 7.5pt;  
            display: block;  
            margin-bottom: 2px;  
        }

        .spec-value {  
            color: \#0f172a;  
            font-weight: 600;  
        }

        /\* Section Styling \*/  
        .section-header {  
            border-left: 4px solid \#2563eb;  
            padding-left: 10px;  
            margin: 22px 0 12px 0;  
            page-break-after: avoid;  
        }

        .section-title {  
            font-size: 13pt;  
            font-weight: 700;  
            color: \#0f172a;  
            margin: 0;  
            text-transform: uppercase;  
            letter-spacing: 0.3px;  
        }

        /\* Narrative Summary Box \*/  
        .narrative-box {  
            background-color: \#ffffff;  
            border: 1px solid \#cbd5e1;  
            border-left: 4px solid \#0d9488;  
            padding: 12px 16px;  
            border-radius: 0 6px 6px 0;  
            margin-bottom: 20px;  
            font-size: 9.5pt;  
            color: \#334155;  
        }

        /\* Script Two-Column Table \*/  
        .script-table {  
            width: 100%;  
            border-collapse: collapse;  
            background-color: \#ffffff;  
            border: 1px solid \#cbd5e1;  
            border-radius: 6px;  
            margin-bottom: 20px;  
        }

        .script-table th {  
            background-color: \#1e293b;  
            color: \#ffffff;  
            font-size: 9pt;  
            font-weight: 700;  
            text-transform: uppercase;  
            letter-spacing: 0.5px;  
            padding: 10px 14px;  
            text-align: left;  
            border-bottom: 2px solid \#0f172a;  
        }

        .script-table td {  
            padding: 12px 14px;  
            vertical-align: top;  
            border-bottom: 1px solid \#e2e8f0;  
            font-size: 9.5pt;  
        }

        .script-table tr:last-child td {  
            border-bottom: none;  
        }

        .script-table tr:nth-child(even) {  
            background-color: \#f8fafc;  
        }

        /\* Column specific styling \*/  
        .col-scene {  
            width: 10%;  
            font-weight: 700;  
            color: \#2563eb;  
            text-align: center;  
        }

        .col-video {  
            width: 45%;  
            color: \#334155;  
        }

        .col-audio {  
            width: 45%;  
            color: \#0f172a;  
        }

        .video-tag {  
            font-size: 8pt;  
            font-weight: 700;  
            color: \#475569;  
            background-color: \#f1f5f9;  
            padding: 2px 6px;  
            border-radius: 4px;  
            border: 1px solid \#e2e8f0;  
            display: inline-block;  
            margin-bottom: 4px;  
            text-transform: uppercase;  
        }

        .speaker-tag {  
            font-size: 8.5pt;  
            font-weight: 700;  
            color: \#1e3a8a;  
            display: block;  
            margin-bottom: 3px;  
            text-transform: uppercase;  
        }

        .locution {  
            font-style: normal;  
        }

        .sfx-tag {  
            font-size: 8pt;  
            font-style: italic;  
            color: \#d97706;  
            display: block;  
            margin-top: 4px;  
        }

        /\* Production Notes Callout \*/  
        .notes-table {  
            width: 100%;  
            border-collapse: collapse;  
            margin-top: 15px;  
            background-color: \#eff6ff;  
            border: 1px solid \#bfdbfe;  
            border-radius: 6px;  
        }

        .notes-table td {  
            padding: 12px 16px;  
            font-size: 9pt;  
            color: \#1e40af;  
        }

        .notes-title {  
            font-weight: 700;  
            margin-bottom: 4px;  
            display: block;  
            text-transform: uppercase;  
            font-size: 8.5pt;  
            letter-spacing: 0.5px;  
        }

        ul {  
            margin: 4px 0 0 18px;  
            padding: 0;  
        }

        li {  
            margin-bottom: 3px;  
        }  
    \</style\>  
\</head\>  
\<body\>

    \<\!-- Header Section \--\>  
    \<table class="header-table"\>  
        \<tr\>  
            \<td\>  
                \<h1 class="header-title"\>Guión Técnico Audiovisual\</h1\>  
                \<p class="header-subtitle"\>Campaña de Lanzamiento: Agente de Asistencia Contractual y Beneficios con IA\</p\>  
            \</td\>  
            \<td class="badge-table"\>  
                \<span class="badge"\>Producción AV / Corporativo\</span\>  
            \</td\>  
        \</tr\>  
    \</table\>

    \<\!-- Specification Metadata \--\>  
    \<table class="specs-table"\>  
        \<tr\>  
            \<td\>  
                \<span class="spec-label"\>Formato\</span\>  
                \<span class="spec-value"\>Video Animado / Motion Graphics 2D\</span\>  
            \</td\>  
            \<td\>  
                \<span class="spec-label"\>Duración\</span\>  
                \<span class="spec-value"\>60 Segundos\</span\>  
            \</td\>  
            \<td\>  
                \<span class="spec-label"\>Audiencia Target\</span\>  
                \<span class="spec-value"\>Colaboradores de la Entidad Financiera\</span\>  
            \</td\>  
            \<td\>  
                \<span class="spec-label"\>Tono / Estilo\</span\>  
                \<span class="spec-value"\>Dinámico, Ágil, Cercano e Innovador\</span\>  
            \</td\>  
        \</tr\>  
    \</table\>

    \<\!-- Executive Summary / Objective \--\>  
    \<div class="section-header"\>  
        \<h2 class="section-title"\>1. Enfoque Narrativo y Objetivo Audiovisual\</h2\>  
    \</div\>  
    \<div class="narrative-box"\>  
        \<strong\>Objetivo de la Campaña:\</strong\> Informar y promover el uso del nuevo Agente de IA para el autoservicio de Recursos Humanos. Se busca comunicar de forma clara y directa cómo la herramienta resuelve dudas sobre beneficios (seguros, créditos, becas) y tramita documentos contractuales (cartas de trabajo, vacaciones) de manera inmediata, segura y disponible 24/7.  
    \</div\>

    \<\!-- Script Table \--\>  
    \<div class="section-header"\>  
        \<h2 class="section-title"\>2. Guión Técnico Formato Dos Columnas (Visual & Audio)\</h2\>  
    \</div\>

    \<table class="script-table"\>  
        \<thead\>  
            \<tr\>  
                \<th class="col-scene"\>Escena\</th\>  
                \<th class="col-video"\>Video / Planteamiento Visual (FX / Motion)\</th\>  
                \<th class="col-audio"\>Audio / Locución & Efectos (SFX)\</th\>  
            \</tr\>  
        \</thead\>  
        \<tbody\>  
            \<\!-- Escena 1 \--\>  
            \<tr\>  
                \<td class="col-scene"\>01\<br\>\<small style="color:\#64748b; font-weight:normal;"\>(0-8s)\</small\>\</td\>  
                \<td class="col-video"\>  
                    \<span class="video-tag"\>Plano Medio / Animación\</span\>\<br\>  
                    Un colaborador frente a su computadora consulta su reloj preocupado. En pantalla flotan signos de interrogación y formularios sobrevolando: \<em\>"¿Cómo pido una carta de trabajo?"\</em\>, \<em\>"¿Cuándo es mi reembolso de odontología?"\</em\>. El entorno transiciona de un ambiente sofocado a uno limpio y digital.  
                \</td\>  
                \<td class="col-audio"\>  
                    \<span class="speaker-tag"\>Locutor (Cálido y Dinámico)\</span\>  
                    \<span class="locution"\>"¿Necesitas una carta de trabajo urgente o consultar la cobertura de tu seguro y no quieres esperar trámites largos?"\</span\>  
                    \<span class="sfx-tag"\>\[SFX: Música corporativa moderna y rítmica entra de fondo. Sonido sutil de tic-tac que se transforma en un 'chime' tecnológico claro\].\</span\>  
                \</td\>  
            \</tr\>  
            \<\!-- Escena 2 \--\>  
            \<tr\>  
                \<td class="col-scene"\>02\<br\>\<small style="color:\#64748b; font-weight:normal;"\>(8-18s)\</small\>\</td\>  
                \<td class="col-video"\>  
                    \<span class="video-tag"\>Plano General / Interfaces\</span\>\<br\>  
                    Aparece en pantalla el logo animado del \*\*Agente de IA de RRHH\*\*. Se muestran iconos conectándose orgánicamente: \*\*Microsoft Teams\*\*, \*\*WhatsApp Corporativo\*\* e \*\*Intranet\*\*. Se resalta un candado dorado de seguridad que se cierra con la sigla \*\*SSO (Single Sign-On)\*\*.  
                \</td\>  
                \<td class="col-audio"\>  
                    \<span class="speaker-tag"\>Locutor\</span\>  
                    \<span class="locution"\>"¡Llegó tu nuevo Agente de Asistencia Contractual y Beneficios con Inteligencia Artificial\! Disponible 24/7 en Teams, WhatsApp Corporativo o la Intranet, ingresando fácil y seguro con tu cuenta institucional."\</span\>  
                    \<span class="sfx-tag"\>\[SFX: Notificación digital suave \+ click de conexión exitosa\].\</span\>  
                \</td\>  
            \</tr\>  
            \<\!-- Escena 3 \--\>  
            \<tr\>  
                \<td class="col-scene"\>03\<br\>\<small style="color:\#64748b; font-weight:normal;"\>(18-32s)\</small\>\</td\>  
                \<td class="col-video"\>  
                    \<span class="video-tag"\>Primer Plano / UI UX Demo\</span\>\<br\>  
                    Simulación gráfica de chat interactivo. El usuario escribe en lenguaje natural: \<em\>"¿Cómo pido el reembolso de odontología?"\</em\>.  
                    \<br\>\<br\>  
                    Se despliega una animación de \*\*3 caminos iluminados\*\*:  
                    \<br\>• \<strong\>Vía A (Info):\</strong\> Aparece un extracto de la política de salud en pantalla.  
                    \<br\>• \<strong\>Vía B (Trámite):\</strong\> Se genera instantáneamente un documento PDF con sello de descarga.  
                    \<br\>• \<strong\>Vía C (Casos Complejos):\</strong\> Se crea un ticket automatizado hacia el equipo de RRHH.  
                \</td\>  
                \<td class="col-audio"\>  
                    \<span class="speaker-tag"\>Locutor\</span\>  
                    \<span class="locution"\>"Simplemente escribe lo que necesitas en tu propio lenguaje. La IA entiende tu perfil y resuelve al instante: te explica las políticas de beneficios, genera directamente tus constancias y vacaciones en PDF, o si tu caso es especial, genera un ticket priorizado con el equipo de RRHH."\</span\>  
                    \<span class="sfx-tag"\>\[SFX: Tecleo fluido de teclado \+ sonido de 'pop' al aparecer los tres caminos \+ 'whoosh' de generación de PDF\].\</span\>  
                \</td\>  
            \</tr\>  
            \<\!-- Escena 4 \--\>  
            \<tr\>  
                \<td class="col-scene"\>04\<br\>\<small style="color:\#64748b; font-weight:normal;"\>(32-48s)\</small\>\</td\>  
                \<td class="col-video"\>  
                    \<span class="video-tag"\>Infografía Motion Graphics\</span\>\<br\>  
                    Zoom in a elementos de seguridad: Un escudo digital enmascara datos como la cédula y el sueldo (\*\*Enmascaramiento PII\*\*). A su lado, un gráfico animado muestra requisitos de elegibilidad aprobados automáticamente (ej. 6 meses de antigüedad para créditos).  
                \</td\>  
                \<td class="col-audio"\>  
                    \<span class="speaker-tag"\>Locutor\</span\>  
                    \<span class="locution"\>"Todo esto con total confidencialidad. Tu información personal y sensible está protegida bajo los más estrictos estándares de seguridad bancaria, validando tus beneficios automáticamente según tu antigüedad y contrato."\</span\>  
                    \<span class="sfx-tag"\>\[SFX: Sonido de escudo protector activándose \+ tono de aprobación/check positivo\].\</span\>  
                \</td\>  
            \</tr\>  
            \<\!-- Escena 5 \--\>  
            \<tr\>  
                \<td class="col-scene"\>05\<br\>\<small style="color:\#64748b; font-weight:normal;"\>(48-60s)\</small\>\</td\>  
                \<td class="col-video"\>  
                    \<span class="video-tag"\>Plano Final / Call To Action\</span\>\<br\>  
                    El colaborador sonríe mientras recibe su comprobante en el teléfono. Transición a pantalla final con los accesos directos (Icons Teams, WhatsApp e Intranet), el slogan de la campaña y el logotipo de la entidad financiera.  
                \</td\>  
                \<td class="col-audio"\>  
                    \<span class="speaker-tag"\>Locutor\</span\>  
                    \<span class="locution"\>"Menos tiempo en trámites, más tiempo para ti. ¡Haz tu consulta hoy mismo desde Teams o la Intranet y vive la experiencia del autoservicio inteligente\!"\</span\>  
                    \<span class="sfx-tag"\>\[SFX: Cierre musical en crescendo con acorde positivo y limpio\].\</span\>  
                \</td\>  
            \</tr\>  
        \</tbody\>  
    \</table\>

    \<\!-- Production & Technical Directives \--\>  
    \<div class="section-header"\>  
        \<h2 class="section-title"\>3. Directrices Técnicas de Postproducción y Arte\</h2\>  
    \</div\>

    \<table class="notes-table"\>  
        \<tr\>  
            \<td\>  
                \<span class="notes-title"\>Recomendaciones de Producción Audiovisual:\</span\>  
                \<ul\>  
                    \<li\>\<strong\>Línea Gráfica:\</strong\> Uso estricto de la paleta institucional de la entidad financiera, combinada con tonos azul violeta/cyan para denotar Inteligencia Artificial e innovación.\</li\>  
                    \<li\>\<strong\>Música de Fondo:\</strong\> Pista instrumental de género \<em\>Corporate Tech / Uplifting\</em\>, con nivel regulado (-18dB bajo la voz del locutor) para asegurar inteligibilidad.\</li\>  
                    \<li\>\<strong\>Locución:\</strong\> Voz de tono corporativo pero cercano, fresco y profesional (ritmo moderado de 130-140 palabras por minuto).\</li\>  
                    \<li\>\<strong\>Accesibilidad:\</strong\> Incluir subtítulos maquetados en la parte inferior (Closed Captions corporativos) alineados con la identidad visual.\</li\>  
                \</ul\>  
            \</td\>  
        \</tr\>  
    \</table\>

\</body\>  
\</html\>  
"""

with open("guion\_campana\_agente\_ia.html", "w", encoding="utf-8") as f:  
    f.write(html\_content)

HTML("guion\_campana\_agente\_ia.html").write\_pdf("guion\_campana\_agente\_ia.pdf")  
print("PDF generado con éxito.")

Salida de código

PDF generado con éxito.

Your PDF file is ready

![Icono de PDF][image1]

guion\_campana\_agente\_ia  
PDF

Abierto

# **Guión Técnico Audiovisual: Campaña de Lanzamiento "Agente de IA para Beneficios y Servicios de RRHH"**

Como **Experto en Producción Audiovisual**, se ha estructurado una propuesta de campaña en formato de **Video Animado / Motion Graphics 2D de 60 segundos**, optimizado para difusión en pantallas corporativas, Teams, correo masivo e Intranet de la entidad financiera.  
El guión utiliza la estructura de **dos columnas (Visual / Audio)** habitual en la industria audiovisual, traduciendo los conceptos técnicos de la arquitectura del proceso (RAG, SSO, enmascaramiento PII, vías A, B y C) en explicaciones dinámicas y visuales para el personal.

## **📄 Ficha Técnica de Producción**

* **Título de la Campaña:** *"Tu RRHH al Instante: Inteligencia Artificial a tu Servicio"*

* **Formato:** Video Animado 2D / Infografía Dinámica en Motion Graphics.  
* **Duración:** 60 segundos (ritmo ágil de 130-140 palabras/minuto).  
* **Audiencia Target:** Colaboradores de la entidad financiera (empleados fijos, contratados y directivos).  
* **Tono / Estilo:** Moderno, cercano, transparente, institucional e innovador.  
* **Paleta de Color Recomendada:** Colores corporativos del banco combinados con acentos en tonos *cyan/azul eléctrico* para representar la tecnología de IA.

## **🎬 Guión Audiovisual (Dos Columnas)**

| Escena / Tiempo | Visual / Dirección de Arte (Motion Graphics & UI) | Audio / Locución & Efectos Sonoros (SFX) |
| :---- | :---- | :---- |
| **Escena 1** *(00:00 \- 00:08)* | **Plano Medio (Animación):** Un colaborador frente a su laptop mira su reloj con preocupación. A su alrededor flotan globos de duda con preguntas: *"¿Cómo solicito una carta de trabajo?"*, *"¿Cómo pido el reembolso de odontología?"*. La escena pasa de tonos grises a un fondo azul brillante e iluminado. | **Locutor (Voz cálida y dinámica):** *"¿Necesitas una carta de trabajo urgente o consultar la cobertura de tu seguro y no quieres esperar trámites largos?" (SFX: Música de fondo tech/upbeat \+ sonido suave de reloj tic-tac que se transforma en un destello digital)* |
| **Escena 2** *(00:08 \- 00:18)* | **Plano General:** Aparece en el centro el **Agente de IA**. Desde él se desprenden tres conexiones hacia logos icónicos: **Microsoft Teams**, **WhatsApp Corporativo** y la **Intranet**. Se anima un candado de seguridad con las siglas **SSO**. | **Locutor:** "¡Conoce a tu nuevo Agente de Asistencia Contractual y Beneficios con Inteligencia Artificial\! Disponible 24/7 en Teams, WhatsApp e Intranet, ingresando fácil y seguro con tus mismas credenciales." *(SFX: Pop de notificación \+ click de conexión exitosa)* |
| **Escena 3** *(00:18 \- 00:32)* | **Primer Plano / UI Chat Demo:** Animación del chat. El usuario escribe en lenguaje natural: *"¿Cómo pido el reembolso de odontología?"*. Se despliegan tres caminos visuales: • **Ruta A (Info):** Resalta una cláusula de política en pantalla. • **Ruta B (Trámite):** Se genera y descarga en vivo un PDF con la constancia/vacaciones. • **Ruta C (Casos Especiales):** Se crea una tarjeta de ticket directo hacia RRHH. | **Locutor:** "Solo escribe lo que necesitas como si hablaras con un compañero. La IA analiza tu perfil y te responde al instante: consulta las políticas vigentes, genera directamente tus constancias y vacaciones en PDF, o deriva casos complejos creando un ticket prioritario para el equipo humano de RRHH." *(SFX: Tecleo fluido \+ 'whoosh' al aparecer las 3 vías \+ sonido de descarga de documento)* |
| **Escena 4** *(00:32 \- 00:48)* | **Infografía En Movimiento:** Animación de un escudo protector digital que cubre datos delicados como la cédula y el sueldo (**Enmascaramiento PII**). Al lado, un gráfico verifica de forma transparente los meses de antigüedad necesarios para créditos corporativos. | **Locutor:** "Todo esto con total confidencialidad. Tu información personal y salarial está protegida bajo los más altos estándares de seguridad bancaria, validando de forma transparente tus requisitos según tu tipo de contrato y antigüedad." *(SFX: Escudo de seguridad activándose \+ tono de confirmación/check positivo)* |
| **Escena 5** *(00:48 \- 01:00)* | **Plano Final / Cierre:** El colaborador sonríe sosteniendo su teléfono con el trámite resuelto. Transición a la pantalla de cierre con los iconos de acceso (Teams, WhatsApp, Intranet), la marca institucional y el slogan de la campaña. | **Locutor:** *"Menos tiempo en trámites, más tiempo para ti. ¡Haz tu consulta hoy mismo desde Teams o la Intranet y vive el autoservicio inteligente\!" (SFX: Acorde musical final en crescendo positivo)* |

## **🎧 Indicaciones de Postproducción y Producción Sonora**

> 1. **Locución:** Seleccionar una voz de locutor/a corporativa, cercana y fresca (evitar tonos monótonos o excesivamente solemnes).  
> 2. **Banda Sonora:** Pista instrumental estilo *Corporate Tech / Ambient Bright* (mezclada a \-18dB respecto a la voz para asegurar perfecta nitidez).  
> 3. **Pacing y Edición:** Transiciones fluidas entre pantallas. El uso de tipografías cinéticas en pantalla (texto resaltado para palabras clave como *"24/7"*, *"PDF Inmediato"*, *"100% Seguro"*) aumentará la retención visual.  
> 4. **Accesibilidad:** Se recomienda incluir subtítulos estilizados en la parte inferior de la pantalla para reproducción sin sonido en estaciones de trabajo.

*(El documento PDF generado incluye el diseño maquetado listo para la etapa de preproducción y rodaje/animación).*

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABaklEQVR4Xu2XO0/DMBSF/Z+g/QE1M2TuxATMFayVOoIEWxc2Fpg6MTGxMCKVFYmVlj6gbcJLQAk+ETdyrkNxCnIXH+lITu6N/cXXtmQhlHqyHPRlqa0cO/GKGqtSWsfYAg0jwZF7cikQA7ns7s+ZB2omBH/p2h7AA3gAA+BhoxqHe42MR7WtTM6otvlrzri+Y+SQh9XVnwEejw7jPL3fXMfDtUqS83J2ysOJnlvHaT9vV5c8nCrcbRQHgKLm/kwACLPzbwAYMGoepM+IcQBM6VPrxMghgM8oNEpwb1sC1ArJpDwAPKP+PIcAPrqdTP/cMwGmd53EpHkAIOqHSmgNwEVTVxSAx6wBsPLR0evFeWabFQVAG9YXnxWAvl91G4tQ+4YD/GkN2ABwTerbiwPAe8qZG0A/iunk4x7bHMXfORN1JPPvdRsAru0BPIAHAMDCrmbKbYELYk7Aibt0Q0aj7/KSqi6lt7IcYOwvVnl9HqNTU2QAAAAASUVORK5CYII=>