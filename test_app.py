import os
import subprocess
import sys
import tempfile
import pytest
import json
from src.app import app


@pytest.fixture(autouse=True)
def reset_rate_limit():
    from src.app import RATE_LIMIT
    RATE_LIMIT.clear()

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
    items = catalog['results'] if isinstance(catalog, dict) and 'results' in catalog else catalog
    assert any(row['user'] == 'alice' for row in items)

def test_rate_limit(client):
    token = get_jwt_token(client, 'bob', 'password456')
    for _ in range(10):
        client.post('/speak', json={'text': 'Rate limit test'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.post('/speak', json={'text': 'Rate limit test'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 429

def test_get_tts_providers(client):
    resp = client.get('/tts/providers')
    assert resp.status_code == 200
    providers = resp.get_json()
    assert 'azure' in providers
    assert 'aws' in providers
    assert 'google' in providers
    assert 'dummy' in providers
    assert 'local_dia' in providers
    assert providers['azure']['supports_ssml'] is True
    assert providers['local_dia']['type'] == 'local'

def test_list_voice_profiles(client):
    token = get_jwt_token(client, 'alice', 'password123')
    resp = client.get('/voice-profiles', headers={'Authorization': 'Bearer ' + token})
    assert resp.status_code == 200
    profiles = resp.get_json()
    assert isinstance(profiles, list)
    assert len(profiles) >= 3

    resp_filtered = client.get('/voice-profiles?provider=azure', headers={'Authorization': 'Bearer ' + token})
    assert resp_filtered.status_code == 200
    azure_profiles = resp_filtered.get_json()
    assert all(p['provider'] == 'azure' for p in azure_profiles)

def test_create_get_update_delete_voice_profile(client):
    token = get_jwt_token(client, 'alice', 'password123')
    headers = {'Authorization': 'Bearer ' + token}

    payload = {
        'name': 'Alice Custom Azure Voice',
        'description': 'Custom voice profile for Alice',
        'provider': 'azure',
        'voice_id': 'en-US-JennyNeural',
        'language': 'en-US',
        'gender': 'female',
        'settings': {
            'speaking_rate': 1.1,
            'pitch': 2.0,
            'volume': 90.0,
            'output_format': 'mp3',
            'sample_rate': 24000
        },
        'provider_params': {
            'style': 'cheerful',
            'style_degree': 1.2
        },
        'fallback_config': {
            'allow_provider_fallback': True,
            'fallback_provider': 'dummy'
        }
    }
    resp = client.post('/voice-profiles', json=payload, headers=headers)
    assert resp.status_code == 201
    created = resp.get_json()
    profile_id = created['id']
    assert created['name'] == 'Alice Custom Azure Voice'
    assert created['user'] == 'alice'

    resp_get = client.get(f'/voice-profiles/{profile_id}', headers=headers)
    assert resp_get.status_code == 200
    fetched = resp_get.get_json()
    assert fetched['id'] == profile_id

    update_payload = {'name': 'Alice Updated Azure Voice', 'description': 'Updated description'}
    resp_update = client.put(f'/voice-profiles/{profile_id}', json=update_payload, headers=headers)
    assert resp_update.status_code == 200
    updated = resp_update.get_json()
    assert updated['name'] == 'Alice Updated Azure Voice'

    resp_del = client.delete(f'/voice-profiles/{profile_id}', headers=headers)
    assert resp_del.status_code == 200

    resp_del_sys = client.delete('/voice-profiles/default-local-dia', headers=headers)
    assert resp_del_sys.status_code == 400

def test_speak_with_voice_profile(client):
    token = get_jwt_token(client, 'alice', 'password123')
    headers = {'Authorization': 'Bearer ' + token}

    resp = client.post('/speak', json={
        'text': 'Speech with voice profile',
        'voice_profile_id': 'default-azure-jenny'
    }, headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['voice_profile_id'] == 'default-azure-jenny'
    assert data['fallback_applied'] is True
    assert data['provider_used'] in ('dummy', 'local_dia')

def test_voice_profile_validation_errors(client):
    token = get_jwt_token(client, 'alice', 'password123')
    headers = {'Authorization': 'Bearer ' + token}

    resp = client.post('/voice-profiles', json={
        'name': 'Invalid Provider Test',
        'provider': 'unknown_provider',
        'voice_id': 'v1',
        'language': 'en-US'
    }, headers=headers)
    assert resp.status_code == 400

    resp2 = client.post('/voice-profiles', json={
        'name': 'Invalid Rate Test',
        'provider': 'azure',
        'voice_id': 'en-US-JennyNeural',
        'language': 'en-US',
        'settings': {'speaking_rate': 10.0}
    }, headers=headers)
    assert resp2.status_code == 400
