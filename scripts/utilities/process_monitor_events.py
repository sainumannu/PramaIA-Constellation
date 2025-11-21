#!/usr/bin/env python3
import requests
import json

# Leggi tutti gli eventi dal Monitor
r = requests.get('http://localhost:8001/monitor/events?limit=100')
if r.status_code != 200:
    print(f'Error getting events: {r.status_code}')
    exit(1)

unsent_events = r.json().get('unsent_events', [])
print(f'Processing {len(unsent_events)} events from Monitor...\n')

# Invia ogni evento al backend
processed = 0
failed = 0
for event in unsent_events[:15]:  # Primo 15
    event_id = event.get('id')
    event_type = event.get('event_type', 'created')
    
    payload = {
        'event_type': event_type,
        'source': 'document_monitor',
        'data': event
    }
    
    try:
        r = requests.post('http://localhost:8000/api/events/process', 
                         json=payload, timeout=5)
        if r.status_code == 200:
            result = r.json()
            msg = result.get('message', 'processed')[:60]
            print(f'✓ Event {event_id} ({event_type}): {msg}')
            processed += 1
        else:
            print(f'✗ Event {event_id}: HTTP {r.status_code}')
            failed += 1
    except Exception as e:
        print(f'✗ Event {event_id}: {str(e)[:50]}')
        failed += 1

print(f'\n=== RESULT ===')
print(f'Processed: {processed}')
print(f'Failed: {failed}')
print(f'Total: {len(unsent_events)}')
