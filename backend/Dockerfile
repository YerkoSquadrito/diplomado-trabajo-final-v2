FROM python:3.11-slim


# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends\
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install OpenCV dependencies
#when torch is needed, use after 'requirement.txt' : --extra-index-url https://download.pytorch.org/whl/cpu

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 
COPY .env ./.env
COPY . .

EXPOSE 8001

CMD ["python", "fastapi_backend.py"]