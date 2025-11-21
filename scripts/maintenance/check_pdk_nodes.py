#!/usr/bin/env python3
import requests

try:
    resp = requests.get('http://localhost:3001/api/nodes')
    data = resp.json()
    
    print('🔧 Nodi PDK disponibili:')
    print(f'Response type: {type(data)}')
    print(f'Data: {data}')
    
    if isinstance(data, dict):
        for k, v in data.items():
            desc = v.get('description', 'N/A') if isinstance(v, dict) else str(v)
            print(f'  • {k}: {desc}')
        print(f'\n📊 Totale nodi: {len(data)}')
    elif isinstance(data, list):
        for item in data:
            print(f'  • {item}')
        print(f'\n📊 Totale nodi: {len(data)}')
    else:
        print(f'Formato dati inatteso: {type(data)}')
    
except Exception as e:
    print(f'Errore: {e}')