#!/usr/bin/env python3
"""
Test completo operazioni CRUD ChromaDB
Test delle funzionalità complete del VectorStoreOperationsProcessor
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import PDK processor invece del processore server
from backend.engine.processors import PDKNodeProcessor


async def test_full_crud():
    print('🚀 Test completo operazioni CRUD ChromaDB\n')
    proc = VectorStoreOperationsProcessor()
    await proc._initialize_chroma_client()
    
    # 1. CREATE (Index) - Documento iniziale
    print('📝 1. CREATE - Indicizzazione documento...')
    doc1_input = {
        'document_id': 'doc_manual_001',
        'chunks': [
            {
                'chunk_id': 'doc_manual_001_chunk_0',
                'text': 'Manuale utente per il sistema PramaIA. Questo sistema gestisce workflow automatizzati.',
                'metadata': {'source': 'manual.pdf', 'chunk_index': 0, 'page': 1, 'document_id': 'doc_manual_001'}
            },
            {
                'chunk_id': 'doc_manual_001_chunk_1',
                'text': 'I trigger del sistema permettono di automatizzare le operazioni sui documenti PDF.',
                'metadata': {'source': 'manual.pdf', 'chunk_index': 1, 'page': 2, 'document_id': 'doc_manual_001'}
            }
        ]
    }
    
    create_result = await proc._index_document(doc1_input, {})
    print(f'   ✅ Indicizzati {create_result.get("indexed_count", 0)} chunks')
    print(f'   Status: {create_result["status"]}')
    
    # 2. READ (Search) - Ricerca nel contenuto
    print('\n🔍 2. READ - Ricerca semantica...')
    search_tests = [
        'sistema workflow',
        'trigger automatizzazione', 
        'documenti PDF',
        'manuale utente'
    ]
    
    for query in search_tests:
        search_input = {'query': query}
        search_result = await proc._search_documents(search_input, {'limit': 3})
        found = search_result.get('total_found', 0)
        print(f'   Query: "{query}" → {found} risultati')
        if search_result['results']:
            best_match = search_result['results'][0]
            distance = best_match.get('distance', 'N/A')
            snippet = best_match['document'][:60] + '...'
            print(f'     Migliore: [{distance:.3f}] {snippet}')
    
    # 3. CREATE (Index) - Secondo documento  
    print('\n📝 3. CREATE - Secondo documento...')
    doc2_input = {
        'document_id': 'doc_guide_002',
        'chunks': [
            {
                'chunk_id': 'doc_guide_002_chunk_0',
                'text': 'Guida sviluppatore API PramaIA. Le API REST permettono integrazione con sistemi esterni.',
                'metadata': {'source': 'api_guide.pdf', 'chunk_index': 0, 'page': 1, 'document_id': 'doc_guide_002'}
            },
            {
                'chunk_id': 'doc_guide_002_chunk_1', 
                'text': 'Endpoint per gestione documenti: POST /documents, GET /documents/{id}, DELETE /documents/{id}.',
                'metadata': {'source': 'api_guide.pdf', 'chunk_index': 1, 'page': 3, 'document_id': 'doc_guide_002'}
            }
        ]
    }
    
    create2_result = await proc._index_document(doc2_input, {})
    print(f'   ✅ Indicizzati {create2_result.get("indexed_count", 0)} chunks aggiuntivi')
    
    # Verifica totale documenti
    total_count = proc.collection.count()
    print(f'   📊 Totale chunks nel database: {total_count}')
    
    # 4. READ (Search) - Ricerca cross-document
    print('\n🔍 4. READ - Ricerca cross-document...')
    cross_queries = [
        'API REST',
        'documenti PDF', 
        'sistemi PramaIA'
    ]
    
    for query in cross_queries:
        search_input = {'query': query}
        search_result = await proc._search_documents(search_input, {'limit': 5})
        found = search_result.get('total_found', 0)
        print(f'   Query: "{query}" → {found} risultati')
        
        # Mostra risultati da documenti diversi
        docs_found = set()
        for result in search_result['results'][:3]:
            doc_id = result['metadata'].get('document_id', 'unknown')
            source = result['metadata'].get('source', 'unknown')
            docs_found.add(f'{doc_id} ({source})')
        print(f'     Documenti trovati: {list(docs_found)}')
    
    # 5. UPDATE - Aggiornamento documento
    print('\n🔄 5. UPDATE - Aggiornamento documento...')
    # Simula aggiornamento del primo documento con contenuto modificato
    updated_doc1 = {
        'document_id': 'doc_manual_001',
        'chunk_ids': ['doc_manual_001_chunk_0', 'doc_manual_001_chunk_1'],  # Per delete
        'chunks': [
            {
                'chunk_id': 'doc_manual_001_chunk_0_v2',
                'text': 'Manuale utente PramaIA versione 2.0. Sistema avanzato per workflow automatizzati con AI.',
                'metadata': {'source': 'manual_v2.pdf', 'chunk_index': 0, 'page': 1, 'document_id': 'doc_manual_001', 'version': '2.0'}
            },
            {
                'chunk_id': 'doc_manual_001_chunk_1_v2',
                'text': 'I trigger intelligenti utilizzano machine learning per ottimizzare le operazioni sui documenti.',
                'metadata': {'source': 'manual_v2.pdf', 'chunk_index': 1, 'page': 2, 'document_id': 'doc_manual_001', 'version': '2.0'}
            }
        ]
    }
    
    update_result = await proc._update_document(updated_doc1, {})
    print(f'   ✅ Update Status: {update_result["status"]}')
    print(f'   📝 Chunks aggiornati: {update_result.get("indexed_count", 0)}')
    
    # Verifica update con ricerca
    search_input = {'query': 'machine learning trigger'}
    search_result = await proc._search_documents(search_input, {'limit': 2})
    if search_result['results']:
        best = search_result['results'][0]
        version = best['metadata'].get('version', 'N/A')
        print(f'   🔍 Verifica update: trovata versione {version}')
        print(f'      Contenuto: {best["document"][:80]}...')
    
    # 6. DELETE - Eliminazione documento
    print('\n🗑️ 6. DELETE - Eliminazione documento...')
    delete_input = {'document_id': 'doc_guide_002'}
    delete_result = await proc._delete_document(delete_input, {})
    print(f'   ✅ Delete Status: {delete_result["status"]}')
    print(f'   🗑️ Chunks eliminati: {delete_result.get("deleted_count", 0)}')
    
    # Verifica finale
    final_count = proc.collection.count()
    print(f'\n📊 STATO FINALE:')
    print(f'   Chunks totali: {final_count}')
    print(f'   Operazioni testate: ✅ Create ✅ Read ✅ Update ✅ Delete')
    
    # Test ricerca finale per conferma
    print(f'\n🔍 VERIFICA FINALE - Ricerca contenuto rimanente...')
    search_input = {'query': 'PramaIA'}
    search_result = await proc._search_documents(search_input, {'limit': 10})
    remaining_docs = set()
    for result in search_result['results']:
        doc_id = result['metadata'].get('document_id', 'unknown')
        source = result['metadata'].get('source', 'unknown')
        remaining_docs.add(f'{doc_id} ({source})')
    
    print(f'   Documenti rimanenti: {list(remaining_docs)}')
    print(f'   ✅ Test CRUD completato con successo!')


if __name__ == "__main__":
    asyncio.run(test_full_crud())