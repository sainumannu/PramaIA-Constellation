# Istruzioni per GitHub Copilot nel progetto PramaIA

## Convenzioni generali
- Quando generi comandi PowerShell, usa il punto e virgola (`;`) invece di `&&` per concatenare comandi
- Mantieni uno stile di codice coerente con quello esistente
- I nomi delle variabili dovrebbero essere in camelCase per JavaScript/TypeScript e snake_case per Python
- Documenta le funzioni con commenti che descrivono input, output e comportamento

## Struttura del progetto
- **PramaIA-PDK**: Framework per lo sviluppo di plugin e nodi di workflow
- **PramaIA-Agents**: Componenti autonomi che estendono il sistema via API
- **PramaIAServer**: Backend server con API REST e database

## Tecnologie principali
- Backend: Python (FastAPI)
- Frontend: TypeScript, React
- Workflow Engine: Node.js
- Elaborazione dati: Python con librerie specializzate

## Standard di documentazione
- Documenta tutti i nuovi nodi PDK con file Markdown dedicati
- I workflow devono includere un commento iniziale che spiega lo scopo e i requisiti
- Le API devono essere documentate con OpenAPI/Swagger

## Sviluppo futuro
- Favorisci la modularità e l'estensibilità
- Considera la compatibilità con versioni precedenti
- Mantieni una chiara separazione tra frontend e backend
