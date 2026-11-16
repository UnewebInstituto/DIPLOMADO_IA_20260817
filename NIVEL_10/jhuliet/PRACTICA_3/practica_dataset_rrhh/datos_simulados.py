"""Paso 2 — Material simulado: 100 ejemplos normales + 20 casos difíciles.

Todas las respuestas se basan en UN solo documento ficticio, el Reglamento de RRHH (M-RRHH-2026-V4),
para que el dataset no contenga hechos contradictorios. Las preguntas "crudas" llevan datos personales
SINTÉTICOS (nombres, correos, teléfonos, IDs) que luego elimina anonimizar.py.

    python datos_simulados.py      # genera crudo.jsonl
"""
import json, pathlib, random, unicodedata

SISTEMA = ("Eres el asistente de Recursos Humanos de la empresa. Redactas respuestas a preguntas frecuentes de "
           "los colaboradores usando únicamente el Reglamento de RRHH (M-RRHH-2026-V4). Responde en español, de "
           "usted, en texto plano y en máximo 4 oraciones. Cierra con la línea 'Fuente: Reglamento de RRHH, "
           "sección N.' o, si la información no está en el reglamento, con 'Derivación: mesa de ayuda de RRHH.'")

# (categoría, sección, pregunta, cuerpo de la respuesta)  -> se añade la línea "Fuente: ..."
NORMALES = [
    ("vacaciones", "1", "¿Con cuántos días de anticipación debo pedir mis vacaciones?",
     "Debe solicitarlas con un mínimo de 15 días hábiles de anticipación, de manera formal en el Portal del Empleado (Autoservicio > Solicitudes > Licencias). No se procesan solicitudes extemporáneas ni notificadas por canales informales."),
    ("vacaciones", "1", "¿Puedo avisarle a mi jefe por WhatsApp que me voy de vacaciones?",
     "No. Las vacaciones deben solicitarse formalmente en el Portal del Empleado con 15 días hábiles de anticipación; las solicitudes por canales informales no se procesan."),
    ("vacaciones", "1", "¿Cuándo tengo derecho a mis primeras vacaciones?",
     "El derecho a vacaciones anuales remuneradas se adquiere al cumplir un año continuo de servicio. Debe coordinar las fechas con su jefatura directa para garantizar la continuidad operativa del departamento."),
    ("vacaciones", "2", "Llevo 5 años en la empresa, ¿cuántos días de vacaciones me tocan?",
     "Con 4 a 6 años de antigüedad le corresponden 18 días hábiles de vacaciones, con una prima vacacional del 30% sobre el sueldo base."),
    ("vacaciones", "2", "¿Cuántos días de vacaciones tengo con 10 años o más?",
     "Con 10 años o más le corresponden 30 días hábiles de vacaciones, con prima vacacional del 50% sobre el sueldo base. Estas vacaciones no son acumulables y es obligatorio disfrutarlas."),
    ("vacaciones", "2", "Tengo 2 años de antigüedad, ¿qué prima vacacional me corresponde?",
     "De 1 a 3 años de antigüedad la prima vacacional es del 25% sobre el sueldo base, junto con 15 días hábiles de descanso."),
    ("vacaciones", "2", "¿Cuántos periodos de vacaciones puedo acumular con 8 años de servicio?",
     "De 7 a 9 años de antigüedad puede acumular hasta 2 periodos. En ese rango le corresponden 22 días hábiles con una prima del 35% sobre el sueldo base."),
    ("vacaciones", "2", "¿Me pueden pagar las vacaciones en dinero en lugar de tomarlas?",
     "No. Las vacaciones no se pueden compensar en dinero, salvo en caso de terminación definitiva de la relación de trabajo."),
    ("vacaciones", "2", "¿Puedo acumular mis vacaciones si tengo 2 años en la empresa?",
     "Con 1 a 3 años de antigüedad puede acumular hasta 1 periodo de vacaciones."),
    ("vacaciones", "2", "¿Cuántos periodos de vacaciones puedo acumular con 5 años?",
     "De 4 a 6 años de antigüedad puede acumular hasta 2 periodos de vacaciones."),
    ("licencias", "3", "¿Cuántas semanas dura la licencia de maternidad?",
     "La licencia por maternidad es de 12 semanas continuas: 4 antes del parto y 8 después, según la certificación del Seguro Social."),
    ("licencias", "3", "Mi esposa dio a luz, ¿cuántos días de permiso me corresponden?",
     "La licencia por paternidad es de 10 días hábiles continuos, contados desde la fecha de nacimiento o de la resolución legal de adopción. Debe presentar la documentación de respaldo."),
    ("licencias", "3", "Falleció mi papá, ¿cuántos días de duelo me dan?",
     "Lamentamos su pérdida. Por el fallecimiento de familiares de primer grado (padres, cónyuge e hijos) corresponden 5 días hábiles de permiso por duelo."),
    ("licencias", "3", "¿Cuántos días de duelo me dan por un familiar de segundo grado?",
     "Por el fallecimiento de un familiar de segundo grado corresponden 3 días hábiles de permiso por duelo."),
    ("licencias", "3", "Estuve enfermo 4 días seguidos, ¿qué debo entregar?",
     "Para ausencias superiores a 3 días consecutivos debe entregar el certificado de incapacidad validado por el organismo oficial de salud, en un lapso no mayor a 48 horas tras su emisión."),
    ("licencias", "16.1", "¿Cuántos días me dan por casarme?",
     "El permiso por matrimonio o unión legal es de 5 días hábiles remunerados continuos."),
    ("licencias", "16.1", "¿Tengo algún día libre por mi cumpleaños?",
     "Sí. Dispone de un día de permiso retribuido durante el mes de su cumpleaños."),
    ("licencias", "16.1", "Regresé de mi licencia de maternidad, ¿tengo algún horario especial para la lactancia?",
     "Sí. Tiene una reducción de 1 hora diaria de la jornada durante los primeros 6 meses tras su reincorporación."),
    ("licencias", "16.1", "¿Dónde puedo extraerme leche en la oficina?",
     "Todas las sedes corporativas tienen salas de lactancia acondicionadas y equipadas, que puede usar durante la jornada laboral."),
    ("evaluacion", "4", "¿Cada cuánto se evalúa el desempeño?",
     "La evaluación del desempeño es semestral, en junio y diciembre, y considera metas individuales (KPIs) y competencias organizacionales."),
    ("evaluacion", "4", "Saqué 96% en mi evaluación, ¿cuánto bono me toca?",
     "Un puntaje de 95% a 100% es categoría Sobresaliente y da un incentivo de 1.5 salarios mensuales adicionales. Además, queda como candidato a promoción o liderazgo."),
    ("evaluacion", "4", "¿Qué bono recibe quien obtiene 80% en la evaluación?",
     "Un puntaje de 75% a 94% corresponde a Satisfactorio, con un incentivo de 0.75 salarios mensuales adicionales y un plan de mantenimiento de metas."),
    ("evaluacion", "4", "Saqué 65% en la evaluación, ¿qué pasa ahora?",
     "Entre 60% y 74% la categoría es Necesita Mejora: no hay bono económico y se establece un Plan de Mejora de Desempeño (PIP) de 60 días."),
    ("evaluacion", "4", "¿Qué ocurre si obtengo menos de 60% en la evaluación?",
     "Un puntaje menor a 60% es Inaceptable: no hay bono económico y el caso pasa a revisión del Comité Disciplinario."),
    ("disciplina", "5", "¿Qué sanciones hay por faltar reiteradamente a la jornada?",
     "El incumplimiento reiterado acarrea sanciones graduales: amonestación verbal escrita, amonestación formal en el expediente, suspensión no remunerada de 1 a 3 días y, por último, terminación justificada del contrato."),
    ("jornada", "6", "¿Cuántas horas semanales dura la jornada normal?",
     "La jornada ordinaria es de 40 horas semanales, de lunes a viernes, en modalidad presencial, híbrida o remota según la naturaleza del puesto."),
    ("jornada", "6.1", "¿Cómo funciona el trabajo híbrido?",
     "En el esquema híbrido (3x2) usted asiste 3 días a la oficina y trabaja 2 días en remoto, previa autorización."),
    ("jornada", "6.1", "¿Puedo trabajar 100% remoto?",
     "El teletrabajo total es exclusivo de posiciones calificadas que cuenten con un acuerdo contractual específico de teletrabajo."),
    ("jornada", "6.1", "En la modalidad presencial, ¿tengo que ir los 5 días?",
     "Sí. En la modalidad presencial completa la asistencia es obligatoria los 5 días de la semana en las instalaciones de la empresa."),
    ("jornada", "6.2", "Llegué 10 minutos tarde, ¿me descuentan?",
     "No, siempre que no supere la tolerancia de entrada de 15 minutos por día, que se aplica sin descuento salarial hasta 3 veces por mes."),
    ("jornada", "6.2", "Llegué 25 minutos tarde, ¿qué pasa?",
     "Un retardo de 16 a 30 minutos es un retardo menor (hasta 3 eventos por mes) y se descuenta de forma proporcional el tiempo no laborado."),
    ("jornada", "6.2", "¿Qué pasa si llego más de 30 minutos tarde?",
     "Un retardo mayor a 30 minutos no tiene tolerancia y requiere autorización de la jefatura para ingresar."),
    ("jornada", "6.2", "¿Cómo registro mi asistencia?",
     "El registro es individual, mediante el biométrico o la aplicación móvil institucional. Registrar la asistencia de un compañero constituye una falta grave."),
    ("jornada", "6.2", "¿Qué pasa si falto un día sin justificar?",
     "La falta injustificada no tiene eventos permitidos: se descuenta el día y se levanta un acta administrativa."),
    ("conducta", "7.1", "¿Cómo puedo denunciar acoso de forma anónima?",
     "Puede usar la Línea Ética telefónica 0800-ETHICS-2026 (anónima, confidencial y 24/7), el correo codigo.etica@empresa.com o el portal web antifraude. Quien denuncia de buena fe está protegido contra represalias."),
    ("conducta", "7.1", "¿Cuánto tarda una investigación por denuncia ética?",
     "El Comité de Ética y Cumplimiento concluye las investigaciones en un plazo máximo de 20 días hábiles."),
    ("conducta", "7.1", "Si presento una denuncia, ¿pueden despedirme por eso?",
     "No. Quien presenta una denuncia de buena fe, o participa como testigo, está protegido contra cualquier represalia laboral, cambio desfavorable de condiciones o despido."),
    ("conducta", "7", "¿La empresa tiene una política contra la discriminación?",
     "Sí. La organización promueve un ambiente de trabajo inclusivo y respetuoso, libre de discriminación, acoso laboral o acoso sexual. Los canales de denuncia están en la sección 7.1."),
    ("capacitacion", "8.1", "¿Qué capacitaciones son obligatorias?",
     "Las obligatorias son los cursos anuales de Ciberseguridad, Protección de Datos y Código de Ética."),
    ("capacitacion", "8.1", "¿Qué tipos de capacitación ofrece la empresa?",
     "Hay tres programas: capacitación obligatoria institucional, capacitación técnica especializada (cursos, certificaciones y talleres vinculados a su puesto) y becas universitarias."),
    ("capacitacion", "8.1", "¿La empresa paga estudios de maestría?",
     "El programa de becas universitarias ofrece apoyo económico para posgrados y maestrías, de hasta el 70% de la colegiatura."),
    ("capacitacion", "8.2", "¿Qué requisitos necesito para la beca?",
     "Necesita 2 años ininterrumpidos en la empresa, calificación Sobresaliente o Satisfactorio Alto en las últimas 2 evaluaciones anuales, promedio académico mínimo de 8.5/10 y firmar un convenio de permanencia de 2 años."),
    ("capacitacion", "8.2", "Si dejo la carrera a medias, ¿tengo que devolver la beca?",
     "Sí. El incumplimiento injustificado de los estudios, o la baja voluntaria antes del plazo pactado, requiere la devolución del beneficio otorgado."),
    ("capacitacion", "8.2", "Tengo 1 año y medio en la empresa, ¿puedo pedir la beca?",
     "Todavía no: se exige una antigüedad mínima de 2 años ininterrumpidos en la empresa."),
    ("capacitacion", "8.2", "¿Qué promedio académico me piden para la beca?",
     "Se exige un promedio mínimo de 8.5/10 o equivalente, que se acredita con el kardex oficial de la institución."),
    ("capacitacion", "8.2", "¿Tengo que quedarme en la empresa después de terminar la beca?",
     "Sí. El compromiso de permanencia es de 2 años posteriores a la finalización de los estudios, formalizado en un convenio de becas firmado."),
    ("viaticos", "9.1", "¿Cuánto es el límite diario de alimentación en un viaje nacional?",
     "Es de $60 USD por día en destinos nacionales."),
    ("viaticos", "9.1", "¿Cuánto es el límite de alimentación en un viaje al extranjero?",
     "Es de $120 USD por día en destinos internacionales."),
    ("viaticos", "9.1", "¿Cuánto puedo gastar en hotel en un viaje internacional?",
     "Hasta $220 USD por noche en destinos internacionales, en hotel convenio."),
    ("viaticos", "9.1", "¿Cuánto es el hospedaje por noche en un viaje nacional?",
     "Hasta $110 USD por noche en destinos nacionales, en hotel convenio."),
    ("viaticos", "9.1", "¿Cuánto me reconocen de transporte local en un viaje nacional?",
     "Hasta $35 USD por día en destinos nacionales, para transporte local, taxis o servicios VTC."),
    ("viaticos", "9.1", "¿Cuánto me reconocen de taxis en un viaje internacional?",
     "Hasta $70 USD por día en destinos internacionales."),
    ("viaticos", "9.1", "¿Hay un monto para gastos imprevistos durante un viaje?",
     "Sí: gastos menores o imprevistos de hasta $15 USD por día en viajes nacionales y $30 USD por día en internacionales."),
    ("viaticos", "9.1", "¿En cuánto tiempo debo rendir cuentas de un viaje?",
     "Debe presentar el reembolso o la legalización del anticipo, con facturas electrónicas válidas, en un máximo de 5 días hábiles tras el regreso del viaje."),
    ("viaticos", "9.1", "¿Me reembolsan las bebidas alcohólicas de una cena de trabajo?",
     "No. No se reembolsan consumos de bebidas alcohólicas, entretenimiento personal ni compras no autorizadas expresamente en la orden de viaje."),
    ("salud", "10.1", "¿Cuándo es el examen médico anual?",
     "El examen médico anual es obligatorio y se realiza durante el primer trimestre del año."),
    ("salud", "10.1", "¿Hay examen médico al ingresar a la empresa?",
     "Sí. Se realizan evaluaciones clínicas al momento de la contratación, de acuerdo con el puesto."),
    ("salud", "10.1", "¿A qué hora son las pausas activas?",
     "Son dos rutinas de ejercicios ergonómicos de 10 minutos al día, a las 10:30 y a las 15:30 horas."),
    ("salud", "10.2", "¿Cuánto cubre el seguro médico por evento?",
     "El seguro de gastos médicos mayores cubre hasta $500,000 USD por evento para el titular y hasta $250,000 USD para dependientes directos."),
    ("salud", "10.2", "¿Cuál es el deducible del seguro médico?",
     "Para el titular es de 2 salarios mínimos mensuales y para dependientes directos de 3 salarios mínimos mensuales."),
    ("salud", "10.2", "¿Cuánto es el coaseguro del seguro médico?",
     "Es del 10% para el titular, con tope de $2,000 USD, y del 15% para dependientes directos, con tope de $3,500 USD."),
    ("salud", "10.2", "¿El seguro médico cubre el parto?",
     "Sí. La cobertura de maternidad o parto llega hasta $4,000 USD para el titular y hasta $3,000 USD para dependientes directos."),
    ("salud", "10.2", "¿Qué cobertura tiene el seguro para mis hijos?",
     "Como dependientes directos cubre hasta $250,000 USD por evento, con deducible de 3 salarios mínimos mensuales y coaseguro del 15% con tope de $3,500 USD."),
    ("salud", "10.2", "Me lastimé en el trabajo, ¿a quién aviso?",
     "Debe reportar el accidente de inmediato al departamento de Salud Ocupacional para recibir atención médica prioritaria."),
    ("movilidad", "11.1", "¿Qué necesito para postularme a una vacante interna?",
     "Debe tener al menos 12 meses continuos en su puesto, una última evaluación Meets o Exceeds y cero sanciones disciplinarias en los últimos 6 meses, y notificar formalmente a su jefatura antes de las entrevistas."),
    ("movilidad", "11.1", "No tengo 12 meses en mi puesto, ¿puedo postularme igual?",
     "El estándar exige 12 meses continuos en el puesto actual; solo se puede exceptuar con la aprobación del VP de Área y de RRHH."),
    ("movilidad", "11.1", "Me sancionaron hace 3 meses, ¿puedo postularme a otra vacante?",
     "No. Se exige cero sanciones disciplinarias en los últimos 6 meses, sin excepciones disciplinarias."),
    ("movilidad", "11.1", "Si me cambian de puesto, ¿cuánto tiempo tiene mi jefe para traspasar mis funciones?",
     "Una vez aceptada la oferta de movilidad interna, la jefatura cedente dispone de un máximo improrrogable de 30 días naturales para el traspaso de funciones."),
    ("movilidad", "11", "¿Cuándo se aplica el aumento salarial por una promoción interna?",
     "A partir del primer día de la quincena siguiente a la toma de posesión del cargo."),
    ("vestimenta", "12.1", "¿Puedo ir en jeans a la oficina?",
     "Solo los viernes (Casual Day), con jeans sin roturas y polo. De lunes a jueves rige el Business Casual."),
    ("vestimenta", "12.1", "¿Qué debo usar en reuniones con clientes?",
     "Traje formal o atuendo ejecutivo institucional, según el requerimiento del evento."),
    ("vestimenta", "12.1", "Trabajo en campo, ¿qué debo vestir?",
     "Debe usar el uniforme institucional completo, provisto por la empresa, y el equipo de protección personal (EPP) obligatorio."),
    ("vestimenta", "12.2", "Perdí mi carnet, ¿qué hago?",
     "Repórtelo de inmediato a Servicios Generales; la reposición por pérdida tiene un costo de $10 USD."),
    ("vestimenta", "12.2", "¿Puedo prestarle mi carnet a un compañero?",
     "No. La transferencia del carnet a terceros está totalmente prohibida y constituye una falta grave disciplinaria."),
    ("vestimenta", "12.2", "¿Dónde debo llevar el carnet dentro de la oficina?",
     "De forma visible, en el pecho o el cuello, dentro de las instalaciones. Si no lo porta, Seguridad le dará un aviso verbal."),
    ("vestimenta", "12.2", "¿Puedo perforar el carnet para ponerle un cordón?",
     "No. El carnet contiene un chip de proximidad para el control de accesos y no debe ser perforado ni expuesto a campos magnéticos."),
    ("terminacion", "13.1", "Soy personal operativo y voy a renunciar, ¿con cuánta anticipación aviso?",
     "El nivel operativo o auxiliar debe avisar con 15 días naturales de anticipación y entregar un checklist básico de entrega de archivos."),
    ("terminacion", "13.1", "Soy gerente, ¿cuánto preaviso debo dar al renunciar?",
     "El nivel gerencial, directivo o VP debe avisar con 60 días naturales de anticipación y entregar un plan de sucesión formal con entrega auditada."),
    ("terminacion", "13.1", "¿En cuánto tiempo me pagan la liquidación cuando me voy?",
     "El finiquito se paga en un máximo de 10 días hábiles posteriores a la fecha efectiva de baja. Incluye sueldos pendientes, vacaciones no disfrutadas, prima vacacional y aguinaldo."),
    ("terminacion", "13.1", "¿Qué debo hacer antes de que me paguen el finiquito?",
     "Debe firmar el paz y salvo y devolver formalmente todos los activos corporativos antes del desembolso final."),
    ("reconocimientos", "14.1", "¿Qué premio dan por 5 años de servicio?",
     "Un diploma de honor y una bonificación especial equivalente a 0.5 meses de sueldo."),
    ("reconocimientos", "14.1", "¿Qué premio dan por 10 años de servicio?",
     "Una placa conmemorativa, una bonificación equivalente a 1 mes de sueldo y 3 días libres adicionales."),
    ("reconocimientos", "14.1", "¿Qué premio dan por 15 años de servicio?",
     "Un reloj o joya corporativa, una bonificación de 1.5 meses de sueldo y un viaje para dos personas."),
    ("reconocimientos", "14.1", "¿Qué premio hay por 20 años o más?",
     "Un homenaje institucional anual y una bonificación equivalente a 2 meses de sueldo."),
    ("reconocimientos", "14.2", "¿Qué categorías tiene el Empleado del Trimestre?",
     "Hay tres: Innovación y Eficiencia, Espíritu de Equipo y Liderazgo, y Excelencia en Servicio al Cliente. Cada una otorga $1,000 USD más un beneficio adicional."),
    ("reconocimientos", "14.2", "¿Cuándo se pueden hacer nominaciones al Empleado del Trimestre?",
     "Cualquier colaborador puede enviar nominaciones durante los primeros 5 días de cada trimestre."),
    ("datos", "15", "¿Cómo pido una constancia de trabajo?",
     "Solicítela a través de la mesa de ayuda de RRHH con al menos 3 días hábiles de anticipación."),
    ("datos", "15.1", "Quiero corregir un dato mal registrado en mi expediente, ¿en cuánto tiempo me responden?",
     "Mediante el derecho de Rectificación, RRHH responde en 3 días hábiles."),
    ("datos", "15.1", "¿Puedo ver los datos que RRHH tiene guardados de mí?",
     "Sí, con el derecho de Acceso. RRHH responde la solicitud en 5 días hábiles."),
    ("datos", "15.1", "¿En cuánto tiempo eliminan mis datos si lo solicito?",
     "La solicitud de Cancelación, para eliminar datos no requeridos por ley, se responde en 15 días hábiles."),
    ("datos", "15.1", "¿Puedo oponerme a que usen mis datos para algo que no es laboral?",
     "Sí, mediante el derecho de Oposición. RRHH responde en 5 días hábiles."),
    ("datos", "15", "¿Pueden dar mis datos a un banco que los solicita?",
     "No sin su autorización previa por escrito, salvo que lo requiera una autoridad judicial competente."),
    ("bienestar", "16.2", "¿Hay ayuda para pagar la guardería?",
     "Sí: hasta $150 USD mensuales por hijo menor de 4 años."),
    ("bienestar", "16.2", "¿Cuánto es el bono por escolaridad?",
     "$200 USD por hijo en etapa escolar, en un pago único al inicio del ciclo escolar."),
    ("bienestar", "16.2", "¿La empresa ofrece apoyo psicológico?",
     "Sí. El Programa EAP ofrece asistencia psicológica y legal 100% gratuita, 24/7, extensiva a su núcleo familiar directo."),
    ("bienestar", "16.2", "¿Qué documentos necesito para cobrar el auxilio de guardería?",
     "Debe presentar la documentación oficial que acredite el parentesco, como el acta de nacimiento o la inscripción escolar."),
    ("clima", "17.1", "¿Cuándo es la encuesta de clima laboral?",
     "La Encuesta Anual de Clima (eNPS) se realiza cada octubre; es 100% anónima y la gestiona una consultora externa."),
    ("clima", "17.1", "¿Cada cuánto hacen el pulse check?",
     "Es trimestral: en marzo, junio y septiembre, con 5 preguntas clave de satisfacción operacional."),
    ("clima", "17.1", "¿Qué pasa con los resultados de la encuesta de clima?",
     "Se presentan en sesiones All-Hands, y cada líder de área debe construir un Plan de Acción de Clima en un plazo de 30 días posteriores a la entrega de los informes."),
    ("clima", "17.1", "¿Qué es la entrevista de salida?",
     "Es una entrevista que se realiza al momento del retiro del colaborador para identificar los motivos de rotación."),
    ("clima", "17.1", "¿Cada cuánto se revisan los buzones de sugerencias?",
     "Los buzones físicos y virtuales se revisan mensualmente por la Gerencia de Cultura y Desarrollo."),
    ("control", "18.1", "¿Desde cuándo rige el procedimiento de vacaciones con 15 días de anticipación?",
     "Rige desde la versión 4.1 del reglamento, de publicación oficial el 1 de enero de 2026."),
    ("control", "18.1", "¿Qué cambió en la versión 4.1 del reglamento?",
     "Se homologó con normativas internacionales de protección de datos, se extendieron las licencias de paternidad y se actualizó el procedimiento de vacaciones con 15 días de anticipación."),
]

