#!/usr/bin/env python3
"""
Test coordinamento ChromaDB e SQLite metadati
Verifica che entrambi i database metadati funzionino correttamente
"""

import sys
import os
sys.path.append('C:/PramaIA/PramaIA-VectorstoreService')

from app.utils.sqlite_metadata_manager import SQLiteMetadataManager
from datetime import datetime


def test_sqlite_metadata():
    print('🏗️ Test Database SQLite Metadati\n')
    
    # Inizializza SQLite metadata manager
    data_dir = 'C:/PramaIA/PramaIA-VectorstoreService/data'
    os.makedirs(data_dir, exist_ok=True)
    
    sqlite_manager = SQLiteMetadataManager(data_dir=data_dir)
    
    # Verifica stato
    doc_count = sqlite_manager.get_document_count()
    print(f'📊 Documenti in SQLite metadati: {doc_count}')
    
    # Lista primi documenti per confronto
    if doc_count > 0:
        docs = sqlite_manager.get_documents(limit=5)
        print('🗃️ Primi documenti SQLite:')
        for doc in docs:
            doc_id = doc.get('id', 'N/A')
            filename = doc.get('filename', 'N/A')
            metadata_count = len(doc.get('metadata', {}))
            print(f'   - {doc_id} | {filename} | {metadata_count} metadati')
    else:
        print('📭 Database SQLite metadati vuoto')
        
    # Test aggiunta documento per verifica coordinamento
    print('\n🔧 Test inserimento documento coordinamento...')
    test_doc = {
        'id': 'test_coordination_001',
        'filename': 'test_coordination.pdf', 
        'collection': 'test_collection',
        'content': 'Test contenuto per verificare coordinamento tra ChromaDB e SQLite.',
        'metadata': {
            'source': 'coordination_test',
            'created_at': datetime.now().isoformat(),
            'test_field': 'coordinamento_attivo',
            'chunk_count': 1,
            'document_type': 'test',
            'priority': 'high'
        }
    }
    
    success = sqlite_manager.add_document(test_doc)
    print(f'✅ Test inserimento SQLite: {success}')
    
    if success:
        # Recupera documento
        retrieved = sqlite_manager.get_document('test_coordination_001')
        if retrieved:
            print(f'🔍 Documento recuperato: {retrieved["filename"]}')
            metadata_keys = list(retrieved["metadata"].keys())
            print(f'📋 Metadati ({len(metadata_keys)}): {metadata_keys}')
            print(f'📄 Contenuto: {len(retrieved.get("content", ""))} caratteri')
        
        # Test ricerca metadati
        print('\n🔍 Test ricerca SQLite...')
        search_results = sqlite_manager.search_documents('coordination')
        print(f'Risultati ricerca "coordination": {len(search_results)}')
        
        # Test metadati filters
        metadata_filter = {'test_field': 'coordinamento_attivo'}
        filtered_results = sqlite_manager.search_documents('test', metadata_filters=metadata_filter)
        print(f'Risultati con filtro metadati: {len(filtered_results)}')
    
    print('\n📊 STATO DATABASE SQLite:')
    final_count = sqlite_manager.get_document_count()
    print(f'   Totale documenti: {final_count}')
    
    # Statistiche collezioni
    collections = sqlite_manager.get_collections()
    print(f'   Collezioni: {collections}')
    
    for collection in collections:
        stats = sqlite_manager.get_collection_stats(collection)
        doc_count = stats.get('document_count', 0)
        print(f'   - {collection}: {doc_count} documenti')
    
    print('\n✅ Test SQLite metadati completato!')


if __name__ == "__main__":
    test_sqlite_metadata()