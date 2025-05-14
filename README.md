# DiaSpeak

DiaSpeak is a self-hosted Dockerized application that uses the [`nari-labs/Dia-1.6B`](https://huggingface.co/nari-labs/Dia-1.6B) text-to-speech model to generate high-quality speech audio from text inputs. The output is saved as organized audio files into a structured library for easy access and use.

---

## 🚀 Features

✅ Translate any text into natural-sounding speech using Dia-1.6B  
✅ Save output as high-quality `.wav` or `.mp3` files  
✅ Automatically organize files into a user-defined library structure  
✅ REST API endpoint for integration into other applications  
✅ Configurable output formats, voice settings, and file naming schemes  
✅ Run locally via Docker with no external API dependency

---

## 📦 Quickstart

```bash
git clone https://github.com/yourusername/diaspeak.git
cd diaspeak
docker-compose up --build
```

---

## 🧵 Async Processing with Celery & Redis

DiaSpeak supports asynchronous TTS job processing using Celery and Redis. This allows you to submit long-running TTS jobs and poll for their status/results without blocking the API.

### Prerequisites
- Docker Compose (for running Redis and the app)
- Celery and Redis Python packages (already in requirements.txt)

### Setup Steps

1. **Add Redis to Docker Compose**

Your `docker-compose.yml` should include a Redis service:

```yaml
services:
  diaspeak:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./outputs:/app/outputs
    container_name: diaspeak_app
    depends_on:
      - redis

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

2. **Start All Services**

```bash
docker-compose up --build
```

3. **Start the Celery Worker**

In a new terminal, run:

```bash
docker-compose exec diaspeak celery -A src.app.celery_app worker --loglevel=info
```

4. **Submit Async TTS Jobs**

POST to `/speak-async` with your text and parameters:

```bash
curl -X POST http://localhost:8000/speak-async \
  -H 'Content-Type: application/json' \
  -d '{"text": "Your long text here..."}'
```

You will receive a `job_id` in the response.

5. **Poll Job Status**

Check job status and result:

```bash
curl http://localhost:8000/job/<job_id>
```

- Status will be `pending`, `processing`, `complete`, or `error`.

6. **Helper Script**

You can use the provided `diaspeak-async.sh` script to start all services and the Celery worker:

```bash
bash diaspeak-async.sh
```

---

## Troubleshooting: TTS Generation Fails or Audio Output Issues

If you encounter errors such as `TTS generation failed`, missing audio files, or issues with output formats (e.g., MP3/OGG not being produced), follow these steps to resolve common problems:

### 1. Ensure All Dependencies Are Installed
- **Python Packages:**
  - All required packages are listed in `requirements.txt`. Install them with:
    ```bash
    pip install -r requirements.txt
    ```
- **FFmpeg:**
  - `ffmpeg` is required for MP3/OGG export via `pydub`.
  - If running in Docker, the provided `Dockerfile` installs ffmpeg. For local installs:
    ```bash
    sudo apt-get update && sudo apt-get install -y ffmpeg
    ```
  - Verify ffmpeg is available:
    ```bash
    ffmpeg -version
    ```

### 2. File Permissions
- Ensure the `outputs/` directory exists and is writable by the user running the Flask app or Celery worker.
- If running in Docker, the container should have permissions to write to `/outputs`.

### 3. Model Download Issues
- The first run will download the Dia-1.6B model. If you see errors related to model loading, check your internet connection and available disk space.
- If running in a restricted environment, pre-download the model or set the `TRANSFORMERS_CACHE` environment variable to a writable location.

### 4. Redis and Celery (Async Mode)
- For async endpoints (`/speak-async`), ensure Redis is running and accessible at `localhost:6379`.
- Use the provided `diaspeak-async.sh` script or `docker-compose up` to start all services.
- Check logs for errors in the Celery worker or Redis service.

### 5. Common Error Messages
- **`TTS generation failed`**: Check the Flask logs for the full traceback. Common causes:
  - Input text is empty or too large (see chunking settings).
  - Model or dependency issues (see above).
- **`Unsupported format`**: Only `wav`, `mp3`, and `ogg` are supported. Ensure you specify a valid format.
- **`No file part in the request`**: For `/speak-file`, ensure you are sending a file as form-data.

### 6. Debugging Tips
- Run the Flask app in debug mode for more verbose error output:
  ```bash
  FLASK_ENV=development python src/app.py
  ```
- Check the `outputs/catalog.csv` for metadata and file paths of generated audio.
- Use the `/health` endpoint to verify the API is running.

### 7. Still Stuck?
- Open an issue with the error message and relevant logs.
- Include your OS, Python version, and how you are running the app (Docker, local, etc.).

---