# (tipo, categoría, pregunta, respuesta COMPLETA incluida la línea de cierre)
DIFICILES = [
    # --- fuera de alcance (8) ---
    ("fuera_alcance", "privacidad", "¿Cuánto gana mi compañero {N}?",
     "No puedo compartir información salarial ni datos de otros colaboradores, porque es confidencial.\nDerivación: mesa de ayuda de RRHH."),
    ("fuera_alcance", "conducta", "Mi jefe me gritó delante de todos, ¿lo van a despedir?",
     "No puedo opinar sobre casos individuales ni decidir sanciones. Si considera que hubo acoso o maltrato, puede denunciarlo de forma anónima en la Línea Ética 0800-ETHICS-2026, disponible 24/7.\nDerivación: Línea Ética 0800-ETHICS-2026."),
    ("fuera_alcance", "salud", "Tengo gripe fuerte, ¿qué medicamento me recomiendan? Voy a pedir reposo.",
     "No puedo dar recomendaciones médicas; consulte a un profesional de la salud. Si su ausencia supera 3 días consecutivos, entregue el certificado de incapacidad validado por el organismo oficial de salud en un máximo de 48 horas tras su emisión.\nFuente: Reglamento de RRHH, sección 3."),
    ("fuera_alcance", "legal", "¿Me conviene demandar a la empresa por mi despido?",
     "No puedo dar asesoría legal ni evaluar casos individuales.\nDerivación: mesa de ayuda de RRHH."),
    ("fuera_alcance", "nomina", "¿Qué día de este mes me pagan la nómina?",
     "El reglamento no indica las fechas de pago de la nómina, por lo que no puedo confirmarlas.\nDerivación: mesa de ayuda de RRHH."),
    ("fuera_alcance", "sedes", "¿Cuántas vacaciones tiene el personal de la sede de Madrid?",
     "El reglamento disponible no incluye condiciones particulares de otras sedes, por lo que no puedo confirmarlas.\nDerivación: mesa de ayuda de RRHH."),
    ("fuera_alcance", "privacidad", "¿Cómo quedó mi evaluación comparada con la de mis compañeros?",
     "No tengo acceso a resultados individuales de evaluación ni puedo compararlos con los de otros colaboradores.\nDerivación: mesa de ayuda de RRHH."),
    ("fuera_alcance", "corporativo", "¿Es verdad que habrá despidos masivos el próximo mes?",
     "No cuento con información sobre decisiones corporativas ni puedo confirmar rumores. El reglamento solo regula los procesos de terminación de la relación laboral.\nDerivación: mesa de ayuda de RRHH."),
    # --- ambiguas (6) ---
    ("ambigua", "permisos", "¿Cuántos días me tocan?",
     "Depende del tipo de permiso: por ejemplo, vacaciones de 15 a 30 días hábiles según la antigüedad, paternidad de 10 días hábiles o duelo de 5 o 3 días. ¿A cuál se refiere? Con ese dato le indico la cifra exacta.\nFuente: Reglamento de RRHH, secciones 2 y 3."),
    ("ambigua", "bonos", "¿Cuánto es el bono?",
     "Existen varios: el de desempeño (1.5 o 0.75 salarios mensuales según la evaluación), el de escolaridad ($200 USD por hijo) y los premios por antigüedad. ¿Cuál necesita consultar?\nFuente: Reglamento de RRHH, secciones 4, 14 y 16."),
    ("ambigua", "plazos", "¿Hasta cuándo tengo plazo?",
     "Depende del trámite: por ejemplo, rendir cuentas de un viaje (5 días hábiles tras el regreso), entregar un certificado de incapacidad (48 horas) o pedir vacaciones (15 días hábiles de anticipación). ¿De cuál se trata?\nFuente: Reglamento de RRHH, secciones 1, 3 y 9."),
    ("ambigua", "terminacion", "Quiero renunciar, ¿con cuánto aviso?",
     "Depende de su nivel: 15 días naturales para personal operativo, 30 para profesional, analista o especialista, y 60 para gerencial, directivo o VP.\nFuente: Reglamento de RRHH, sección 13.1."),
    ("ambigua", "viaticos", "¿Me pagan el viaje?",
     "Los viajes de negocios autorizados cuentan con viáticos diarios con límites máximos, que varían según el destino sea nacional o internacional. ¿Cuál es su caso?\nFuente: Reglamento de RRHH, sección 9.1."),
    ("ambigua", "permisos", "¿Cuántos días me dan por un familiar?",
     "Si se refiere a un fallecimiento: 5 días hábiles para familiares de primer grado (padres, cónyuge, hijos) y 3 días hábiles para segundo grado. Si es otro motivo, indíquelo para orientarle mejor.\nFuente: Reglamento de RRHH, sección 3."),
    # --- mal escritas (6) ---
    ("mal_escrita", "vacaciones", "q dias de bacaciones me tokan xq llevo 8 años",
     "Con 7 a 9 años de antigüedad le corresponden 22 días hábiles de vacaciones, con una prima vacacional del 35% sobre el sueldo base.\nFuente: Reglamento de RRHH, sección 2."),
    ("mal_escrita", "permisos", "mi jefe no m deja salir antes d la hora x una cita medica, puede???",
     "El reglamento contempla permisos para situaciones personales justificadas con documentación de respaldo, pero no detalla el caso de citas médicas puntuales. Le conviene consultarlo con la mesa de ayuda de RRHH.\nDerivación: mesa de ayuda de RRHH."),
    ("mal_escrita", "constancias", "ola komo pido constansia d trabajo urgente!!!",
     "Solicítela a través de la mesa de ayuda de RRHH con al menos 3 días hábiles de anticipación. El reglamento no contempla un trámite de urgencia.\nFuente: Reglamento de RRHH, sección 15."),
    ("mal_escrita", "viaticos", "CUANTO PAGAN DE HOTEL EN VIAJES???",
     "El límite es de $110 USD por noche en destinos nacionales y de $220 USD por noche en internacionales, en hotel convenio.\nFuente: Reglamento de RRHH, sección 9.1."),
    ("mal_escrita", "permisos", "kiero saver si m dan el dia libre x mi cumple y si tiene q ser el mismo dia",
     "Sí, tiene un día de permiso retribuido durante el mes de su cumpleaños. El reglamento no precisa si debe coincidir con el día exacto; para definir la fecha consulte a la mesa de ayuda de RRHH.\nFuente: Reglamento de RRHH, sección 16.1."),
    ("mal_escrita", "terminacion", "hola buenas tardes disculpe la molestia sera q me pueden decir cuanto tiempo tienen pa pagarme mi liquidacion xfa",
     "El finiquito se paga en un máximo de 10 días hábiles posteriores a la fecha efectiva de baja.\nFuente: Reglamento de RRHH, sección 13.1."),
]

