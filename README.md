# SpeechForge

## 📦 speechforge@1.0.0-beta.1 — Main Features

- **Flask Backend API**  
  - Text-to-Speech (TTS) endpoint (sync & async, Celery/Redis)
  - File upload & batch processing
  - Catalog management (CRUD, filtering, pagination, CSV export)
  - Async job dashboard & persistent job history
  - S3/Cloud file management (list, download, delete)
  - JWT authentication, rate limiting
  - Admin endpoints: user/tenant management, audit log, audit logging

- **React Frontend**  
  - Login/session management (JWT)
  - TTS request form with advanced options
  - File upload & batch processing UI
  - Async job dashboard with polling & results
  - Catalog table (Material-UI): filtering, batch actions, CSV export, advanced search
  - Custom audio player with waveform visualization
  - Toast notifications for all actions
  - Persistent async job history table
  - S3 browser: browse, download, delete S3 files
  - **Admin Panel UI**: user/tenant management, audit log (admin only)
  - **User Preferences**: language, theme, TTS defaults, notifications
  - **Notifications**: browser notifications for async job completion
  - **i18n**: 15+ languages, language switcher, all UI strings translatable
  - **Accessibility**: ARIA roles/labels, screen reader support
  - **Automated Testing**: Jest, React Testing Library, ESM/JSX support, mocks

---

## 🛣️ Near-term / v1.0 Roadmap

Planned for the stable v1.0 release:

- More granular permissions/roles (RBAC)
- Real-time job status updates (WebSocket)

---

## 🚀 Possible Features for Future Versions

- Webhooks for async job completion (user-defined endpoints)
- OAuth2/social login support
- Multi-factor authentication (MFA)
- User profile management (avatar, email, etc.)
- Advanced catalog analytics and reporting
- S3 file upload and folder management
- Audio editing/cropping tools in frontend
- Admin dashboard analytics (usage, errors, audit trends)
- Plugin system for custom TTS engines or voices
- Improved mobile/responsive UI
- Integration with external TTS providers (Azure, AWS, Google)
- API rate limit dashboard for users/admins
- CLI tool improvements (batch, scripting, etc.)
- More languages and right-to-left (RTL) support

---

## 🤝 Contributing & Issue Reporting

**Found a bug? Have a feature request? Want to contribute?**

