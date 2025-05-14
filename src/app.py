from flask import Flask, request, jsonify, g, send_file, Response, abort
from werkzeug.utils import secure_filename
from transformers import pipeline
import os
from datetime import datetime, timedelta
import soundfile as sf
import numpy as np
import uuid
from urllib.parse import quote
import json
from pydub import AudioSegment
import csv
from typing import List
import re
from celery import Celery
import time
from functools import wraps
from collections import defaultdict
import jwt  # PyJWT is installed as 'jwt'
import mimetypes
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
import zipfile
from io import BytesIO
import threading

# Secret key for JWT (in production, use env var)
JWT_SECRET = 'supersecretkey'
JWT_ALGO = 'HS256'

# In-memory user store (for demo)
USERS = {
    'alice': {'password': 'password123', 'tenant': 'org1'},
    'bob': {'password': 'password456', 'tenant': 'org2'},
}

# In-memory rate limit store: {user: [timestamps]}
RATE_LIMIT = defaultdict(list)
RATE_LIMIT_MAX = 10  # requests
RATE_LIMIT_WINDOW = 60  # seconds

# Helper: JWT auth decorator
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            g.user = payload['user']
            g.tenant = payload.get('tenant')
        except Exception as e:
            return jsonify({'error': 'Invalid token', 'message': str(e)}), 401
        # Rate limiting
        now = time.time()
        timestamps = RATE_LIMIT[g.user]
        # Remove old timestamps
        RATE_LIMIT[g.user] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
        if len(RATE_LIMIT[g.user]) >= RATE_LIMIT_MAX:
            return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429
        RATE_LIMIT[g.user].append(now)
        return f(*args, **kwargs)
    return decorated

# Initialize Flask app
app = Flask(__name__)

# Detect test mode robustly (pytest, unittest, Flask test, or TESTING env)
def is_test_mode():
    import sys
    return (
        os.environ.get('PYTEST_CURRENT_TEST') or
        os.environ.get('TESTING') or
        app.config.get('TESTING') or
        any('pytest' in x or 'unittest' in x for x in sys.modules)
    )

# Model abstraction layer for TTS backends
class BaseTTS:
    def __call__(self, text, **kwargs):
        raise NotImplementedError

class DiaTTS(BaseTTS):
    def __init__(self):
        from transformers import pipeline
        self.pipeline = pipeline("text-to-speech", model="nari-labs/Dia-1.6B")
    def __call__(self, text, **kwargs):
        return self.pipeline(text, **kwargs)

class DummyTTS(BaseTTS):
    def __call__(self, text, **kwargs):
        import numpy as np
        arr = np.zeros(22050, dtype=np.float32)
        return {"audio": arr, "sampling_rate": 22050}

# TTS backend selection
TTS_BACKENDS = {
    'dia': DiaTTS,
    'dummy': DummyTTS,
}

def get_tts_backend():
    if is_test_mode():
        return DummyTTS()
    backend = os.environ.get('TTS_BACKEND', 'dia')
    return TTS_BACKENDS.get(backend, DiaTTS)()

tts_pipeline = get_tts_backend()