# ---------------- datos personales SINTÉTICOS ----------------
NOMBRES = [("Marcela", "Quintero"), ("Daniela", "Rojas"), ("Luis", "Fernández"), ("Carlos", "Paredes"),
           ("Ana", "Beltrán"), ("Jorge", "Zambrano"), ("Patricia", "Gómez"), ("Roberto", "Díaz"),
           ("Pedro", "Navarro"), ("Camila", "Reyes"), ("Sofía", "Linares"), ("Andrés", "Molina"),
           ("Karen", "Villalobos"), ("Xiomara", "Betancourt"), ("Gerardo", "Villasmil"), ("Yuleidy", "Carrasquel"),
           ("Osmar", "Pacheco"), ("Ismael", "Quiroz"), ("Nerea", "Colmenares"), ("Wilmer", "Rondón")]
RELACIONES = ["jefe", "jefa", "supervisor", "supervisora", "compañero", "compañera"]
PLANTILLAS = [
    ("Hola, soy {n} ({c}). {q}", "n c"), ("{q} Gracias, {n}.", "n"),
    ("Buenas, habla {n}, ext. {e}. {q}", "n e"), ("Me llamo {n} y mi teléfono es {t}. {q}", "n t"),
    ("{q} Atentamente, {n}, {t}", "n t"), ("Mi {rel} {n} me pidió que preguntara: {q}", "n"),
    ("{q} (mi ID es {id}, cédula {doc})", "id doc"), ("Soy {n}, {id}. {q}", "n id"),
    ("Saludos, {n}. {q} Escríbanme a {c}", "n c"),
]


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def _datos_falsos(rng):
    nom, ape = rng.choice(NOMBRES)
    return {
        "n": f"{nom} {ape}", "nombre": nom, "apellido": ape,
        "c": f"{_sin_tildes(nom).lower()}.{_sin_tildes(ape).lower()}@ejemplo.com",
        "t": rng.choice([f"0414-{rng.randint(1000000, 9999999)}", f"+58 412-{rng.randint(1000000, 9999999)}",
                         f"(0212) {rng.randint(100, 999)} {rng.randint(10, 99)} {rng.randint(10, 99)}",
                         f"{rng.randint(200, 999)}-{rng.randint(1000, 9999)}"]),
        "e": str(rng.randint(1000, 9999)), "id": f"EMP-{rng.randint(10000, 99999)}",
        "doc": f"V-{rng.randint(10, 29)}.{rng.randint(100, 999)}.{rng.randint(100, 999)}",
        "rel": rng.choice(RELACIONES),
    }


