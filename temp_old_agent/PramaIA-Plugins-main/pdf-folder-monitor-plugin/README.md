# PDF Folder Monitor Plugin

Plugin esterno per PramaIA: monitora una cartella, estrae testo dai PDF, genera embedding e aggiorna un vector database per utente.

## Funzionalità previste
- Monitoraggio file system (watchdog)
- Estrazione testo PDF (pdfplumber, PyPDF2, unstructured)
- Generazione embedding (HuggingFace Transformers, Instructor, MiniLM, ecc.)
- Salvataggio in vector DB (Qdrant, Chroma, ecc.)
- Namespace/indice separato per ogni utente

## Requisiti
- Python 3.9+
- Solo dipendenze open source

## Struttura consigliata
- `src/` — codice principale
- `tests/` — test automatici
- `requirements.txt` — dipendenze


## Avvio rapido

### Windows
```bat
pip install -r requirements.txt
python src/main.py
```

### Mac/Linux
```sh
chmod +x start.command
./start.command
```

## TODO
- [ ] Implementazione watcher
- [ ] Parsing PDF
- [ ] Embedding
- [ ] Vector DB
- [ ] API di stato