1. **Open an Issue:**  
   - Go to the [GitHub repository](https://github.com/EAasen/SpeechForge)
   - Click on the “Issues” tab
   - Click “New Issue” and fill out the template (bug, feature, question, etc.)

2. **Contribute Code:**  
   - Fork the repository
   - Create a new branch (`feature/your-feature` or `fix/your-bug`)
   - Make your changes and add tests if possible
   - Open a Pull Request (PR) to the `main` branch with a clear description

3. **Backlog & Roadmap:**  
   - All open issues and feature requests are tracked in the GitHub Issues tab
   - You can comment, upvote, or discuss features in the issues
   - Maintainers will triage and label issues for future releases

4. **Code of Conduct:**  
   - Please be respectful and follow the [Contributor Covenant](https://www.contributor-covenant.org/)

**Docs, install, and usage instructions are in the `README.md`.  
For questions, open an issue or start a discussion!**

---

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

## 🛠️ Installation & Local Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) ≥ v2
- [Node.js](https://nodejs.org/) ≥ 18 and npm ≥ 9 (frontend only)
- [Python](https://www.python.org/downloads/) ≥ 3.11 (backend local-only mode)
- ~5–10 GB free disk space (the Dia-1.6B model is downloaded on first run)

---

### Option A — Docker (Recommended)

This is the easiest way to run the full stack (backend + Redis) with no manual dependency management.

Copy `.env.example` to `.env` and edit as needed.

```bash
git clone https://github.com/EAasen/SpeechForge.git
cd SpeechForge
cp .env.example .env
docker-compose up --build
```

The Flask API will be available at **http://localhost:8000**.

To enable async TTS jobs, start the Celery worker in a second terminal:

```bash
docker-compose exec diaspeak celery -A src.app.celery_app worker --loglevel=info
```

Or use the helper script which does both:

```bash
bash diaspeak-async.sh
```

**Environment variables (optional):**

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET` | `changeme` | Secret used to sign JWT tokens. **Change in production.** |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Celery broker URL (auto-set by docker-compose) |
| `CELERY_RESULT_BACKEND` | same as broker | Celery result backend URL |
| `TTS_BACKEND` | `dia` | Set to `dummy` to skip model download (useful for testing), or `google` to use Google Cloud Text-to-Speech (see [Using Google Cloud Text-to-Speech](#-using-google-cloud-text-to-speech) below) |

Set them in a `.env` file next to `docker-compose.yml`, for example:

```env
JWT_SECRET=my-very-secret-key
```

---

### Option B — Local Python (Backend only)

Use this if you want to run the Flask app directly without Docker.

**1. Install system dependencies**

```bash
# macOS
brew install ffmpeg redis

# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y ffmpeg redis-server
```

**2. Install Python packages**

```bash
pip install -r requirements.txt
```

**3. Start Redis**

```bash
redis-server &
```

**4. Start the Flask API**

```bash
JWT_SECRET=changeme python src/app.py
```

The API will be available at **http://localhost:8000**.

**5. Start the Celery worker** (needed for `/speak-async`)

```bash
celery -A src.app.celery_app worker --loglevel=info
```

---

### Option C — Frontend (React dev server)

The React frontend talks to the Flask API. Run it alongside Option A or B.

```bash
npm install
npm start
```

The dev server will open at **http://localhost:3000** and proxy API calls to **http://localhost:8000**.

> ℹ️ The `REACT_APP_API_URL` environment variable controls the API base URL (default: `http://localhost:8000`).

---

### Default Credentials

The demo ships with two hardcoded users for **local development only**. Use these to log in via the UI or `/login` endpoint:

| Username | Password | Tenant |
|---|---|---|
| `alice` | `password123` | `org1` |
| `bob` | `password456` | `org2` |

> 🚨 **Security warning:** These credentials and the default `JWT_SECRET` are hardcoded in source code and publicly known. **Never expose this application on a public or shared network without replacing them.** Edit `USERS` in `src/app.py` and set a strong `JWT_SECRET` environment variable before any non-local deployment.

---

## 📦 Quickstart (short version)

```bash
git clone https://github.com/EAasen/SpeechForge.git
cd SpeechForge
docker-compose up --build
# In a second terminal:
docker-compose exec diaspeak celery -A src.app.celery_app worker --loglevel=info
```

---

## 🧵 Async Processing with Celery & Redis

DiaSpeak supports asynchronous TTS job processing using Celery and Redis. This allows you to submit long-running TTS jobs and poll for their status/results without blocking the API.

### Submit Async TTS Jobs

POST to `/speak-async` with your text and parameters:

```bash
curl -X POST http://localhost:8000/speak-async \
  -H 'Content-Type: application/json' \
  -d '{"text": "Your long text here..."}'
```

You will receive a `job_id` in the response.

### Poll Job Status

Check job status and result:

```bash
curl http://localhost:8000/job/<job_id>
```

- Status will be `pending`, `processing`, `complete`, or `error`.

---

## 🧪 Running Tests

The Python test suite uses [pytest](https://pytest.org/). Before running tests, install the dependencies:

```bash
pip install -r requirements.txt
```

**Important:** By default the app loads the Dia-1.6B model (~5–10 GB) on startup. Always run tests with the `dummy` backend to skip the model download:

```bash
TTS_BACKEND=dummy pytest test_app.py
```

A `conftest.py` at the project root automatically sets `TTS_BACKEND=dummy` when you run `pytest` without explicitly setting the variable, so the following also works:

```bash
pytest test_app.py
```

For the React frontend tests:

```bash
npm install
npm test
```

---

## ☁️ Using Google Cloud Text-to-Speech

SpeechForge can generate speech using [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech) instead of the local Dia-1.6B model. This is the first supported external TTS provider, and is useful if you want access to Google's WaveNet/Neural2/Studio voices, additional languages, or don't want to download the ~5–10 GB local model.

### 1. Prerequisites

- A [Google Cloud](https://console.cloud.google.com/) account with billing enabled (Text-to-Speech has a free monthly quota, but a billing account is required to enable the API).
- The [`google-cloud-texttospeech`](https://pypi.org/project/google-cloud-texttospeech/) Python package, which is already listed in `requirements.txt`. Install/update dependencies with:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Enable the Text-to-Speech API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project (or select an existing one).
2. Open **APIs & Services → Library**, search for **"Cloud Text-to-Speech API"**, and click **Enable**.

### 3. Create a service account and credentials

1. In the Cloud Console, go to **IAM & Admin → Service Accounts** and click **Create Service Account**.
2. Give it a name (e.g. `speechforge-tts`) and grant it the **Cloud Text-to-Speech User** role (or `roles/cloudtts.user`). No project-wide Editor/Owner role is needed.
3. Open the new service account, go to the **Keys** tab, click **Add Key → Create new key**, choose **JSON**, and download the key file.
4. Store the downloaded JSON file somewhere safe **outside of version control** (it must never be committed to the repo).

### 4. Configure environment variables

Set the following variables (in your `.env` file or shell environment):

| Variable | Required | Description |
|---|---|---|
| `TTS_BACKEND` | Yes | Set to `google` to route `/speak`, `/speak-async`, and `/speak-file` through Google Cloud TTS. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Absolute path to the service account JSON key file downloaded above. This is the [standard variable](https://cloud.google.com/docs/authentication/application-default-credentials) used by all Google Cloud client libraries. |
| `GOOGLE_TTS_VOICE` | No | Default voice name to use when a request doesn't specify one (default: `en-US-Standard-C`). |
| `GOOGLE_TTS_LANGUAGE_CODE` | No | Default language/locale code (default: derived from the voice name, e.g. `en-US`). |

Example `.env` snippet:

```env
TTS_BACKEND=google
GOOGLE_APPLICATION_CREDENTIALS=/secrets/speechforge-gcp-key.json
GOOGLE_TTS_VOICE=en-US-Neural2-F
GOOGLE_TTS_LANGUAGE_CODE=en-US
```

> 🚨 If running in Docker, mount the credentials file into the container (e.g. `-v /secrets/speechforge-gcp-key.json:/secrets/key.json:ro`) and set `GOOGLE_APPLICATION_CREDENTIALS=/secrets/key.json` accordingly.

### 5. Selecting and using voices

Browse the full, up-to-date list of available voices, languages, and voice types (Standard, WaveNet, Neural2, Studio, etc.) at the [Google Cloud TTS voices page](https://cloud.google.com/text-to-speech/docs/voices). Pass the desired voice per-request using the existing `voice` parameter, e.g.:

```bash
curl -X POST http://localhost:8000/speak \
  -H 'Authorization: ******' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Hello from the cloud!", "voice": "en-US-Neural2-F", "speed": 1.0, "pitch": 0}'
```

- `voice` should match a Google voice name exactly (e.g. `en-GB-Wavenet-A`, `fr-FR-Neural2-B`).
- `speed` maps to Google's `speakingRate` (`0.25`–`4.0`, default `1.0`).
- `pitch` maps to Google's `pitch` (`-20.0`–`20.0` semitones, default `0`).
- If `voice` is omitted, the `GOOGLE_TTS_VOICE` environment variable (or built-in default) is used.

### 6. Limitations and capabilities

- Requires network access and a valid GCP billing account; usage beyond the free tier incurs [Google Cloud charges](https://cloud.google.com/text-to-speech/pricing).
- Higher-quality voice tiers (WaveNet, Neural2, Studio) cost more per character than Standard voices and may have region availability restrictions.
- Google enforces a maximum input length per request (5,000 bytes); SpeechForge's existing text-chunking logic (`max_chars`) already splits long text into smaller requests, so long inputs are still supported.
- Audio is requested as 16-bit linear PCM (`LINEAR16`) and converted the same way as other backends, so `format`/`quality` options in `/speak` still apply after generation.
- Unlike the local Dia backend, no local GPU/model download is required, but each request depends on external API latency and availability.

### 7. End-to-end verification

1. Set `TTS_BACKEND=google` and `GOOGLE_APPLICATION_CREDENTIALS` as described above.
2. Start the API: `python src/app.py` (or `docker-compose up --build` with the variables set in `.env`).
3. Log in and request speech:
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8000/login -H 'Content-Type: application/json' \
     -d '{"username": "alice", "password": "password123"}' | python -c "import sys, json; print(json.load(sys.stdin)['token'])")

   curl -X POST http://localhost:8000/speak \
     -H "Authorization: ******" \
     -H 'Content-Type: application/json' \
     -d '{"text": "Testing Google Cloud text to speech.", "voice": "en-US-Neural2-F"}' \
     --output test.json
   ```
4. Confirm the response contains a `file_path`/download URL and that the referenced file in `outputs/` is a valid, playable audio file.

### 8. Troubleshooting

- **`DefaultCredentialsError` / "Could not automatically determine credentials"**: `GOOGLE_APPLICATION_CREDENTIALS` is unset, points to a missing file, or the file isn't readable by the process/container user. Double-check the path and file permissions.
- **`PermissionDenied` (403)**: The service account is missing the Text-to-Speech role, or the Cloud Text-to-Speech API isn't enabled on the project. Re-check steps 2 and 3 above.
- **`InvalidArgument` mentioning voice/language**: The `voice` name doesn't exist or doesn't match `language_code`. Verify the exact voice name on the [voices page](https://cloud.google.com/text-to-speech/docs/voices).
- **Requests hang or time out**: Check outbound network/firewall access to `texttospeech.googleapis.com`, and confirm billing is enabled on the GCP project (APIs return errors, not silent failures, once billing is set up correctly).
- **Quota exceeded errors**: Check usage/quotas under **APIs & Services → Text-to-Speech API → Quotas** in the Cloud Console.

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
