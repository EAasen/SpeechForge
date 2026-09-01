import os
import subprocess
import sys
import tempfile
import pytest
import json
from src.app import app

def get_jwt_token(client, username, password):
    resp = client.post('/login', json={'username': username, 'password': password})
    assert resp.status_code == 200
    return resp.get_json()['token']

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_success(client):
    resp = client.post('/login', json={'username': 'alice', 'password': 'password123'})
    assert resp.status_code == 200
    assert 'token' in resp.get_json()

def test_login_fail(client):
    resp = client.post('/login', json={'username': 'alice', 'password': 'wrong'})
    assert resp.status_code == 401

def test_speak_requires_auth(client):
    resp = client.post('/speak', json={'text': 'Hello world'})
    assert resp.status_code == 401

def test_startup_creates_outputs_directory(tmp_path):
    repo_root = os.path.dirname(__file__)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in [repo_root, env.get("PYTHONPATH")] if p
    )
    env["TTS_BACKEND"] = "dummy"
    env["TESTING"] = "1"
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; "
                f"os.chdir({str(tmp_path)!r}); "
                "import src.app; "
                "assert os.path.isdir('outputs')"
            ),
        ],
        check=True,
        env=env,
    )

def test_speak_minimal(client):
    token = get_jwt_token(client, 'alice', 'password123')
    resp = client.post('/speak', json={'text': 'Hello world'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'file_path' in data and 'url' in data

def test_catalog_filtering(client):
    token = get_jwt_token(client, 'alice', 'password123')
    # Add an entry
    client.post('/speak', json={'text': 'Test catalog filter'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.get('/catalog?user=alice')
    assert resp.status_code == 200
    catalog = resp.get_json()
    assert any(row['user'] == 'alice' for row in catalog)

def test_rate_limit(client):
    token = get_jwt_token(client, 'bob', 'password456')
    for _ in range(10):
        client.post('/speak', json={'text': 'Rate limit test'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.post('/speak', json={'text': 'Rate limit test'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 429


def test_google_tts_backend_registered():
    from src.app import TTS_BACKENDS, GoogleTTS
    assert TTS_BACKENDS['google'] is GoogleTTS


def test_google_tts_generates_audio():
    import io
    import numpy as np
    import soundfile as sf
    from src.app import GoogleTTS

    # Build a small valid WAV payload to stand in for Google's LINEAR16 response.
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, np.zeros(100, dtype=np.float32), 16000, format='WAV')
    wav_bytes = wav_buffer.getvalue()

    class FakeResponse:
        audio_content = wav_bytes

    class FakeClient:
        def synthesize_speech(self, input, voice, audio_config):
            return FakeResponse()

    tts = GoogleTTS.__new__(GoogleTTS)
    from google.cloud import texttospeech
    tts._texttospeech = texttospeech
    tts.client = FakeClient()

    result = tts("Hello world", voice="en-US-Neural2-F", speed=1.0, pitch=0)
    assert result["sampling_rate"] == 16000
    assert len(result["audio"]) == 100
