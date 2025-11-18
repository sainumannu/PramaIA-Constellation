"""
Script per analizzare e correggere i trigger esistenti
"""
import os
import sqlite3
import json

# Percorso del database
DB_PATH = os.path.join("backend", "db", "database.db")

def print_trigger_summary(conn):
    """Stampa un riepilogo dei trigger esistenti."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, event_type, source, workflow_id, target_node_id, conditions, active
        FROM workflow_triggers
    """)
    triggers = cursor.fetchall()
    
    print("\n=== RIEPILOGO TRIGGER WORKFLOW ===")
    for trigger in triggers:
        trigger_id, name, event_type, source, workflow_id, target_node_id, conditions_json, active = trigger
        
        # Converti conditions da JSON
        try:
            conditions = json.loads(conditions_json) if conditions_json else {}
        except:
            conditions = {"error": "Impossibile decodificare JSON"}
            
        # Verifica l'esistenza del workflow
        cursor.execute("SELECT name FROM workflows WHERE workflow_id = ?", (workflow_id,))
        workflow = cursor.fetchone()
        workflow_name = workflow[0] if workflow else "NON TROVATO"
        
        # Verifica l'esistenza del nodo target
        if target_node_id:
            cursor.execute("""
                SELECT name FROM workflow_nodes 
                WHERE workflow_id = ? AND node_id = ?
            """, (workflow_id, target_node_id))
            node = cursor.fetchone()
            node_name = node[0] if node else "NON TROVATO"
        else:
            node_name = "Non specificato"
        
        print(f"Trigger: {name} (ID: {trigger_id})")
        print(f"  Tipo evento: {event_type}")
        print(f"  Sorgente: {source}")
        print(f"  Workflow: {workflow_name} (ID: {workflow_id})")
        print(f"  Nodo target: {node_name} (ID: {target_node_id or 'None'})")
        print(f"  Attivo: {'Sì' if active else 'No'}")
        print(f"  Condizioni: {conditions}")
        print()

def find_input_nodes(conn):
    """Trova i nodi di input per ciascun workflow."""
    cursor = conn.cursor()
    
    # Ottieni tutti i workflow
    cursor.execute("SELECT workflow_id, name FROM workflows")
    workflows = cursor.fetchall()
    
    input_nodes_by_workflow = {}
    
    for workflow in workflows:
        workflow_id, workflow_name = workflow
        
        # Trova tutti i nodi con connessioni in ingresso
        cursor.execute("""
            SELECT DISTINCT to_node_id 
            FROM workflow_connections 
            WHERE workflow_id = ?
        """, (workflow_id,))
        nodes_with_input = {row[0] for row in cursor.fetchall()}
        
        # Trova tutti i nodi
        cursor.execute("""
            SELECT node_id, name, node_type 
            FROM workflow_nodes 
            WHERE workflow_id = ?
        """, (workflow_id,))
        nodes = cursor.fetchall()
        
        # Filtra per nodi senza connessioni in ingresso
        input_nodes = [node for node in nodes if node[0] not in nodes_with_input]
        
        # Salva i nodi di input per questo workflow
        input_nodes_by_workflow[workflow_id] = {
            "workflow_name": workflow_name,
            "input_nodes": input_nodes
        }
    
    return input_nodes_by_workflow

