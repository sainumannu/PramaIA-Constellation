# Roadmap: Ricerca Semantica PDF per Utente (PramaIA)

## Obiettivo
Consentire a ciascun utente di monitorare una propria cartella, indicizzare i PDF in un vector database personale e interrogarli tramite ricerca semantica e LLM, usando tecnologie gratuite/open source ove possibile.

---

## 1. Punti Salienti
- Ogni utente può configurare una cartella da monitorare
- I PDF vengono estratti, indicizzati e vettorializzati solo per quell’utente
- Vector DB separato (o namespace) per ogni utente
- Query semantica tramite LLM sui propri documenti
- Tutto integrato come nodi PDK modulari

---

## 2. Roadmap Tecnica

### Fase 1: Progettazione
- [ ] Definizione schema nodi PDK:
    - Nodo "Folder Monitor" (ingestione/indicizzazione)
    - Nodo "Semantic Query" (retrieval + LLM)
- [ ] Scelta stack open source:
    - Vector DB: Qdrant, Chroma, Milvus, ecc.
    - Embedding: HuggingFace Transformers, Instructor, MiniLM, ecc.
    - Estrazione PDF: PyPDF2, pdfplumber, unstructured
    - LLM: Ollama, LM Studio, HuggingFace, ecc.

### Fase 2: Implementazione Backend
- [ ] Nodo Folder Monitor:
    - Configurazione percorso cartella, filtri, modello embedding
    - Estrazione testo, generazione embedding, salvataggio in vector DB
    - Deduplicazione e aggiornamento incrementale
- [ ] Nodo Semantic Query:
    - Configurazione parametri ricerca (top-k, soglia, prompt)
    - Query → embedding → ricerca vector DB → retrieval chunk → LLM
    - Output risposta LLM

### Fase 3: Integrazione Frontend
- [ ] UI per configurare cartella e parametri
- [ ] UI per inserire query semantica e visualizzare risultati
- [ ] Visualizzazione stato indicizzazione e log

### Fase 4: Sicurezza e Privacy
- [ ] Isolamento dati utente (namespace, ACL, ecc.)
- [ ] Accesso solo ai propri dati

### Fase 5: Testing e Ottimizzazione
- [ ] Test end-to-end multiutente
- [ ] Ottimizzazione performance e UX

---

## 3. Vincoli
- **Solo tecnologie gratuite/open source** (no Pinecone, no OpenAI API a pagamento)
- **Scalabilità**: ogni utente ha il proprio spazio vettoriale
- **Privacy**: nessun dato condiviso tra utenti
- **Modularità**: ogni step come nodo PDK

---

## 4. Estensioni Future
- OCR per PDF scansionati
- Estrazione tabelle e immagini
- Notifiche su nuovi documenti rilevanti
- Integrazione con altri workflow

---

**Questa roadmap va aggiornata a ogni milestone.**
