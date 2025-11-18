#!/usr/bin/env python3

import requests
import json

def test_triggers_endpoint():
    """Testa l'endpoint corretto per i nodi di input."""
    
    workflow_id = 'wf_055bf5029833'  # PDF Document UPDATE Pipeline
    url = f'http://localhost:8000/api/workflows/triggers/workflows/{workflow_id}/input-nodes'
    headers = {'Authorization': 'Bearer fake-token-for-debug'}

    print(f"Testing TRIGGERS endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f'Status Code: {response.status_code}')
        print(f'Response Body:')
        print(response.text)
        print('-' * 50)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print('✅ Successful Response:')
                print(f'   Workflow ID: {data.get("workflow_id", "N/A")}')
                print(f'   Workflow Name: {data.get("workflow_name", "N/A")}')
                print(f'   Input Nodes Count: {len(data.get("input_nodes", []))}')
                
                input_nodes = data.get('input_nodes', [])
                if input_nodes:
                    print('\n   Input Nodes:')
                    for idx, node in enumerate(input_nodes, 1):
                        print(f'   {idx}. {node.get("node_id", "N/A")}: {node.get("name", "N/A")} ({node.get("node_type", "N/A")})')
                        if node.get("description"):
                            print(f'      Description: {node["description"]}')
                else:
                    print('   ⚠️ No input nodes found!')
                    
                return True
                    
            except json.JSONDecodeError as e:
                print(f'❌ JSON decode error: {e}')
                
        else:
            print(f'❌ Status code: {response.status_code}')
            
    except requests.exceptions.RequestException as e:
        print(f'❌ Request failed: {e}')
        return False
        
    return False

if __name__ == '__main__':
    success = test_triggers_endpoint()
    if success:
        print('\n🎉 Fix implementato! Il frontend ora dovrebbe vedere i nodi di input.')
    else:
        print('\n❌ Test fallito.')