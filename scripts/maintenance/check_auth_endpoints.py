#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

resp = requests.get('http://localhost:8000/openapi.json')
spec = resp.json()

auth_paths = {
    '/auth/callback': spec['paths'].get('/auth/callback', {}),
    '/auth/login': spec['paths'].get('/auth/login', {}),
    '/auth/register': spec['paths'].get('/auth/register', {}),
    '/auth/token/local': spec['paths'].get('/auth/token/local', {})
}

for path, methods in auth_paths.items():
    print(f"\n{path}")
    print("=" * 80)
    for method, details in methods.items():
        print(f"  {method.upper()}")
        if 'summary' in details:
            print(f"    Summary: {details['summary']}")
        if 'requestBody' in details:
            print(f"    Request: {json.dumps(details['requestBody'], indent=6)[:200]}")
        if 'responses' in details:
            for status, resp_info in details['responses'].items():
                print(f"    Response {status}: {resp_info.get('description', 'N/A')}")
