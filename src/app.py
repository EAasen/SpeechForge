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

# Secret key for JWT — set JWT_SECRET env var in production
JWT_SECRET = os.environ.get('JWT_SECRET', 'changeme')
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
os.makedirs('outputs', exist_ok=True)

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

# TTS Provider Capability Registry
TTS_PROVIDER_REGISTRY = {
    "local_dia": {
        "id": "local_dia",
        "name": "Local Dia (On-Device)",
        "type": "local",
        "supports_offline": True,
        "supports_ssml": False,
        "supported_formats": ["wav", "mp3", "ogg"],
        "sample_rates": [22050, 44100],
        "languages": [
            {"code": "en-US", "name": "English (US)"},
            {"code": "es-ES", "name": "Spanish"}
        ],
        "voices": [
            {"id": "dia-default", "name": "Dia Voice 1 (Default)", "gender": "neutral", "styles": []},
            {"id": "dia-female", "name": "Dia Voice 2 (Female)", "gender": "female", "styles": []},
            {"id": "dia-male", "name": "Dia Voice 3 (Male)", "gender": "male", "styles": []}
        ],
        "custom_params": {
            "temperature": {"type": "float", "min": 0.1, "max": 2.0, "default": 0.7},
            "guidance_scale": {"type": "float", "min": 1.0, "max": 10.0, "default": 3.0}
        }
    },
    "dummy": {
        "id": "dummy",
        "name": "Dummy Backend (Testing)",
        "type": "local",
        "supports_offline": True,
        "supports_ssml": False,
        "supported_formats": ["wav", "mp3", "ogg"],
        "sample_rates": [22050],
        "languages": [{"code": "en-US", "name": "English (US)"}],
        "voices": [{"id": "default", "name": "Dummy Default Voice", "gender": "neutral", "styles": []}],
        "custom_params": {}
    },
    "azure": {
        "id": "azure",
        "name": "Azure Cognitive Services Speech",
        "type": "cloud",
        "supports_offline": False,
        "supports_ssml": True,
        "supported_formats": ["wav", "mp3", "ogg", "pcm"],
        "sample_rates": [16000, 24000, 44100, 48000],
        "languages": [
            {"code": "en-US", "name": "English (US)"},
            {"code": "fr-FR", "name": "French"},
            {"code": "de-DE", "name": "German"},
            {"code": "es-ES", "name": "Spanish"}
        ],
        "voices": [
            {"id": "en-US-JennyNeural", "name": "Jenny (Neural)", "gender": "female", "styles": ["cheerful", "sad", "empathetic", "chat", "newscast"]},
            {"id": "en-US-GuyNeural", "name": "Guy (Neural)", "gender": "male", "styles": ["newscast", "angry", "cheerful"]}
        ],
        "custom_params": {
            "style": {"type": "string"},
            "style_degree": {"type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
            "use_ssml": {"type": "boolean", "default": False}
        }
    },
    "aws": {
        "id": "aws",
        "name": "AWS Polly",
        "type": "cloud",
        "supports_offline": False,
        "supports_ssml": True,
        "supported_formats": ["mp3", "ogg", "pcm", "wav"],
        "sample_rates": [8000, 16000, 22050, 24000],
        "languages": [
            {"code": "en-US", "name": "English (US)"},
            {"code": "es-US", "name": "Spanish (US)"}
        ],
        "voices": [
            {"id": "Joanna", "name": "Joanna", "gender": "female", "engines": ["standard", "neural"]},
            {"id": "Matthew", "name": "Matthew", "gender": "male", "engines": ["standard", "neural", "generative"]}
        ],
        "custom_params": {
            "engine": {"type": "enum", "options": ["standard", "neural", "generative"], "default": "neural"},
            "lexicon_names": {"type": "array_string"}
        }
    },
    "google": {
        "id": "google",
        "name": "Google Cloud Text-to-Speech",
        "type": "cloud",
        "supports_offline": False,
        "supports_ssml": True,
        "supported_formats": ["mp3", "wav", "ogg"],
        "sample_rates": [16000, 24000, 48000],
        "languages": [
            {"code": "en-US", "name": "English (US)"},
            {"code": "ja-JP", "name": "Japanese"}
        ],
        "voices": [
            {"id": "en-US-Neural2-F", "name": "Neural2 Female F", "gender": "female"},
            {"id": "en-US-Studio-O", "name": "Studio Male O", "gender": "male"}
        ],
        "custom_params": {
            "ssml_gender": {"type": "string"},
            "effects_profile_id": {"type": "array_string"}
        }
    }
}

VOICE_PROFILES_LOCK = threading.Lock()

def get_voice_profiles_path():
    if is_test_mode():
        import tempfile
        return os.path.join(tempfile.gettempdir(), 'voice_profiles.json')
    return os.path.join('outputs', 'voice_profiles.json')

def get_seed_voice_profiles():
    now_iso = datetime.utcnow().isoformat() + 'Z'
    local_provider = 'dummy' if is_test_mode() else 'local_dia'
    default_voice = 'default' if is_test_mode() else 'dia-default'
    return [
        {
            "id": "default-local-dia",
            "name": "Default On-Device Voice",
            "description": "Local on-device TTS voice profile",
            "provider": local_provider,
            "voice_id": default_voice,
            "language": "en-US",
            "gender": "neutral",
            "is_default": True,
            "user": "system",
            "tenant": "global",
            "settings": {
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume": 100.0,
                "output_format": "wav",
                "sample_rate": 22050
            },
            "provider_params": {
                "temperature": 0.7,
                "guidance_scale": 3.0
            },
            "fallback_config": {
                "fallback_profile_id": None,
                "allow_provider_fallback": True,
                "fallback_provider": local_provider
            },
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "default-azure-jenny",
            "name": "Azure Jenny Neural",
            "description": "Cloud Azure Speech with Jenny Neural voice",
            "provider": "azure",
            "voice_id": "en-US-JennyNeural",
            "language": "en-US",
            "gender": "female",
            "is_default": False,
            "user": "system",
            "tenant": "global",
            "settings": {
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume": 100.0,
                "output_format": "mp3",
                "sample_rate": 24000
            },
            "provider_params": {
                "style": "cheerful",
                "style_degree": 1.0,
                "use_ssml": False
            },
            "fallback_config": {
                "fallback_profile_id": "default-local-dia",
                "allow_provider_fallback": True,
                "fallback_provider": local_provider
            },
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "default-aws-joanna",
            "name": "AWS Polly Joanna",
            "description": "Cloud AWS Polly Neural voice profile",
            "provider": "aws",
            "voice_id": "Joanna",
            "language": "en-US",
            "gender": "female",
            "is_default": False,
            "user": "system",
            "tenant": "global",
            "settings": {
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume": 100.0,
                "output_format": "mp3",
                "sample_rate": 22050
            },
            "provider_params": {
                "engine": "neural"
            },
            "fallback_config": {
                "fallback_profile_id": "default-local-dia",
                "allow_provider_fallback": True,
                "fallback_provider": local_provider
            },
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

def load_voice_profiles():
    path = get_voice_profiles_path()
    with VOICE_PROFILES_LOCK:
        if not os.path.exists(path):
            seeds = get_seed_voice_profiles()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(seeds, f, indent=2)
            return seeds
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return get_seed_voice_profiles()

def save_voice_profiles(profiles):
    path = get_voice_profiles_path()
    with VOICE_PROFILES_LOCK:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(profiles, f, indent=2)

def validate_voice_profile(data):
    if not isinstance(data, dict):
        return False, "Profile data must be an object"
    name = data.get('name')
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        return False, "Profile name is required and cannot be empty"
    provider = data.get('provider')
    if not provider or provider not in TTS_PROVIDER_REGISTRY:
        return False, f"Invalid provider '{provider}'. Must be one of: {list(TTS_PROVIDER_REGISTRY.keys())}"
    voice_id = data.get('voice_id')
    if not voice_id or not isinstance(voice_id, str):
        return False, "voice_id is required"
    language = data.get('language')
    if not language or not isinstance(language, str):
        return False, "language is required"
    
    settings = data.get('settings', {})
    if isinstance(settings, dict):
        rate = settings.get('speaking_rate', 1.0)
        if rate is not None and not (0.25 <= float(rate) <= 4.0):
            return False, "speaking_rate must be between 0.25 and 4.0"
        pitch = settings.get('pitch', 0.0)
        if pitch is not None and not (-20.0 <= float(pitch) <= 20.0):
            return False, "pitch must be between -20.0 and 20.0"
        vol = settings.get('volume', 100.0)
        if vol is not None and not (0.0 <= float(vol) <= 100.0):
            return False, "volume must be between 0.0 and 100.0"

    return True, None

def resolve_voice_profile_and_fallback(profile_id=None, user=None, tenant=None, overrides=None):
    profiles = load_voice_profiles()
    overrides = overrides or {}
    matched_profile = None

    if profile_id:
        for p in profiles:
            if p.get('id') == profile_id:
                matched_profile = p
                break

    if not matched_profile:
        for p in profiles:
            if p.get('is_default') and (p.get('user') == user or p.get('tenant') == tenant or p.get('tenant') == 'global'):
                matched_profile = p
                break
        if not matched_profile and profiles:
            matched_profile = profiles[0]

    if not matched_profile:
        matched_profile = get_seed_voice_profiles()[0]

    provider = matched_profile.get('provider', 'local_dia')
    fallback_applied = False
    warnings = []

    is_cloud = TTS_PROVIDER_REGISTRY.get(provider, {}).get('type') == 'cloud'
    if is_cloud and (is_test_mode() or os.environ.get('FORCE_PROVIDER_FALLBACK') == '1'):
        fb_config = matched_profile.get('fallback_config', {})
        if fb_config.get('allow_provider_fallback', True):
            fallback_provider = fb_config.get('fallback_provider', 'dummy' if is_test_mode() else 'local_dia')
            warnings.append(f"Cloud provider '{provider}' fallback triggered. Executing with '{fallback_provider}'.")
            provider = fallback_provider
            fallback_applied = True
        else:
            warnings.append(f"Cloud provider '{provider}' requested without fallback.")

    profile_settings = matched_profile.get('settings', {})
    merged_voice = overrides.get('voice') or matched_profile.get('voice_id')
    merged_speed = overrides.get('speed') or profile_settings.get('speaking_rate')
    merged_pitch = overrides.get('pitch') or profile_settings.get('pitch')
    merged_format = (overrides.get('format') or profile_settings.get('output_format', 'wav')).lower()
    merged_quality = overrides.get('quality') or 'medium'

    exec_meta = {
        "voice_profile_id": matched_profile.get('id'),
        "voice_profile_name": matched_profile.get('name'),
        "provider_used": provider,
        "fallback_applied": fallback_applied,
        "warnings": warnings,
        "merged_voice": merged_voice,
        "merged_speed": merged_speed,
        "merged_pitch": merged_pitch,
        "merged_format": merged_format,
        "merged_quality": merged_quality
    }

    return matched_profile, exec_meta

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

# Celery configuration — broker URL can be overridden via CELERY_BROKER_URL env var
_celery_broker = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
_celery_backend = os.environ.get('CELERY_RESULT_BACKEND', _celery_broker)
celery_app = Celery('diaspeak', broker=_celery_broker, backend=_celery_backend)

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
    Falls back to wav if ffmpeg/pydub conversion fails or is unavailable.
    """
    if fmt == 'wav':
        sf.write(output_file, audio_array, sampling_rate)
    else:
        try:
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
        except Exception:
            sf.write(output_file, audio_array, sampling_rate)

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

@app.route('/tts/providers', methods=['GET'])
def get_tts_providers():
    return jsonify(TTS_PROVIDER_REGISTRY)

@app.route('/voice-profiles', methods=['GET'])
@jwt_required
def list_voice_profiles():
    provider = request.args.get('provider')
    language = request.args.get('language')
    is_default = request.args.get('is_default')
    
    profiles = load_voice_profiles()
    user = getattr(g, 'user', None)
    tenant = getattr(g, 'tenant', None)

    filtered = []
    for p in profiles:
        p_user = p.get('user')
        p_tenant = p.get('tenant')
        if p_user in ('system', user) or p_tenant in ('global', tenant):
            filtered.append(p)

    if provider:
        filtered = [p for p in filtered if p.get('provider') == provider]
    if language:
        filtered = [p for p in filtered if p.get('language') == language]
    if is_default is not None:
        val = is_default.lower() in ('true', '1')
        filtered = [p for p in filtered if p.get('is_default') == val]

    return jsonify(filtered)

@app.route('/voice-profiles', methods=['POST'])
@jwt_required
def create_voice_profile():
    data = request.get_json() or {}
    is_valid, err = validate_voice_profile(data)
    if not is_valid:
        return jsonify({"error": "Validation error", "message": err}), 400

    profiles = load_voice_profiles()
    now_iso = datetime.utcnow().isoformat() + 'Z'
    profile_id = str(uuid.uuid4())
    
    user = getattr(g, 'user', 'system')
    tenant = getattr(g, 'tenant', 'global')

    new_profile = {
        "id": profile_id,
        "name": data.get('name').strip(),
        "description": data.get('description', ''),
        "provider": data.get('provider'),
        "voice_id": data.get('voice_id'),
        "language": data.get('language'),
        "gender": data.get('gender', 'unspecified'),
        "is_default": bool(data.get('is_default', False)),
        "user": user,
        "tenant": tenant,
        "settings": data.get('settings', {
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "volume": 100.0,
            "output_format": "wav",
            "sample_rate": 22050
        }),
        "provider_params": data.get('provider_params', {}),
        "fallback_config": data.get('fallback_config', {
            "fallback_profile_id": None,
            "allow_provider_fallback": True,
            "fallback_provider": "dummy" if is_test_mode() else "local_dia"
        }),
        "created_at": now_iso,
        "updated_at": now_iso
    }

    if new_profile['is_default']:
        for p in profiles:
            if p.get('user') == user or p.get('tenant') == tenant:
                p['is_default'] = False

    profiles.append(new_profile)
    save_voice_profiles(profiles)
    return jsonify(new_profile), 201

@app.route('/voice-profiles/<profile_id>', methods=['GET'])
@jwt_required
def get_voice_profile(profile_id):
    profiles = load_voice_profiles()
    user = getattr(g, 'user', None)
    tenant = getattr(g, 'tenant', None)
    for p in profiles:
        if p.get('id') == profile_id:
            if p.get('user') in ('system', user) or p.get('tenant') in ('global', tenant):
                return jsonify(p)
            return jsonify({"error": "Unauthorized access to profile"}), 403
    return jsonify({"error": "Voice profile not found"}), 404

@app.route('/voice-profiles/<profile_id>', methods=['PUT'])
@jwt_required
def update_voice_profile(profile_id):
    data = request.get_json() or {}
    profiles = load_voice_profiles()
    user = getattr(g, 'user', None)
    tenant = getattr(g, 'tenant', None)

    target_index = -1
    for i, p in enumerate(profiles):
        if p.get('id') == profile_id:
            target_index = i
            break

    if target_index == -1:
        return jsonify({"error": "Voice profile not found"}), 404

    target = profiles[target_index]
    if target.get('user') not in (user, 'system') and target.get('tenant') not in (tenant, 'global'):
        return jsonify({"error": "Unauthorized access to profile"}), 403

    merged = dict(target)
    for k in ['name', 'description', 'provider', 'voice_id', 'language', 'gender', 'is_default', 'settings', 'provider_params', 'fallback_config']:
        if k in data:
            merged[k] = data[k]

    is_valid, err = validate_voice_profile(merged)
    if not is_valid:
        return jsonify({"error": "Validation error", "message": err}), 400

    merged['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    if merged.get('is_default'):
        for p in profiles:
            if p.get('user') == user or p.get('tenant') == tenant:
                p['is_default'] = False

    profiles[target_index] = merged
    save_voice_profiles(profiles)
    return jsonify(merged)

@app.route('/voice-profiles/<profile_id>', methods=['DELETE'])
@jwt_required
def delete_voice_profile(profile_id):
    profiles = load_voice_profiles()
    user = getattr(g, 'user', None)
    tenant = getattr(g, 'tenant', None)

    target = None
    for p in profiles:
        if p.get('id') == profile_id:
            target = p
            break

    if not target:
        return jsonify({"error": "Voice profile not found"}), 404

    if target.get('user') == 'system':
        return jsonify({"error": "Cannot delete system default profiles"}), 400

    if target.get('user') != user and target.get('tenant') != tenant:
        return jsonify({"error": "Unauthorized access to profile"}), 403

    profiles = [p for p in profiles if p.get('id') != profile_id]
    save_voice_profiles(profiles)
    return jsonify({"message": "Voice profile deleted successfully"}), 200

@app.route('/speak', methods=['POST'])
@jwt_required
def speak():
    # Get text input and config params from the request
    data = request.get_json() or {}
    text = data.get('text', '')
    voice_profile_id = data.get('voice_profile_id')

    if not text:
        return jsonify({"error": "Text input is required."}), 400

    profile, exec_meta = resolve_voice_profile_and_fallback(
        profile_id=voice_profile_id,
        user=getattr(g, 'user', None),
        tenant=getattr(g, 'tenant', None),
        overrides=data
    )

    voice = exec_meta['merged_voice']
    speed = exec_meta['merged_speed']
    pitch = exec_meta['merged_pitch']
    format_ = exec_meta['merged_format']
    quality = exec_meta['merged_quality']

    # Log config params for future extension
    print(f"[TTS CONFIG] voice_profile_id={exec_meta['voice_profile_id']}, provider={exec_meta['provider_used']}, voice={voice}, speed={speed}, pitch={pitch}, format={format_}, quality={quality}")

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
        "voice_profile_id": exec_meta["voice_profile_id"],
        "voice_profile_name": exec_meta["voice_profile_name"],
        "provider_used": exec_meta["provider_used"],
        "fallback_applied": exec_meta["fallback_applied"],
        "warnings": exec_meta["warnings"]
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
