# Dockerfile para aplicação Django
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos de requirements e instala dependências
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Expõe a porta configurada
EXPOSE ${PORT}

# Comando para rodar a aplicação
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn setup.wsgi:application --bind 0.0.0.0:${PORT}"]
