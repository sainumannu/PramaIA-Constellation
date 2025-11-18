import re
from fastapi import APIRouter, HTTPException, Response
import httpx
import logging
import time
import functools
import json
from backend.engine.node_registry import NodeRegistry
from backend.core.config import PDK_SERVER_URL

# Creiamo un router senza prefisso
router = APIRouter(tags=["pdk"])
logger = logging.getLogger(__name__)

# Configurazione livello di logging per maggiore visibilità
logger.setLevel(logging.DEBUG)

# Ottieni l'istanza del registro nodi
node_registry = NodeRegistry()

logger.info(f"🔌 PDK Server configurato su: {PDK_SERVER_URL}")

# Helper per misurare il tempo di esecuzione (usato nei log)
def log_execution_time(func):
    @functools.wraps(func)  # Preserva la firma della funzione originale
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"⏱️ Inizio esecuzione {func.__name__}")
        result = await func(*args, **kwargs)
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"⏱️ {func.__name__} completato in {execution_time}ms")
        return result
    return wrapper

# (placeholder consentiti: li mostriamo così come arrivano dal plugin)

# Funzione per verificare se un'icona è valida
def is_valid_icon(icon):
    # Accetta stringhe non vuote che non contengano caratteri di sostituzione
    if not icon or not isinstance(icon, str):
        return False
    if '�' in icon:
        return False
    return len(icon.strip()) > 0

# Funzione per riparare un'icona
def fix_icon(node_name, icon):
    """Restituisce l'icona originale se valida; altrimenti usa un default minimale.
    Policy: nessun fallback deterministico per nome. I placeholder vanno bene.
    """
    if is_valid_icon(icon):
        return icon
    # Default minimale se mancante/corrotta
    return '🧩'

@router.get("/pdk/plugins")
@log_execution_time
async def get_plugins():
    logger.info("🔍 [ENDPOINT] /api/workflows/pdk/plugins chiamato")
    logger.info(f"🔌 Tentativo connessione a {PDK_SERVER_URL}/api/plugins")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PDK_SERVER_URL}/api/plugins")
            response_data = response.json()
            plugins = response_data.get("plugins", [])
            logger.info(f"Ricevuta risposta dal PDK server: {len(plugins)} plugin")
            
            result_plugins = []
            for plugin_info in plugins:
                plugin_id = plugin_info.get("id")
                
                # Verifica la presenza dei nodi
                nodes = plugin_info.get("nodes", [])
                logger.info(f"Nodi trovati nel plugin {plugin_id}: {len(nodes)}")
                
                # Registra i nodi nel NodeRegistry
                registered_nodes = []
                for node in nodes:
                    try:
                        node_type = node_registry.register_pdk_node(plugin_id, node)
                        # Aggiorna il tipo del nodo con quello registrato
                        node["type"] = node_type
                        registered_nodes.append(node)
                    except Exception as e:
                        logger.error(f"Errore durante la registrazione del nodo PDK: {e}")
                
                # Aggiungi il plugin al risultato
                result_plugins.append({
                    "id": plugin_id,
                    "name": plugin_info.get("name", "Unnamed Plugin"),
                    "description": plugin_info.get("description", ""),
                    "version": plugin_info.get("version", "1.0.0"),
                    "nodes": registered_nodes
                })
            
            # Convertiamo il formato per corrispondere a quello atteso dal frontend
            logger.info(f"Invio al frontend: {result_plugins}")
            return result_plugins
        except Exception as e:
            logger.error(f"Errore nella richiesta al PDK server: {e}")
            raise HTTPException(status_code=502, detail=str(e))

@router.get("/pdk/plugins/{plugin_id}")
@log_execution_time
async def get_plugin_details(plugin_id: str):
    logger.info(f"🔍 [ENDPOINT] /api/workflows/pdk/plugins/{plugin_id} chiamato")
    logger.info(f"🔌 Tentativo connessione a {PDK_SERVER_URL}/api/plugins/{plugin_id}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PDK_SERVER_URL}/api/plugins/{plugin_id}")
            if response.status_code != 200:
                logger.error(f"❌ Errore richiesta plugin: HTTP {response.status_code}")
                raise HTTPException(status_code=502, detail=f"PDK server error: {response.status_code}")
            
            plugin_data = response.json()
            
            # Estrae lo schema di configurazione
            config_schema = plugin_data.get("configSchema", {})
            
            # Formatta lo schema per essere compatibile con rjsf
            formatted_schema = {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "title": "Testo di input",
                        "description": "Il testo da processare"
                    },
                    "config": config_schema
                },
                "required": ["input"]
            }
            
            return {
                **plugin_data,
                "configSchema": formatted_schema
            }
        except Exception as e:
            logger.error(f"Errore nella richiesta al PDK server: {e}")
            raise HTTPException(status_code=502, detail=str(e))

