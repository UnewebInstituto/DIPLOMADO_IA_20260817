# NO probado en el entorno de desarrollo del proyecto: revíselo antes de usarlo.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
# Ollama corre en el anfitrión: OLLAMA_HOST=http://host.docker.internal:11434
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
