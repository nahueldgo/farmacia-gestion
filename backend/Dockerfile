FROM python:3.11-slim

WORKDIR /app

# Instala dependencias primero (aprovecha la cache de Docker si no cambian)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del backend
COPY . .

EXPOSE 8000

# Arranque de producción, sin --reload. La plataforma puede indicar el puerto con la variable PORT.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
