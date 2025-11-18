#!/usr/bin/env python3
"""
Test coordinamento completo ChromaDB + SQLite
Verifica sincronizzazione tra vector store e database metadati strutturato
"""

import sys
import os
import asyncio
from datetime import datetime

# Setup paths
sys.path.append('C:/PramaIA')
sys.path.append('C:/PramaIA/PramaIA-VectorstoreService')

# Import PDK processor invece del processore server
from backend.engine.processors import PDKNodeProcessor
from app.utils.sqlite_metadata_manager import SQLiteMetadataManager


async def test_coordinated_storage():
    print('🔗 Test Coordinamento ChromaDB ↔ SQLite\n')
    
    # Inizializza entrambi i sistemi
    print('🚀 Inizializzazione sistemi...')
    
    # ChromaDB Vector Store
    vector_processor = VectorStoreOperationsProcessor()
    await vector_processor._initialize_chroma_client()
    print('✅ ChromaDB inizializzato')
    
    # SQLite Metadata Database  
    sqlite_manager = SQLiteMetadataManager(data_dir='C:/PramaIA/PramaIA-VectorstoreService/data')
    print('✅ SQLite metadati inizializzato')
    
    # Documento di test completo
    print('\n📄 Preparazione documento test...')
    test_document = {
        'document_id': 'coordinated_doc_001',
        'filename': 'manual_coordinamento.pdf',
        'collection': 'manuals',
        'content': 'Manuale di coordinamento tra sistemi PramaIA. Questo documento spiega come ChromaDB e SQLite lavorano insieme per gestire metadati strutturati e ricerca vettoriale.',
        'metadata': {
            'source': 'coordination_manual.pdf',
            'author': 'PramaIA Team', 
            'created_at': datetime.now().isoformat(),
            'document_type': 'manual',
            'priority': 'high',
            'tags': ['coordinamento', 'architettura', 'metadati'],
            'page_count': 25,
            'file_size': 2048000,
            'language': 'italian',
            'version': '1.0',
            'security_level': 'internal'
        }
    }
    
    # Test 1: Salvataggio coordinato  
    print('\n1️⃣ SALVATAGGIO COORDINATO')
    print('   🔄 SQLite: Metadati strutturati...')
    
    # SQLite: metadati completi e contenuto
    sqlite_doc = {
        'id': test_document['document_id'],
        'filename': test_document['filename'], 
        'collection': test_document['collection'],
        'content': test_document['content'],
        'metadata': test_document['metadata']
    }
    
    sqlite_success = sqlite_manager.add_document(sqlite_doc)
    print(f'   ✅ SQLite storage: {sqlite_success}')
    
    # ChromaDB: chunks con metadati per ricerca  
    print('   🔄 ChromaDB: Vector indexing...')
    
    # Simula chunking del contenuto
    content = test_document['content']
    chunks = [
        {
            'chunk_id': f"{test_document['document_id']}_chunk_0",
            'text': content[:100] + '...',
            'metadata': {
                **test_document['metadata'],
                'chunk_index': 0,
                'document_id': test_document['document_id']
            }
        },
        {
            'chunk_id': f"{test_document['document_id']}_chunk_1", 
            'text': '...' + content[100:],
            'metadata': {
                **test_document['metadata'],
                'chunk_index': 1,  
                'document_id': test_document['document_id']
            }
        }
    ]
    
    chroma_input = {
        'document_id': test_document['document_id'],
        'chunks': chunks
    }
    
    chroma_result = await vector_processor._index_document(chroma_input, {})
    print(f'   ✅ ChromaDB indexing: {chroma_result["status"]} ({chroma_result.get("indexed_count", 0)} chunks)')
    
    # Test 2: Verifica accesso coordinato
    print('\n2️⃣ VERIFICA ACCESSO COORDINATO')
    
    # SQLite: accesso metadati strutturati
    print('   🔍 SQLite: Query metadati...')
    sqlite_retrieved = sqlite_manager.get_document(test_document['document_id'])
    if sqlite_retrieved:
        print(f'      📋 Metadati recuperati: {len(sqlite_retrieved["metadata"])} campi')
        print(f'      📄 Contenuto: {len(sqlite_retrieved.get("content", ""))} caratteri')
        print(f'      🏷️ Tags: {sqlite_retrieved["metadata"].get("tags", [])}')
        print(f'      👤 Autore: {sqlite_retrieved["metadata"].get("author", "N/A")}')
    
    # ChromaDB: ricerca semantica 
    print('   🔍 ChromaDB: Ricerca semantica...')
    search_queries = ['coordinamento sistemi', 'metadati architettura', 'PramaIA manuale']
    
    for query in search_queries:
        search_input = {'query': query}
        search_result = await vector_processor._search_documents(search_input, {'limit': 3})
        found = search_result.get('total_found', 0)
        print(f'      Query "{query}": {found} risultati')
        
        if search_result['results']:
            best = search_result['results'][0]
            distance = best.get('distance', 'N/A')
            doc_id = best['metadata'].get('document_id', 'N/A')
            print(f'         Migliore: {doc_id} [distance: {distance:.3f}]')
    
    # Test 3: Ricerca filtrata combinata
    print('\n3️⃣ RICERCA FILTRATA COMBINATA')
    
    # SQLite: filtro metadati strutturato
    print('   🔍 SQLite: Filtro per priority=high...')
    metadata_filter = {'priority': 'high'}
    filtered_docs = sqlite_manager.search_documents('manual', metadata_filters=metadata_filter)
    print(f'      Documenti high priority: {len(filtered_docs)}')
    
    # ChromaDB: verifica che i metadati siano searchable  
    print('   🔍 ChromaDB: Verifica metadati in vector search...')
    if search_result['results']:
        sample_metadata = search_result['results'][0]['metadata']
        metadata_keys = list(sample_metadata.keys())
        print(f'      Metadati in ChromaDB: {len(metadata_keys)} campi')
        print(f'      Campi disponibili: {metadata_keys[:5]}...')
    
    # Test 4: Statistiche coordinate  
    print('\n4️⃣ STATISTICHE COORDINATE')
    
    # SQLite stats
    sqlite_count = sqlite_manager.get_document_count()
    collections = sqlite_manager.get_collections()
    print(f'   📊 SQLite: {sqlite_count} documenti in {len(collections)} collezioni')
    
    # ChromaDB stats
    chroma_count = vector_processor.collection.count()  
    print(f'   📊 ChromaDB: {chroma_count} chunks vettoriali')
    
    # Rapporto coordinamento
    if sqlite_count > 0:
        chunk_ratio = chroma_count / sqlite_count
        print(f'   📈 Rapporto chunks/documenti: {chunk_ratio:.1f}')
    
    print('\n✅ Test coordinamento completato!')
    print('\n📋 RIEPILOGO ARCHITETTURA:')
    print('   🗄️ SQLite: Metadati strutturati, contenuto completo, query relazionali')
    print('   🔍 ChromaDB: Embedding vettoriali, ricerca semantica, similarity search')
    print('   🔗 Coordinamento: Metadati condivisi, accesso ottimizzato per use case')


if __name__ == "__main__":
    asyncio.run(test_coordinated_storage())