def find_matching_workflows_for_triggers(conn):
    """Trova i workflow più adatti per ciascun trigger in base al tipo di evento."""
    cursor = conn.cursor()
    
    # Ottieni tutti i trigger
    cursor.execute("""
        SELECT id, name, event_type, source, workflow_id, target_node_id
        FROM workflow_triggers
    """)
    triggers = cursor.fetchall()
    
    # Ottieni i nodi di input per ciascun workflow
    input_nodes_by_workflow = find_input_nodes(conn)
    
    # Mappa per i tipi di eventi ai workflow appropriati
    event_type_mapping = {
        "pdf_file_added": "pdf_document_add_workflow",
        "pdf_file_modified": "pdf_document_modify_workflow",
        "pdf_file_deleted": "pdf_document_delete_workflow",
        "record_updated": "pdf_metadata_update_workflow"
    }
    
    recommendations = {}
    
    for trigger in triggers:
        trigger_id, name, event_type, source, current_workflow_id, current_target_node_id = trigger
        
        # Verifica se il workflow corrente esiste
        cursor.execute("SELECT COUNT(*) FROM workflows WHERE workflow_id = ?", (current_workflow_id,))
        workflow_exists = cursor.fetchone()[0] > 0
        
        # Verifica se il nodo target esiste
        node_exists = False
        if current_target_node_id and workflow_exists:
            cursor.execute("""
                SELECT COUNT(*) FROM workflow_nodes 
                WHERE workflow_id = ? AND node_id = ?
            """, (current_workflow_id, current_target_node_id))
            node_exists = cursor.fetchone()[0] > 0
        
        # Se il workflow e il nodo esistono, potrebbe non essere necessario un aggiornamento
        if workflow_exists and (node_exists or current_target_node_id is None):
            # Ma controlliamo comunque se il target_node_id dovrebbe essere un nodo di input
            if current_target_node_id is None and current_workflow_id in input_nodes_by_workflow:
                input_nodes = input_nodes_by_workflow[current_workflow_id]["input_nodes"]
                if input_nodes:
                    # Se il workflow ha nodi di input ma il trigger non ne specifica uno, 
                    # suggeriamo di aggiornare il target_node_id
                    suggested_workflow_id = current_workflow_id
                    suggested_node_id = input_nodes[0][0]
                    suggested_node_name = input_nodes[0][1]
                    needs_update = True
                else:
                    # Il workflow non ha nodi di input, lasciamo invariato
                    suggested_workflow_id = current_workflow_id
                    suggested_node_id = current_target_node_id
                    suggested_node_name = "N/A"
                    needs_update = False
            else:
                # Workflow e nodo esistono, non serve aggiornamento
                suggested_workflow_id = current_workflow_id
                suggested_node_id = current_target_node_id
                suggested_node_name = "Mantenere esistente"
                needs_update = False
        else:
            # Il workflow o il nodo non esistono, dobbiamo trovare un'alternativa
            
            # Identifica il workflow consigliato in base al tipo di evento
            suggested_workflow_id = event_type_mapping.get(event_type)
            
            if not suggested_workflow_id:
                # Se non c'è una mappatura diretta, cerca workflow che contengono il tipo di evento nel nome
                for wf_id, wf_info in input_nodes_by_workflow.items():
                    if event_type.replace('_', '') in wf_id.replace('_', '').lower():
                        suggested_workflow_id = wf_id
                        break
            
            # Se ancora non abbiamo un workflow consigliato, usiamo un default
            if not suggested_workflow_id:
                # Per i tipi di eventi PDF, utilizziamo il workflow di aggiunta PDF come fallback
                if "pdf" in event_type.lower():
                    suggested_workflow_id = "pdf_document_add_workflow"
                else:
                    # Se proprio non troviamo corrispondenza, manteniamo il workflow corrente
                    suggested_workflow_id = current_workflow_id
            
            # Trova il nodo di input appropriato
            if suggested_workflow_id in input_nodes_by_workflow:
                input_nodes = input_nodes_by_workflow[suggested_workflow_id]["input_nodes"]
                suggested_node_id = input_nodes[0][0] if input_nodes else None
                suggested_node_name = input_nodes[0][1] if input_nodes else "Nessun nodo di input trovato"
            else:
                suggested_node_id = None
                suggested_node_name = "Workflow non trovato"
            
            needs_update = True
        
        recommendations[trigger_id] = {
            "trigger_name": name,
            "event_type": event_type,
            "current_workflow_id": current_workflow_id,
            "current_target_node_id": current_target_node_id,
            "suggested_workflow_id": suggested_workflow_id,
            "suggested_workflow_name": input_nodes_by_workflow.get(suggested_workflow_id, {}).get("workflow_name", "Sconosciuto"),
            "suggested_node_id": suggested_node_id,
            "suggested_node_name": suggested_node_name,
            "needs_update": needs_update
        }
    
    return recommendations

def update_triggers(conn, recommendations, dry_run=True):
    """Aggiorna i trigger in base alle raccomandazioni."""
    cursor = conn.cursor()
    
    print("\n=== AGGIORNAMENTO TRIGGER ===")
    
    for trigger_id, rec in recommendations.items():
        if rec["needs_update"]:
            print(f"Trigger: {rec['trigger_name']} (ID: {trigger_id})")
            print(f"  Modifiche necessarie: Sì")
            print(f"  Workflow attuale: {rec['current_workflow_id']} → Suggerito: {rec['suggested_workflow_id']} ({rec['suggested_workflow_name']})")
            print(f"  Nodo target attuale: {rec['current_target_node_id']} → Suggerito: {rec['suggested_node_id']} ({rec['suggested_node_name']})")
            
            if not dry_run:
                cursor.execute("""
                    UPDATE workflow_triggers
                    SET workflow_id = ?, target_node_id = ?
                    WHERE id = ?
                """, (rec['suggested_workflow_id'], rec['suggested_node_id'], trigger_id))
                print("  ✅ Aggiornato!")
            else:
                print("  ⚠️ Simulazione: nessuna modifica effettuata (dry_run=True)")
        else:
            print(f"Trigger: {rec['trigger_name']} (ID: {trigger_id})")
            print(f"  Modifiche necessarie: No (già corretto)")
        
        print()
    
    if not dry_run:
        conn.commit()
        print("✅ Tutti gli aggiornamenti sono stati salvati nel database!")
    else:
        print("⚠️ Simulazione completata. Eseguire nuovamente con dry_run=False per applicare le modifiche.")

def main():
    print(f"Analisi e correzione dei trigger nel database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"Errore: Database non trovato in {DB_PATH}")
        return
    
    # Connessione al database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Mostra riepilogo dei trigger
        print_trigger_summary(conn)
        
        # Trova raccomandazioni per l'aggiornamento
        recommendations = find_matching_workflows_for_triggers(conn)
        
        # Aggiorna i trigger (simulazione)
        update_triggers(conn, recommendations, dry_run=True)
        
        # Chiedi conferma per l'aggiornamento effettivo
        choice = input("\nVuoi applicare le modifiche consigliate? (s/n): ")
        if choice.lower() in ['s', 'si', 'sì', 'y', 'yes']:
            update_triggers(conn, recommendations, dry_run=False)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
