#!/usr/bin/env python3

import requests
import json
import sys

def test_input_nodes_api():
    """Testa l'API endpoint per i nodi di input del workflow."""
    
    workflow_id = 'wf_055bf5029833'  # PDF Document UPDATE Pipeline
    url = f'http://localhost:8000/api/workflows/{workflow_id}/input-nodes'
    headers = {'Authorization': 'Bearer fake-token-for-debug'}

    print(f"Testing API endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f'Status Code: {response.status_code}')
        print(f'Response Headers: {dict(response.headers)}')
        print('Response Body:')
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
                    
            except json.JSONDecodeError as e:
                print(f'❌ JSON decode error: {e}')
                
        elif response.status_code == 401:
            print('❌ Authentication failed (expected for this test)')
            
        elif response.status_code == 404:
            print('❌ Workflow not found')
            
        else:
            print(f'❌ Unexpected status code: {response.status_code}')
            
    except requests.exceptions.RequestException as e:
        print(f'❌ Request failed: {e}')
        return False
        
    return True

if __name__ == '__main__':
    test_input_nodes_api()