def _inyectar(q, rng):
    """Devuelve (pregunta_cruda, [(tipo, texto_inyectado)])."""
    plantilla, usa = rng.choice(PLANTILLAS)
    d = _datos_falsos(rng)
    crudo = plantilla.format(q=q, **d)
    etiquetas = {"n": "NOMBRE", "c": "CORREO", "t": "TELÉFONO", "e": "TELÉFONO", "id": "ID_EMPLEADO", "doc": "DOCUMENTO"}
    inyectados = [(etiquetas[k], d[k]) for k in usa.split()]
    return crudo, inyectados


def construir():
    rng = random.Random(2026)
    ejemplos = []
    for i, (cat, sec, q, a) in enumerate(NORMALES):
        ejemplos.append({"tipo": "normal", "categoria": cat, "q": q, "respuesta":
                         f"{a}\nFuente: Reglamento de RRHH, sección {sec}."})
    for tipo, cat, q, a in DIFICILES:
        ejemplos.append({"tipo": tipo, "categoria": cat, "q": q, "respuesta": a})
    salida = []
    for i, e in enumerate(ejemplos, start=1):
        q = e["q"]
        if "{N}" in q:                                   # el caso de salario ajeno ya trae un nombre
            nom = _datos_falsos(rng)
            q = q.replace("{N}", nom["n"])
            inyect = [("NOMBRE", nom["n"])]
        elif i % 3 == 1 or (e["tipo"] != "normal" and i % 2 == 0):
            q, inyect = _inyectar(q, rng)                # ~40% de las preguntas llevan datos personales
        else:
            inyect = []
        salida.append({"id": f"ej{i:03d}", "tipo": e["tipo"], "categoria": e["categoria"],
                       "pregunta_cruda": q, "respuesta": e["respuesta"], "pii_inyectada": inyect})
    return salida


if __name__ == "__main__":
    datos = construir()
    destino = pathlib.Path(__file__).with_name("crudo.jsonl")
    with open(destino, "w", encoding="utf-8") as f:
        for d in datos:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    n_pii = sum(1 for d in datos if d["pii_inyectada"])
    print(f"{len(datos)} ejemplos ({sum(d['tipo'] == 'normal' for d in datos)} normales + "
          f"{sum(d['tipo'] != 'normal' for d in datos)} difíciles) -> {destino.name}; {n_pii} con datos personales sintéticos")
