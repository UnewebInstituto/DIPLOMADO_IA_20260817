import pandas as pd

# 1. Cargar el dataset original
df = pd.read_csv("WA_Fn-UseC_-Telco-Customer-Churn.csv")

# 2. Tomar una muestra aleatoria de 150 filas
# La opción random_state asegura reproducibilidad
sample_df = df.sample(n=150, random_state=42)

# 3. Guardar la muestra en un nuevo archivo CSV
sample_df.to_csv("historial_churn.csv", index=False)
