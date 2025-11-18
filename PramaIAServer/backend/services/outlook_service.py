"""
Servizio per l'integrazione con Microsoft Graph API (Outlook)
"""
import logging
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class OutlookService:
    """
    Servizio per interagire con Microsoft Graph API per Outlook
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_email(self, to: str, subject: str, body: str, body_type: str = "Text") -> Dict[str, Any]:
        """
        Invia un'email tramite Outlook
        
        Args:
            to: Indirizzo email del destinatario
            subject: Oggetto dell'email
            body: Corpo dell'email
            body_type: Tipo di corpo (Text o HTML)
            
        Returns:
            Dict con il risultato dell'operazione
        """
        try:
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": body_type,
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to
                            }
                        }
                    ]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/me/sendMail",
                    headers=self.headers,
                    json=message
                ) as response:
                    if response.status == 202:  # Accepted
                        logger.info(f"Email inviata con successo a {to}")
                        return {
                            "success": True,
                            "message": "Email inviata con successo",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Errore nell'invio email: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Errore HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Errore nell'invio email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def read_emails(self, folder: str = "inbox", top: int = 10) -> Dict[str, Any]:
        """
        Legge le email da una cartella specifica
        
        Args:
            folder: Nome della cartella (inbox, sent, drafts, etc.)
            top: Numero massimo di email da recuperare
            
        Returns:
            Dict con la lista delle email
        """
        try:
            # Mappa dei nomi delle cartelle
            folder_mapping = {
                "inbox": "inbox",
                "sent": "sentitems",
                "drafts": "drafts",
                "deleted": "deleteditems"
            }
            
            folder_name = folder_mapping.get(folder, folder)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/me/mailFolders/{folder_name}/messages?$top={top}&$select=id,subject,from,receivedDateTime,bodyPreview,isRead",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        emails = []
                        
                        for email in data.get("value", []):
                            emails.append({
                                "id": email.get("id"),
                                "subject": email.get("subject"),
                                "from": email.get("from", {}).get("emailAddress", {}).get("address"),
                                "receivedDateTime": email.get("receivedDateTime"),
                                "bodyPreview": email.get("bodyPreview"),
                                "isRead": email.get("isRead")
                            })
                        
                        logger.info(f"Recuperate {len(emails)} email dalla cartella {folder}")
                        return {
                            "success": True,
                            "emails": emails,
                            "count": len(emails)
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Errore nel recupero email: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Errore HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Errore nel recupero email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_emails(self, query: str, folder: str = "inbox", top: int = 10) -> Dict[str, Any]:
        """
        Cerca email con una query specifica
        
        Args:
            query: Query di ricerca (es: "from:example@email.com")
            folder: Cartella dove cercare
            top: Numero massimo di risultati
            
        Returns:
            Dict con i risultati della ricerca
        """
        try:
            folder_mapping = {
                "inbox": "inbox",
                "sent": "sentitems", 
                "drafts": "drafts",
                "deleted": "deleteditems"
            }
            
            folder_name = folder_mapping.get(folder, folder)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/me/mailFolders/{folder_name}/messages?$search=\"{query}\"&$top={top}&$select=id,subject,from,receivedDateTime,bodyPreview,isRead",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        emails = []
                        
                        for email in data.get("value", []):
                            emails.append({
                                "id": email.get("id"),
                                "subject": email.get("subject"),
                                "from": email.get("from", {}).get("emailAddress", {}).get("address"),
                                "receivedDateTime": email.get("receivedDateTime"),
                                "bodyPreview": email.get("bodyPreview"),
                                "isRead": email.get("isRead")
                            })
                        
                        logger.info(f"Trovate {len(emails)} email con query '{query}'")
                        return {
                            "success": True,
                            "emails": emails,
                            "count": len(emails),
                            "query": query
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Errore nella ricerca email: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Errore HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Errore nella ricerca email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def execute_outlook_node(config: Dict[str, Any], input_data: Any, access_token: str) -> Dict[str, Any]:
        """
        Esegue un nodo Outlook in base alla configurazione
        
        Args:
            config: Configurazione del nodo
            input_data: Dati di input dal nodo precedente
            access_token: Token di accesso Microsoft Graph
            
        Returns:
            Dict con il risultato dell'esecuzione
        """
        service = OutlookService(access_token)
        action = config.get("action", "send")
        
        try:
            if action == "send":
                # Per l'invio, usa i dati di input se disponibili per body
                to = config.get("to", "")
                subject = config.get("subject", "")
                body = config.get("body", "")
                
                # Se c'è input_data, usalo come corpo o appendilo
                if input_data:
                    if body:
                        body = f"{body}\n\n{input_data}"
                    else:
                        body = str(input_data)
                
                return await service.send_email(to, subject, body)
                
            elif action == "read":
                folder = config.get("folder", "inbox")
                top = config.get("top", 10)
                return await service.read_emails(folder, top)
                
            elif action == "search":
                query = config.get("searchQuery", "")
                folder = config.get("folder", "inbox")
                top = config.get("top", 10)
                return await service.search_emails(query, folder, top)
                
            else:
                return {
                    "success": False,
                    "error": f"Azione non supportata: {action}"
                }
                
        except Exception as e:
            logger.error(f"Errore nell'esecuzione nodo Outlook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
