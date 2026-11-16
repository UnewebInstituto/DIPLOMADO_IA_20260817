# Práctica 3 — Dataset para fine-tuning: redactor de respuestas a preguntas frecuentes de RRHH

Pipeline reproducible (Python 3.10+, solo biblioteca estándar):

```bash
python datos_simulados.py      # 1) material simulado  -> crudo.jsonl (contiene datos personales SINTÉTICOS)
python anonimizar.py           # 2) anonimización      -> anonimizado.jsonl (+ medición de recall)
python validar_y_dividir.py    # 3) validación + 80/10/10 -> train.jsonl, val.jsonl, test.jsonl, split_manifest.csv
```

| Archivo | Contenido |
|---|---|
| `train.jsonl`, `val.jsonl`, `test.jsonl` | **Entregables**: formato chat `{"messages": [system, user, assistant]}` |
| `split_manifest.csv` | A qué conjunto pertenece cada ejemplo, con su tipo y categoría |
| `reporte_validacion.txt` | Resultado de la validación y de la división |
| `crudo.jsonl` | Preguntas ANTES de anonimizar (datos personales ficticios) |

Los scripts son deterministas (semilla fija): ejecutarlos de nuevo reproduce exactamente los mismos archivos.
