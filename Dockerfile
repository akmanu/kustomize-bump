FROM python:3-alpine
WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "kustomize-bump.py"]

COPY . /app
LABEL maintainer="Simone Esposito <chaufnet@gmail.com>"
