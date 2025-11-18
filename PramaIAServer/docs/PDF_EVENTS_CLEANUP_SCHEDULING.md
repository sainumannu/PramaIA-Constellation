# Configurazione Task Scheduler per Windows

Per configurare la pulizia automatica degli eventi PDF su Windows:

1. Apri Task Scheduler (Utilità di pianificazione)
   - Premi Win+R, digita `taskschd.msc` e premi Enter

2. Crea una nuova attività
   - Fai clic destro su "Libreria Utilità di pianificazione" -> "Crea attività"

3. Scheda Generale:
   - Nome: `PramaIA_PDF_Events_Cleanup`
   - Descrizione: `Pulizia automatica eventi PDF nel database PramaIA`
   - Seleziona: "Esegui solo quando l'utente ha effettuato l'accesso"
   - Seleziona: "Esegui con privilegi più elevati"

4. Scheda Trigger:
   - Fai clic su "Nuovo"
   - Inizia: "Su una pianificazione"
   - Impostazioni: "Giornaliero"
   - Ora: 00:00:00 (mezzanotte)
   - Fai clic su "OK"

5. Scheda Azioni:
   - Fai clic su "Nuovo"
   - Azione: "Avvia un programma"
   - Programma/script: `C:\PramaIA\PramaIAServer\PramaIA-venv\Scripts\python.exe`
   - Argomenti: `C:\PramaIA\PramaIAServer\schedule_pdf_events_cleanup.py`
   - Fai clic su "OK"

6. Scheda Condizioni:
   - Deseleziona "Avvia l'attività solo se il computer è alimentato a corrente alternata"

7. Scheda Impostazioni:
   - Seleziona "Consenti esecuzione su richiesta"
   - Seleziona "Se l'attività non viene eseguita, riavviala dopo: 30 minuti"
   - Fai clic su "OK" per completare la creazione dell'attività

# Configurazione Cron per Linux/macOS

Su sistemi Linux o macOS, puoi utilizzare cron:

1. Apri un terminale e digita `crontab -e`

2. Aggiungi la seguente riga per eseguire il cleanup ogni giorno a mezzanotte:
   ```
   0 0 * * * /path/to/python /path/to/PramaIA/PramaIAServer/schedule_pdf_events_cleanup.py
   ```

3. Salva e chiudi l'editor