# Login endpoint to get JWT
def create_token(user, tenant):
    payload = {'user': user, 'tenant': tenant, 'exp': datetime.utcnow() + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = USERS.get(username)
    if not user or user['password'] != password:
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_token(username, user['tenant'])
    return jsonify({'token': token})

# Celery configuration
celery_app = Celery('diaspeak', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@celery_app.task(bind=True)
def tts_task(self, text, params):
    """
    Background TTS task for async processing.
    """
    # Simulate long processing for demonstration
    time.sleep(1)
    # Here you would call the TTS logic (refactor main logic into a helper for reuse)
    # For now, just return a dummy result
    return {"status": "complete", "message": "TTS job finished", "params": params}

def save_audio_with_format(audio_array, sampling_rate, output_file, fmt, quality=None):
    """
    Save audio in the requested format using soundfile (wav) or pydub (mp3, ogg).
    """
    if fmt == 'wav':
        sf.write(output_file, audio_array, sampling_rate)
    else:
        # Save as wav to temp, then convert
        tmp_wav = output_file + '.tmp.wav'
        sf.write(tmp_wav, audio_array, sampling_rate)
        audio = AudioSegment.from_wav(tmp_wav)
        params = {}
        if quality == 'low':
            params['bitrate'] = '64k'
        elif quality == 'medium':
            params['bitrate'] = '128k'
        elif quality == 'high':
            params['bitrate'] = '192k'
        else:
            params['bitrate'] = '128k'
        audio.export(output_file, format=fmt, **params)
        os.remove(tmp_wav)

def log_metadata(metadata):
    """
    Append metadata to a CSV catalog file.
    In test mode, use a temp file for the catalog.
    """
    if is_test_mode():
        import tempfile
        catalog_path = os.path.join(tempfile.gettempdir(), 'catalog.csv')
    else:
        catalog_path = os.path.join('outputs', 'catalog.csv')
    os.makedirs(os.path.dirname(catalog_path), exist_ok=True)
    file_exists = os.path.isfile(catalog_path)
    with open(catalog_path, 'a', newline='') as csvfile:
        fieldnames = ['title', 'date', 'length', 'tone', 'prompt', 'voice', 'speed', 'pitch', 'format', 'quality', 'file_path', 'user', 'tenant', 's3_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(metadata)

def sanitize_filename(s):
    """Sanitize and normalize a string for safe filenames."""
    s = s.strip().replace(' ', '-')
    s = ''.join(c for c in s if c.isalnum() or c in ('-', '_'))
    return s[:64]  # limit length

def split_text_into_chunks(text: str, max_chars: int = 2000, overlap: int = 100) -> List[str]:
    """
    Split text into chunks of up to max_chars, preferably at sentence boundaries.
    Overlap is the number of characters to repeat at the end of each chunk for continuity.
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current = ''
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current += (' ' if current else '') + sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence
    if current:
        chunks.append(current.strip())
    # Add overlap
    if overlap > 0 and len(chunks) > 1:
        for i in range(1, len(chunks)):
            prev = chunks[i-1]
            chunks[i] = prev[-overlap:] + ' ' + chunks[i]
    return chunks

# Utility: get output dir (test mode uses temp dir)
def get_output_dir():
    if is_test_mode():
        import tempfile
        base = tempfile.gettempdir()
        now = datetime.now()
        return os.path.join(base, "outputs", f"{now.year}", f"{now.month:02}", f"{now.day:02}")
    else:
        now = datetime.now()
        return os.path.join("outputs", f"{now.year}", f"{now.month:02}", f"{now.day:02}")

# Utility: upload file to S3
def upload_to_s3(local_path, s3_bucket, s3_key):
    try:
        s3 = boto3.client('s3')
        s3.upload_file(local_path, s3_bucket, s3_key)
        return f's3://{s3_bucket}/{s3_key}'
    except (BotoCoreError, NoCredentialsError) as e:
        print(f"[S3 UPLOAD ERROR] {e}")
        return None

@app.route('/')
def hello_world():
    return "Hello, World!"

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400

@app.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({"error": "Unprocessable Entity", "message": str(error)}), 422

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

@app.route('/speak', methods=['POST'])
@jwt_required
def speak():
    # Get text input and config params from the request
    data = request.get_json()
    text = data.get('text', '')
    voice = data.get('voice', 'default')  # Placeholder
    speed = data.get('speed', None)
    pitch = data.get('pitch', None)
    format_ = data.get('format', 'wav').lower()
    quality = data.get('quality', 'medium')

    if not text:
        return jsonify({"error": "Text input is required."}), 400

    # Log config params for future extension
    print(f"[TTS CONFIG] voice={voice}, speed={speed}, pitch={pitch}, format={format_}, quality={quality}")

    # Validate format
    supported_formats = {'wav', 'mp3', 'ogg'}
    if format_ not in supported_formats:
        return jsonify({"error": f"Unsupported format '{format_}'. Supported: wav, mp3, ogg."}), 422

    # Validate quality
    supported_qualities = {'low', 'medium', 'high'}
    if quality not in supported_qualities:
        quality = 'medium'

    # Try/except for TTS generation
    try:
        # Chunking logic
        max_chars = 2000  # could be configurable
        overlap = 100
        chunks = split_text_into_chunks(text, max_chars=max_chars, overlap=overlap) if len(text) > max_chars else [text]
        audio_segments = []
        tts_kwargs = {}
        if voice: tts_kwargs['voice'] = voice
        if speed: tts_kwargs['speed'] = speed
        if pitch: tts_kwargs['pitch'] = pitch
        for chunk in chunks:
            # Pass advanced settings if supported by the model
            audio = tts_pipeline(chunk, **tts_kwargs)
            audio_array = audio["audio"] if isinstance(audio, dict) and "audio" in audio else audio
            sampling_rate = audio.get("sampling_rate", 22050) if isinstance(audio, dict) else 22050
            audio_segments.append((audio_array, sampling_rate))
        # Combine audio segments
        if len(audio_segments) == 1:
            audio_array, sampling_rate = audio_segments[0]
        else:
            # Use pydub to concatenate
            combined = AudioSegment.silent(duration=0)
            for arr, sr in audio_segments:
                seg = AudioSegment(
                    arr.tobytes(),
                    frame_rate=sr,
                    sample_width=arr.dtype.itemsize,
                    channels=1 if len(arr.shape) == 1 else arr.shape[1]
                )
                combined += seg
            audio_array = np.array(combined.get_array_of_samples())
            sampling_rate = combined.frame_rate
    except Exception as e:
        return jsonify({"error": "TTS generation failed", "message": str(e)}), 500

    # Create output directory structure
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename: {timestamp}-{first-5-words-of-text}.{format}
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    words = '-'.join(sanitize_filename(word) for word in text.strip().split()[:5])
    base_filename = f"{timestamp}-{words}.{format_}"
    output_file = os.path.join(output_dir, base_filename)
    counter = 1
    while os.path.exists(output_file):
        base_filename = f"{timestamp}-{words}-{counter}.{format_}"
        output_file = os.path.join(output_dir, base_filename)
        counter += 1

    # Save audio file using helper
    save_audio_with_format(audio_array, sampling_rate, output_file, format_, quality)
    # Calculate duration
    duration_sec = len(audio_array) / sampling_rate if hasattr(audio_array, '__len__') else 0
    duration_str = str(timedelta(seconds=int(duration_sec)))
    # Return file path and accessible URL
    rel_path = os.path.relpath(output_file, start="outputs")
    url = f"http://localhost:8000/outputs/{rel_path.replace(os.sep, '/')}"
    # S3 export if enabled
    s3_url = None
    s3_bucket = os.environ.get('S3_BUCKET')
    s3_prefix = os.environ.get('S3_PREFIX', '')
    if s3_bucket:
        s3_key = os.path.join(s3_prefix, rel_path.replace(os.sep, '/'))
        s3_url = upload_to_s3(output_file, s3_bucket, s3_key)
    # Log metadata
    metadata = {
        'title': None,
        'date': now.strftime('%Y-%m-%d'),
        'length': duration_str,
        'tone': None,
        'prompt': None,
        'voice': voice,
        'speed': speed,
        'pitch': pitch,
        'format': format_,
        'quality': quality,
        'file_path': f"/outputs/{rel_path}",
        'user': getattr(g, 'user', None),
        'tenant': getattr(g, 'tenant', None),
        's3_url': s3_url,
    }
    log_metadata(metadata)

    return jsonify({
        "file_path": f"/outputs/{rel_path}",
        "url": url,
        "format": format_,
        "quality": quality,
        "duration": duration_str,
        "s3_url": s3_url,
    })

# Path for job history
JOB_HISTORY_PATH = os.path.join('outputs', 'job_history.csv')
JOB_HISTORY_LOCK = threading.Lock()

# Helper to log/update job history

def log_job_history(job_id, user, text, status, submitted_at=None, completed_at=None, result_url=None, error=None):
    import csv
    import time
    os.makedirs(os.path.dirname(JOB_HISTORY_PATH), exist_ok=True)
    with JOB_HISTORY_LOCK:
        file_exists = os.path.isfile(JOB_HISTORY_PATH)
        with open(JOB_HISTORY_PATH, 'a', newline='') as csvfile:
            fieldnames = ['job_id', 'user', 'text', 'status', 'submitted_at', 'completed_at', 'result_url', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'job_id': job_id,
                'user': user,
                'text': text,
                'status': status,
                'submitted_at': submitted_at or time.strftime('%Y-%m-%d %H:%M:%S'),
                'completed_at': completed_at or '',
                'result_url': result_url or '',
                'error': error or ''
            })

def update_job_history(job_id, **updates):
    import csv
    with JOB_HISTORY_LOCK:
        if not os.path.isfile(JOB_HISTORY_PATH):
            return
        with open(JOB_HISTORY_PATH, 'r', newline='') as csvfile:
            rows = list(csv.DictReader(csvfile))
            fieldnames = csvfile.fieldnames if hasattr(csvfile, 'fieldnames') else rows[0].keys()
        for row in rows:
            if row['job_id'] == job_id:
                for k, v in updates.items():
                    if k in row:
                        row[k] = v
        with open(JOB_HISTORY_PATH, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List async TTS jobs (history). Supports filtering by user, status, and pagination.
    Query params: user, status, page, page_size
    """
    import csv
    if not os.path.isfile(JOB_HISTORY_PATH):
        return jsonify({'results': [], 'total': 0, 'page': 1, 'page_size': 20})
    with JOB_HISTORY_LOCK:
        with open(JOB_HISTORY_PATH, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            jobs = list(reader)
    user = request.args.get('user')
    status = request.args.get('status')
    if user:
        jobs = [j for j in jobs if j.get('user') == user]
    if status:
        jobs = [j for j in jobs if j.get('status') == status]
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        if page < 1: page = 1
        if page_size < 1: page_size = 20
    except Exception:
        page, page_size = 1, 20
    total = len(jobs)
    start = (page - 1) * page_size
    end = start + page_size
    paged = jobs[start:end]
    return jsonify({'results': paged, 'total': total, 'page': page, 'page_size': page_size})

# Update async job submission and status endpoints to log/update job history
@app.route('/speak-async', methods=['POST'])
@jwt_required
def speak_async():
    data = request.get_json()
    text = data.get('text', '')
    params = {k: v for k, v in data.items() if k != 'text'}
    if not text:
        return jsonify({"error": "Text input is required."}), 400
    # Enqueue background task
    job = tts_task.apply_async(args=[text, params])
    log_job_history(job.id, getattr(g, 'user', None), text, 'queued')
    return jsonify({"job_id": job.id, "status": "queued"})

@app.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = tts_task.AsyncResult(job_id)
    status = None
    result_url = None
    error = None
    if job.state == 'PENDING':
        status = 'pending'
    elif job.state == 'STARTED':
        status = 'processing'
    elif job.state == 'SUCCESS':
        status = 'complete'
        result_url = job.result.get('url') if isinstance(job.result, dict) else None
    elif job.state == 'FAILURE':
        status = 'error'
        error = str(job.info)
    else:
        status = job.state
    update_job_history(job_id, status=status, result_url=result_url or '', error=error or '', completed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status in ['complete','error'] else '')
    if job.state == 'SUCCESS':
        return jsonify({"status": "complete", "result": job.result})
    elif job.state == 'FAILURE':
        return jsonify({"status": "error", "message": str(job.info)})
    elif job.state == 'PENDING':
        return jsonify({"status": "pending"})
    elif job.state == 'STARTED':
        return jsonify({"status": "processing"})
    else:
        return jsonify({"status": job.state})

@app.route('/speak-file', methods=['POST'])
@jwt_required
def speak_file():
    """
    Accepts a file upload (.txt, .md, .json) and optional fields as form-data.
    Extracts text, title, and optional fields for TTS processing.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    # Read file content
    content = file.read().decode('utf-8', errors='ignore')
    # Parse fields
    title = request.form.get('title', None)
    text = None
    # Handle .json, .txt, .md
    if ext == '.json':
        try:
            data = json.loads(content)
            text = data.get('text', '')
            if not title:
                title = data.get('title', None)
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400
    else:
        # .txt or .md: try to extract title and text
        lines = content.splitlines()
        if not title and lines and lines[0].lower().startswith('title:'):
            title = lines[0][6:].trip()
            text = '\n'.join(lines[1:]).strip()
        else:
            text = content.strip()
    # Sanitize and trim
    if title:
        title = ' '.join(title.split())
    if text:
        text = ' '.join(text.split())
    # Accept optional fields
    tone = request.form.get('tone', None)
    prompt = request.form.get('prompt', None)
    voice = request.form.get('voice', 'default')
    speed = request.form.get('speed', None)
    pitch = request.form.get('pitch', None)
    format_ = request.form.get('format', 'wav').lower()
    quality = request.form.get('quality', 'medium')
    # Log config
    print(f"[TTS CONFIG] title={title}, tone={tone}, prompt={prompt}, voice={voice}, speed={speed}, pitch={pitch}, format={format_}, quality={quality}")
    # Validate text
    if not text:
        return jsonify({"error": "Text input is required in the file."}), 400
    # Validate format
    supported_formats = {'wav', 'mp3', 'ogg'}
    if format_ not in supported_formats:
        return jsonify({"error": f"Unsupported format '{format_}'. Supported: wav, mp3, ogg."}), 422
    # Validate quality
    supported_qualities = {'low', 'medium', 'high'}
    if quality not in supported_qualities:
        quality = 'medium'
    # Try/except for TTS generation
    try:
        max_chars = 2000
        overlap = 100
        chunks = split_text_into_chunks(text, max_chars=max_chars, overlap=overlap) if len(text) > max_chars else [text]
        audio_segments = []
        tts_kwargs = {}
        if voice: tts_kwargs['voice'] = voice
        if speed: tts_kwargs['speed'] = speed
        if pitch: tts_kwargs['pitch'] = pitch
        for chunk in chunks:
            audio = tts_pipeline(chunk, **tts_kwargs)
            audio_array = audio["audio"] if isinstance(audio, dict) and "audio" in audio else audio
            sampling_rate = audio.get("sampling_rate", 22050) if isinstance(audio, dict) else 22050
            audio_segments.append((audio_array, sampling_rate))
        if len(audio_segments) == 1:
            audio_array, sampling_rate = audio_segments[0]
        else:
            combined = AudioSegment.silent(duration=0)
            for arr, sr in audio_segments:
                seg = AudioSegment(
                    arr.tobytes(),
                    frame_rate=sr,
                    sample_width=arr.dtype.itemsize,
                    channels=1 if len(arr.shape) == 1 else arr.shape[1]
                )
                combined += seg
            audio_array = np.array(combined.get_array_of_samples())
            sampling_rate = combined.frame_rate
    except Exception as e:
        return jsonify({"error": "TTS generation failed", "message": str(e)}), 500
    # ...existing output file logic (use title if available for filename)...
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    # Use title for filename if available, else fallback to timestamp-words
    now = datetime.now()
    if title:
        safe_title = sanitize_filename(title)
        base_filename = f"{now.strftime('%Y%m%d%H%M%S')}-{safe_title}.{format_}"
    else:
        words = '-'.join(sanitize_filename(word) for word in text.strip().split()[:5])
        base_filename = f"{now.strftime('%Y%m%d%H%M%S')}-{words}.{format_}"
    output_file = os.path.join(output_dir, base_filename)
    counter = 1
    while os.path.exists(output_file):
        if title:
            base_filename = f"{now.strftime('%Y%m%d%H%M%S')}-{safe_title}-{counter}.{format_}"
        else:
            base_filename = f"{now.strftime('%Y%m%d%H%M%S')}-{words}-{counter}.{format_}"
        output_file = os.path.join(output_dir, base_filename)
        counter += 1
    save_audio_with_format(audio_array, sampling_rate, output_file, format_, quality)
    duration_sec = len(audio_array) / sampling_rate if hasattr(audio_array, '__len__') else 0
    duration_str = str(timedelta(seconds=int(duration_sec)))
    rel_path = os.path.relpath(output_file, start="outputs")
    url = f"http://localhost:8000/outputs/{rel_path.replace(os.sep, '/')}"
    # S3 export if enabled
    s3_url = None
    s3_bucket = os.environ.get('S3_BUCKET')
    s3_prefix = os.environ.get('S3_PREFIX', '')
    if s3_bucket:
        s3_key = os.path.join(s3_prefix, rel_path.replace(os.sep, '/'))
        s3_url = upload_to_s3(output_file, s3_bucket, s3_key)
    # Log metadata
    metadata = {
        'title': title,
        'date': now.strftime('%Y-%m-%d'),
        'length': duration_str,
        'tone': tone,
        'prompt': prompt,
        'voice': voice,
        'speed': speed,
        'pitch': pitch,
        'format': format_,
        'quality': quality,
        'file_path': f"/outputs/{rel_path}",
        'user': getattr(g, 'user', None),
        'tenant': getattr(g, 'tenant', None),
        's3_url': s3_url,
    }
    log_metadata(metadata)
    return jsonify({
        "file_path": f"/outputs/{rel_path}",
        "url": url,
        "title": title,
        "tone": tone,
        "prompt": prompt,
        "format": format_,
        "quality": quality,
        "duration": duration_str,
        "s3_url": s3_url,
    })

@app.route('/catalog', methods=['GET'])
def get_catalog():
    """
    Returns the catalog of generated audio files as a list of dicts (JSON) or as a CSV export.
    Supports filtering by user, tenant, date, format, and search by title.
    Query params: user, tenant, date, format, title (substring match), page, page_size, export=csv
    """
    if is_test_mode():
        import tempfile
        catalog_path = os.path.join(tempfile.gettempdir(), 'catalog.csv')
    else:
        catalog_path = os.path.join('outputs', 'catalog.csv')
    if not os.path.isfile(catalog_path):
        if request.args.get('export') == 'csv':
            return Response('', mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename="catalog.csv"'})
        return jsonify({'results': [], 'total': 0, 'page': 1, 'page_size': 20})
    with open(catalog_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        catalog = list(reader)
        fieldnames = reader.fieldnames
    # Filtering
    user = request.args.get('user')
    tenant = request.args.get('tenant')
    date = request.args.get('date')
    fmt = request.args.get('format')
    title = request.args.get('title')
    if user:
        catalog = [row for row in catalog if row.get('user') == user]
    if tenant:
        catalog = [row for row in catalog if row.get('tenant') == tenant]
    if date:
        catalog = [row for row in catalog if row.get('date') == date]
    if fmt:
        catalog = [row for row in catalog if row.get('format') == fmt]
    if title:
        catalog = [row for row in catalog if row.get('title') and title.lower() in row['title'].lower()]
    # Export as CSV if requested
    if request.args.get('export') == 'csv':
        from io import StringIO
        sio = StringIO()
        writer = csv.DictWriter(sio, fieldnames=fieldnames)
        writer.writeheader()
        for row in catalog:
            writer.writerow(row)
        csv_data = sio.getvalue()
        return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename="catalog.csv"'})
    # Pagination
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        if page < 1: page = 1
        if page_size < 1: page_size = 20
    except Exception:
        page, page_size = 1, 20
    total = len(catalog)
    start = (page - 1) * page_size
    end = start + page_size
    paged = catalog[start:end]
    return jsonify({'results': paged, 'total': total, 'page': page, 'page_size': page_size})

@app.route('/catalog/<int:item_id>', methods=['DELETE'])
def delete_catalog_item(item_id):
    """
    Delete a catalog entry and its audio file by index (row number in catalog).
    """
    if is_test_mode():
        import tempfile
        catalog_path = os.path.join(tempfile.gettempdir(), 'catalog.csv')
    else:
        catalog_path = os.path.join('outputs', 'catalog.csv')
    if not os.path.isfile(catalog_path):
        return jsonify({'error': 'Catalog not found'}), 404
    with open(catalog_path, 'r', newline='') as csvfile:
        rows = list(csv.DictReader(csvfile))
    if item_id < 0 or item_id >= len(rows):
        return jsonify({'error': 'Invalid item_id'}), 404
    file_path = rows[item_id].get('file_path')
    # Remove audio file
    if file_path:
        abs_path = os.path.abspath(file_path.lstrip('/'))
        if os.path.isfile(abs_path):
            os.remove(abs_path)
    # Remove row and rewrite catalog
    del rows[item_id]
    with open(catalog_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['title', 'date', 'length', 'tone', 'prompt', 'voice', 'speed', 'pitch', 'format', 'quality', 'file_path', 'user', 'tenant', 's3_url'])
        writer.writeheader()
        writer.writerows(rows)
    return jsonify({'status': 'deleted', 'item_id': item_id})

@app.route('/catalog/<int:item_id>', methods=['PUT'])
def update_catalog_item(item_id):
    """
    Update a catalog entry by index (row number in catalog).
    Accepts JSON body with any updatable fields (title, tone, prompt, voice, speed, pitch, format, quality).
    """
    if is_test_mode():
        import tempfile
        catalog_path = os.path.join(tempfile.gettempdir(), 'catalog.csv')
    else:
        catalog_path = os.path.join('outputs', 'catalog.csv')
    if not os.path.isfile(catalog_path):
        return jsonify({'error': 'Catalog not found'}), 404
    with open(catalog_path, 'r', newline='') as csvfile:
        rows = list(csv.DictReader(csvfile))
        fieldnames = csvfile.fieldnames if hasattr(csvfile, 'fieldnames') else rows[0].keys()
    if item_id < 0 or item_id >= len(rows):
        return jsonify({'error': 'Invalid item_id'}), 404
    data = request.get_json()
    updatable = ['title', 'tone', 'prompt', 'voice', 'speed', 'pitch', 'format', 'quality']
    for field in updatable:
        if field in data:
            rows[item_id][field] = data[field]
    with open(catalog_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return jsonify({'status': 'updated', 'item_id': item_id})

@app.route('/catalog/batch', methods=['POST'])
def catalog_batch():
    """
    Batch actions on catalog: download as zip, export as csv, batch update.
    Expects JSON: { action: 'download'|'export_csv'|'edit', indices: [int], update: {field: value, ...} }
    """
    data = request.get_json()
    action = data.get('action')
    indices = data.get('indices', [])
    update = data.get('update', {})
    if is_test_mode():
        import tempfile
        catalog_path = os.path.join(tempfile.gettempdir(), 'catalog.csv')
    else:
        catalog_path = os.path.join('outputs', 'catalog.csv')
    if not os.path.isfile(catalog_path):
        return jsonify({'error': 'Catalog not found'}), 404
    with open(catalog_path, 'r', newline='') as csvfile:
        rows = list(csv.DictReader(csvfile))
        fieldnames = csvfile.fieldnames if hasattr(csvfile, 'fieldnames') else rows[0].keys()
    selected = [rows[i] for i in indices if 0 <= i < len(rows)]
    if action == 'download':
        # Create zip of audio files
        mem_zip = BytesIO()
        with zipfile.ZipFile(mem_zip, 'w') as zf:
            for row in selected:
                file_path = row.get('file_path')
                if file_path:
                    abs_path = os.path.abspath(file_path.lstrip('/'))
                    if os.path.isfile(abs_path):
                        zf.write(abs_path, arcname=os.path.basename(abs_path))
        mem_zip.seek(0)
        return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='catalog_batch.zip')
    elif action == 'export_csv':
        from io import StringIO
        sio = StringIO()
        writer = csv.DictWriter(sio, fieldnames=fieldnames)
        writer.writeheader()
        for row in selected:
            writer.writerow(row)
        sio.seek(0)
        return Response(sio.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename="catalog_batch.csv"'})
    elif action == 'edit':
        # Batch update fields
        for i in indices:
            if 0 <= i < len(rows):
                for k, v in update.items():
                    if k in rows[i]:
                        rows[i][k] = v
        with open(catalog_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return jsonify({'status': 'updated', 'count': len(indices)})
    else:
        return jsonify({'error': 'Invalid action'}), 400

def safe_output_path(audio_path):
    # Prevent path traversal, only allow files under outputs/
    base = os.path.abspath('outputs')
    full = os.path.abspath(os.path.join('outputs', audio_path))
    if not full.startswith(base):
        abort(403)
    return full

@app.route('/download/<path:audio_path>', methods=['GET'])
def download_audio(audio_path):
    """
    Stream audio file with Range support for preview/download.
    """
    file_path = safe_output_path(audio_path)
    if not os.path.isfile(file_path):
        return jsonify({'error': 'File not found'}), 404
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)
    if not range_header:
        # No Range: send whole file
        mime = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        return send_file(file_path, mimetype=mime, as_attachment=True, download_name=os.path.basename(file_path))
    # Parse Range header
    try:
        match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not match:
            return jsonify({'error': 'Invalid Range header'}), 416
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else file_size - 1
        if start > end or end >= file_size:
            return jsonify({'error': 'Range Not Satisfiable'}), 416
        length = end - start + 1
        with open(file_path, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        resp = Response(data, 206, mimetype=mimetypes.guess_type(file_path)[0] or 'application/octet-stream', direct_passthrough=True)
        resp.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        resp.headers.add('Accept-Ranges', 'bytes')
        resp.headers.add('Content-Length', str(length))
        resp.headers.add('Content-Disposition', f'inline; filename="{os.path.basename(file_path)}"')
        return resp
    except Exception as e:
        return jsonify({'error': 'Failed to stream file', 'message': str(e)}), 500

@app.route('/s3/list', methods=['GET'])
def s3_list():
    """
    List files in the configured S3 bucket/prefix. Query params: prefix, max_keys, start_after
    """
    s3_bucket = os.environ.get('S3_BUCKET')
    s3_prefix = request.args.get('prefix', os.environ.get('S3_PREFIX', ''))
    max_keys = int(request.args.get('max_keys', 100))
    start_after = request.args.get('start_after', '')
    if not s3_bucket:
        return jsonify({'error': 'S3_BUCKET not configured'}), 400
    try:
        s3 = boto3.client('s3')
        kwargs = {'Bucket': s3_bucket, 'Prefix': s3_prefix, 'MaxKeys': max_keys}
        if start_after:
            kwargs['StartAfter'] = start_after
        resp = s3.list_objects_v2(**kwargs)
        files = []
        for obj in resp.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat() if hasattr(obj['LastModified'], 'isoformat') else str(obj['LastModified'])
            })
        return jsonify({'files': files, 'is_truncated': resp.get('IsTruncated', False), 'next_start_after': files[-1]['key'] if files else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/s3/download', methods=['GET'])
def s3_download():
    """
    Download a file from S3. Query param: key
    """
    s3_bucket = os.environ.get('S3_BUCKET')
    key = request.args.get('key')
    if not s3_bucket or not key:
        return jsonify({'error': 'Missing S3_BUCKET or key'}), 400
    try:
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=s3_bucket, Key=key)
        data = obj['Body'].read()
        filename = os.path.basename(key)
        return Response(data, mimetype='application/octet-stream', headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/s3/delete', methods=['POST'])
def s3_delete():
    """
    Delete a file from S3. JSON body: { key: ... }
    """
    s3_bucket = os.environ.get('S3_BUCKET')
    data = request.get_json()
    key = data.get('key')
    if not s3_bucket or not key:
        return jsonify({'error': 'Missing S3_BUCKET or key'}), 400
    try:
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=s3_bucket, Key=key)
        return jsonify({'status': 'deleted', 'key': key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Admin Panel Endpoints ---
from functools import wraps

ADMIN_USERS = {'alice'}  # Set of usernames with admin rights

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user = payload['user']
            if user not in ADMIN_USERS:
                return jsonify({'error': 'Admin access required'}), 403
        except Exception as e:
            return jsonify({'error': 'Invalid token', 'message': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

USERS_PATH = os.path.join('outputs', 'users.json')
AUDIT_LOG_PATH = os.path.join('outputs', 'audit_log.csv')

def load_users():
    if os.path.isfile(USERS_PATH):
        with open(USERS_PATH, 'r') as f:
            return json.load(f)
    return USERS.copy()

def save_users(users):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, 'w') as f:
        json.dump(users, f)

def log_audit(action, user, details=None):
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    import csv, time
    file_exists = os.path.isfile(AUDIT_LOG_PATH)
    with open(AUDIT_LOG_PATH, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'user', 'action', 'details']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user': user,
            'action': action,
            'details': json.dumps(details) if details else ''
        })

@app.route('/admin/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def admin_users():
    users = load_users()
    if request.method == 'GET':
        return jsonify(users)
    data = request.get_json()
    user = data.get('username')
    if request.method == 'POST':
        if user in users:
            return jsonify({'error': 'User already exists'}), 400
        users[user] = {
            'password': data.get('password', ''),
            'tenant': data.get('tenant', '')
        }
        save_users(users)
        log_audit('add_user', g.user, {'username': user})
        return jsonify({'status': 'created', 'user': user})
    elif request.method == 'PUT':
        if user not in users:
            return jsonify({'error': 'User not found'}), 404
        if 'password' in data:
            users[user]['password'] = data['password']
        if 'tenant' in data:
            users[user]['tenant'] = data['tenant']
        save_users(users)
        log_audit('update_user', g.user, {'username': user})
        return jsonify({'status': 'updated', 'user': user})
    elif request.method == 'DELETE':
        if user not in users:
            return jsonify({'error': 'User not found'}), 404
        del users[user]
        save_users(users)
        log_audit('delete_user', g.user, {'username': user})
        return jsonify({'status': 'deleted', 'user': user})

@app.route('/admin/tenants', methods=['GET'])
@admin_required
def admin_tenants():
    users = load_users()
    tenants = sorted(set(u['tenant'] for u in users.values() if u.get('tenant')))
    return jsonify({'tenants': tenants})

@app.route('/admin/audit-log', methods=['GET'])
@admin_required
def admin_audit_log():
    import csv
    if not os.path.isfile(AUDIT_LOG_PATH):
        return jsonify({'log': []})
    with open(AUDIT_LOG_PATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        log = list(reader)
    return jsonify({'log': log})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