@router.post("/pdk/plugins/{plugin_id}/execute")
@log_execution_time
async def execute_plugin(plugin_id: str, data: dict):
    logger.info(f"🔍 [ENDPOINT] /api/workflows/pdk/plugins/{plugin_id}/execute chiamato")
    logger.info(f"📦 Payload ricevuto: {data}")
    
    async with httpx.AsyncClient() as client:
        try:
            # Estrai input e config dal payload ricevuto
            input_text = data.get("input", "")
            config = data.get("config", {})
            
            # Prepara il payload per il server PDK
            pdk_payload = {
                "nodeId": "default",  # Usa il nodeId appropriato se disponibile
                "inputs": {"input": input_text},
                "config": config
            }
            
            logger.info(f"🚀 Invio richiesta al PDK server con payload: {pdk_payload}")
            logger.info(f"🔌 Tentativo connessione a {PDK_SERVER_URL}/plugins/{plugin_id}/execute")
            
            response = await client.post(f"{PDK_SERVER_URL}/plugins/{plugin_id}/execute", json=pdk_payload)
            response_data = response.json()
            
            logger.info(f"✅ Risposta ricevuta dal server PDK: {response_data}")
            return response_data
        except Exception as e:
            logger.error(f"Errore nell'esecuzione del plugin: {e}")
            raise HTTPException(status_code=502, detail=str(e))

