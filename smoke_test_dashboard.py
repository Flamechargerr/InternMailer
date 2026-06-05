#!/usr/bin/env python3
import json
import urllib.request
from urllib.error import URLError

BASE = 'http://localhost:5050'

def get(path):
    with urllib.request.urlopen(BASE + path) as resp:
        return json.loads(resp.read().decode())

def post(path, payload=None):
    payload = payload or {}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def main():
    print('--- Minimal UI Smoke Test ---')
    print('1) GET /api/health')
    print(get('/api/health'))
    print('2) GET /api/stats')
    print(get('/api/stats'))
    print('3) POST /send-emails {count:10}')
    print(post('/send-emails', {'count': 10}))
    print('4) GET /preview-emails?count=2')
    print(get('/preview-emails?count=2'))
    print('5) POST /api/daemon/start')
    print(post('/api/daemon/start', {}))
    print('6) GET /api/daemon/status')
    print(get('/api/daemon/status'))
    print('7) POST /api/daemon/stop')
    print(post('/api/daemon/stop', {}))
    print('8) GET /api/daemon/status')
    print(get('/api/daemon/status'))
    print('--- All tests completed successfully ---')

if __name__ == '__main__':
    try:
        main()
    except URLError as e:
        print('Connection error. Make sure the UI is running on port 5050.')
        print(e)
