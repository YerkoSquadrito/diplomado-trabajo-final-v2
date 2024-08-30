FROM python:3.11-slim

# Install system dependencies

WORKDIR /app

# Install app dependencies
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . .

EXPOSE 8502

CMD ["python", "-m", "dash_frontend", "--host", "0.0.0.0", "--port", "8502"]