@router.get("/pdk-nodes", name="get_pdk_nodes")
@log_execution_time
async def get_workflow_pdk_nodes():
    """
    Ritorna i nodi PDK disponibili per la costruzione dei workflow
    """
    print("\n🚀 [PRAMA-SERVER] ================== ENDPOINT /pdk-nodes CHIAMATO ==================")
    logger.info("🔍 [PRAMA-SERVER] pdk-nodes chiamato")
    logger.info("📋 [PRAMA-SERVER] Recupero nodi PDK dal registry per workflow editor")
    
    # Ottieni nodi dai plugin reali
    available_nodes = []
    registered_node_types = set()  # Per tenere traccia dei nodi già aggiunti ed evitare duplicati
    
    try:
        # Prima prova a caricare i nodi dal server PDK
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"🔌 [PRAMA-SERVER] Tentativo connessione al server PDK: {PDK_SERVER_URL}/api/nodes")
                response = await client.get(f"{PDK_SERVER_URL}/api/nodes")
                
                if response.status_code == 200:
                    print(f"✅ [PRAMA-SERVER] Response status: {response.status_code}")
                    print(f"🔡 [PRAMA-SERVER] Response headers: {dict(response.headers)}")
                    
                    # Log del contenuto raw della risposta
                    raw_content = response.content
                    print(f"📦 [PRAMA-SERVER] Raw response length: {len(raw_content)} bytes")
                    print(f"📦 [PRAMA-SERVER] Raw response preview: {raw_content[:300]}...")
                    
                    # Log del testo della risposta
                    text_content = response.text
                    print(f"📄 [PRAMA-SERVER] Text response length: {len(text_content)} chars")
                    print(f"📄 [PRAMA-SERVER] Text response preview: {text_content[:300]}...")
                    
                    nodes_data = response.json()
                    pdk_nodes = nodes_data.get("nodes", [])
                    print(f"✅ [PRAMA-SERVER] JSON parsed successfully, found {len(pdk_nodes)} nodes")
                    
                    # Debug delle prime 3 icone ricevute
                    for i, node in enumerate(pdk_nodes[:3]):
                        icon = node.get("icon", "NO_ICON")
                        print(f"\n🔍 [PRAMA-SERVER] === NODE {i + 1} RECEIVED ===")
                        print(f"🎯 [PRAMA-SERVER] Name: {node.get('name', 'NO_NAME')}")
                        print(f"🎨 [PRAMA-SERVER] Icon RECEIVED: '{icon}'")
                        print(f"🔢 [PRAMA-SERVER] Icon char codes: [{','.join([str(ord(c)) for c in icon]) if icon != 'NO_ICON' else 'NO_ICON'}]")
                        print(f"🌟 [PRAMA-SERVER] Icon length: {len(icon) if icon != 'NO_ICON' else 0}")
                        print(f"🔤 [PRAMA-SERVER] Icon type: {type(icon)}")
                    
                    # Aggiungi i nodi dal server PDK
                    for node in pdk_nodes:
                        plugin_id = node.get("pluginId", "unknown")
                        node_id = node.get("id", "unknown")
                        node_type = f"{plugin_id}.{node_id}"
                        
                        # Evita duplicati
                        if node_type in registered_node_types:
                            logger.info(f"⚠️ [PRAMA-SERVER] Nodo duplicato ignorato: {node_type}")
                            continue
                        
                        try:
                            # Registra nel NodeRegistry
                            registered_type = node_registry.register_pdk_node(plugin_id, node)
                            
                            # Prepara nodo per il frontend
                            config_schema = node.get("configSchema", {})
                            node_name = node.get("name", "Unnamed Node")
                            original_icon = node.get("icon", "🔌")
                            
                            # NUOVA LOGICA - Verifica e corregge l'icona
                            fixed_icon = fix_icon(node_name, original_icon)
                            if original_icon != fixed_icon:
                                print(f"🔄 [PRAMA-SERVER] Fixed icon for {node_name}: '{original_icon}' -> '{fixed_icon}'")
                            
                            # Verifica che lo schema di configurazione sia valido
                            has_valid_schema = (
                                config_schema and
                                isinstance(config_schema, dict) and
                                "properties" in config_schema and
                                isinstance(config_schema["properties"], dict) and
                                bool(config_schema["properties"])  # True se non è vuoto
                            )
                            
                            # Log dettagliato dello schema di configurazione
                            if has_valid_schema:
                                properties = list(config_schema["properties"].keys())
                                logger.info(f"⚙️ [PRAMA-SERVER] Nodo {node.get('name')} ha uno schema di configurazione valido con {len(properties)} proprietà")
                                logger.info(f"⚙️ [PRAMA-SERVER] Proprietà: {', '.join(properties)}")
                            else:
                                logger.info(f"⚠️ [PRAMA-SERVER] Nodo {node.get('name')} non ha uno schema di configurazione valido, creazione fallback")
                            
                            # Solo se lo schema non è valido, creiamo uno schema di fallback
                            if not has_valid_schema:
                                config_schema = {
                                    "title": f"Configurazione {node.get('name', 'Nodo')}",
                                    "type": "object",
                                    "properties": {
                                        "description": {
                                            "type": "string",
                                            "title": "Descrizione",
                                            "description": "Descrizione personalizzata per questo nodo",
                                            "default": node.get("description", "")
                                        },
                                        "custom_name": {
                                            "type": "string",
                                            "title": "Nome personalizzato",
                                            "description": "Nome personalizzato per identificare questo nodo",
                                            "default": node.get("name", "")
                                        }
                                    }
                                }
                                
                                # Formatta il nome della categoria in modo più leggibile
                                # Cerca prima il display_name nel plugin, poi nel nodo, poi crea un nome formattato
                                plugin_display_name = node.get("pluginDisplayName", "")
                                if not plugin_display_name:
                                    # Cerca il display_name nel plugin parent
                                    response = None
                                    try:
                                        plugin_info_url = f"{PDK_SERVER_URL}/api/plugins/{plugin_id}"
                                        plugin_response = await client.get(plugin_info_url, timeout=2.0)
                                        if plugin_response.status_code == 200:
                                            plugin_data = plugin_response.json()
                                            plugin_display_name = plugin_data.get("display_name", "")
                                            logger.info(f"✅ Trovato display_name del plugin: '{plugin_display_name}'")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Impossibile ottenere display_name del plugin: {e}")
                                    
                                    # Se ancora non trovato, formatta il nome del plugin
                                    if not plugin_display_name:
                                        plugin_name = node.get("pluginName", plugin_id)
                                        # Sostituisci - e _ con spazi e capitalizza le parole
                                        plugin_display_name = ' '.join(word.capitalize() for word in re.split(r'[-_]', plugin_name))
                                        logger.info(f"⚠️ Generato display_name: '{plugin_display_name}' da '{plugin_name}'")
                                
                                # Ottieni la categoria dal nodo
                                node_category = node.get("category", "")
                                
                                # Se non c'è categoria nel nodo, usa il display_name del plugin
                                if not node_category:
                                    # Usa il nome formattato del plugin come categoria
                                    node_category = plugin_display_name
                                    logger.info(f"⚠️ Nodo {node.get('name')} senza categoria, utilizzo plugin display name: {node_category}")
                                
                                node_info = {
                                    "type": registered_type,
                                    "name": node.get("name", "Unnamed Node"),
                                    "display_name": node.get("name", "Unnamed Node"),
                                    "description": node.get("description", ""),
                                    "icon": fixed_icon,  # Usa l'icona corretta
                                    "plugin_id": plugin_id,
                                    "plugin_name": node.get("pluginName", plugin_id),
                                    "plugin_display_name": plugin_display_name,
                                    "plugin_version": "1.0.0",
                                    "group": node_category,  # Usa la categoria del nodo
                                    "category": node_category,
                                    "configSchema": config_schema,  # Usa lo schema generato o originale
                                    "defaultConfig": node.get("defaultConfig", {}),
                                    "inputs": node.get("inputs", []),
                                    "outputs": node.get("outputs", [])
                                }
                                
                                # Debug dell'icona dopo la preparazione del nodo
                                final_icon = node_info["icon"]
                                print(f"🎯 [PRAMA-SERVER] Final icon in node_info: '{final_icon}'")
                                print(f"🔢 [PRAMA-SERVER] Final char codes: [{','.join([str(ord(c)) for c in final_icon])}]")
                                print(f"📄 [PRAMA-SERVER] Icon changed: {original_icon != final_icon}")
                                
                                available_nodes.append(node_info)
                                registered_node_types.add(node_type)
                                logger.info(f"📌 [PRAMA-SERVER] Registrato nodo PDK diretto: {registered_type}")
                        except Exception as e:
                            logger.error(f"❌ [PRAMA-SERVER] Errore registrazione nodo PDK: {e}")
                else:
                    logger.warning(f"⚠️ Endpoint /api/nodes non disponibile: HTTP {response.status_code}")
                    # Prova con l'approccio alternativo tramite /api/plugins
                    logger.info(f"🔌 Tentativo alternativo con: {PDK_SERVER_URL}/api/plugins")
                    response = await client.get(f"{PDK_SERVER_URL}/api/plugins")
                    
                    if response.status_code == 200:
                        plugin_data = response.json()
                        plugins = plugin_data.get("plugins", [])
                        logger.info(f"✅ Connessione PDK riuscita, trovati {len(plugins)} plugin")
                        
                        # Registra i nodi da tutti i plugin
                        for plugin in plugins:
                            plugin_id = plugin.get("id")
                            plugin_name = plugin.get("name")
                            nodes = plugin.get("nodes", [])
                            logger.info(f"📌 Plugin {plugin_name} ({plugin_id}): {len(nodes)} nodi")
                            
                            for node in nodes:
                                node_id = node.get("id", "unknown")
                                node_type = f"{plugin_id}.{node_id}"
                                
                                # Evita duplicati
                                if node_type in registered_node_types:
                                    logger.info(f"⚠️ Nodo duplicato ignorato: {node_type}")
                                    continue
                                
                                try:
                                    registered_type = node_registry.register_pdk_node(plugin_id, node)
                                    
                                    # NUOVA LOGICA - Verifica e corregge l'icona
                                    node_name = node.get("name", "Unnamed Node")
                                    original_icon = node.get("icon", "🔌")
                                    fixed_icon = fix_icon(node_name, original_icon)
                                    
                                    # Formatta il nome della categoria in modo più leggibile
                                    # Cerca prima il display_name nel plugin
                                    plugin_display_name = ""
                                    try:
                                        plugin_info_url = f"{PDK_SERVER_URL}/api/plugins/{plugin_id}"
                                        plugin_response = await client.get(plugin_info_url, timeout=2.0)
                                        if plugin_response.status_code == 200:
                                            plugin_data = plugin_response.json()
                                            plugin_display_name = plugin_data.get("display_name", "")
                                            logger.info(f"✅ Trovato display_name del plugin: '{plugin_display_name}'")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Impossibile ottenere display_name del plugin: {e}")
                                    
                                    # Se non trovato, formatta il nome del plugin
                                    if not plugin_display_name:
                                        plugin_display_name = ' '.join(word.capitalize() for word in re.split(r'[-_]', plugin_name))
                                    
                                    # Ottieni la categoria dal nodo
                                    node_category = node.get("category", "")
                                    
                                    # Se non c'è categoria nel nodo, usa il display_name del plugin
                                    if not node_category:
                                        # Usa il nome formattato del plugin come categoria
                                        node_category = plugin_display_name
                                        logger.info(f"⚠️ Nodo {node.get('name')} senza categoria, utilizzo plugin display name: {node_category}")
                                    
                                    node_info = {
                                        "type": registered_type,
                                        "name": node.get("name", "Unnamed Node"),
                                        "display_name": node.get("name", "Unnamed Node"),
                                        "description": node.get("description", ""),
                                        "icon": fixed_icon,  # Usa l'icona corretta
                                        "plugin_id": plugin_id,
                                        "plugin_name": plugin_name,
                                        "plugin_display_name": plugin_display_name,
                                        "plugin_version": "1.0.0",
                                        "group": node_category,  # Usa la categoria del nodo
                                        "category": node_category,
                                        "configSchema": node.get("configSchema", {}),  # Frontend si aspetta camelCase
                                        "defaultConfig": node.get("defaultConfig", {}),
                                        "inputs": node.get("inputs", []),
                                        "outputs": node.get("outputs", [])
                                    }
                                    
                                    available_nodes.append(node_info)
                                    registered_node_types.add(node_type)
                                    logger.info(f"📌 Registrato nodo PDK: {registered_type}")
                                except Exception as e:
                                    logger.error(f"❌ Errore registrazione nodo PDK: {e}")
                    else:
                        logger.warning(f"⚠️ Server PDK non disponibile: HTTP {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Impossibile connettersi al server PDK: {e}")
        
        # Fallback disabilitato: non aggiungiamo nodi legacy dal NodeRegistry
        if len(available_nodes) == 0:
            logger.warning("⚠️ Nessun nodo PDK disponibile (server PDK non raggiungibile o nessun plugin attivo). Nessun nodo legacy verrà incluso.")
        
        logger.info(f"📊 [PRAMA-SERVER] Totale nodi PDK disponibili: {len(available_nodes)}")
        logger.info(f"📋 [PRAMA-SERVER] Nomi nodi disponibili: {[node['name'] for node in available_nodes]}")
        
        # DEBUG FINALE - Verifica le icone nella risposta finale
        print(f"\n🎯 [PRAMA-SERVER] =============== FINAL RESPONSE DEBUG ===============")
        print(f"📊 [PRAMA-SERVER] Nodes to return: {len(available_nodes)}")
        
        for i, node in enumerate(available_nodes[:5]):  # Prime 5 per debug
            icon = node.get("icon", "NO_ICON")
            print(f"📌 [PRAMA-SERVER] Node {i+1} FINAL: '{node['name']}' icon: '{icon}' chars: [{','.join([str(ord(c)) for c in icon]) if icon != 'NO_ICON' else 'NO_ICON'}]")
        
        response_data = {"nodes": available_nodes}
        
        # Serializza in JSON per debug
        json_string = json.dumps(response_data, ensure_ascii=False)
        print(f"🔤 [PRAMA-SERVER] Response JSON length: {len(json_string)}")
        print(f"🔤 [PRAMA-SERVER] Response JSON preview: {json_string[:400]}...")
        
        # Cerca icone nel JSON
        icon_matches = re.findall(r'"icon":"([^"]*)"', json_string)
        if icon_matches:
            print(f"🔤 [PRAMA-SERVER] Icons in JSON ({len(icon_matches)}):")
            for i, icon in enumerate(icon_matches[:5]):
                print(f"🔤 [PRAMA-SERVER] JSON Icon {i+1}: '{icon}' chars: [{','.join([str(ord(c)) for c in icon])}]")
        
        logger.info(f"✅ [PRAMA-SERVER] Restituzione nodi al workflow editor completata")
        print(f"🏁 [PRAMA-SERVER] =============== END RESPONSE DEBUG ===============\n")
        
        # Imposta l'header di Content-Type per garantire l'encoding UTF-8
        # Utilizziamo JSONResponse invece di return per poter impostare l'header
        return Response(
            content=json_string,
            media_type="application/json; charset=utf-8"
        )
    
    except Exception as e:
        logger.error(f"❌ Errore nel recupero dei nodi PDK: {e}")
        raise HTTPException(status_code=500, detail=str(e))
