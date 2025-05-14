import os
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
