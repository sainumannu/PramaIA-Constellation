#!/usr/bin/env python3

import sqlite3
import json

conn = sqlite3.connect('PramaIAServer/backend/db/database.db')
cursor = conn.cursor()

# Guardiamo l'input_data del workflow fallito
cursor.execute('''
    SELECT execution_id, input_data, error_message
    FROM workflow_executions
    WHERE status = 'failed'
    ORDER BY started_at DESC
    LIMIT 1
''')

result = cursor.fetchone()
if result:
    exec_id, input_data, error = result
    print(f'Execution: {exec_id}')
    print(f'Error: {error}')
    print(f'Input data type: {type(input_data)}')
    
    if input_data:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            print(f'Input keys: {list(data.keys()) if isinstance(data, dict) else "Not dict"}')
            
            if 'trigger' in data:
                print(f'Trigger: {data["trigger"]}')
            if 'execution_context' in data:
                print(f'Context: {data["execution_context"]}')
                
        except Exception as e:
            print(f'Error parsing input: {e}')
            print(f'Raw input: {input_data[:500]}...')

conn.close()