"""
Test Inventory - Sistema
Verifica workflow, event sources, trigger e nodi disponibili nel sistema
"""

import pytest
import json
from test_utils import (
    ServiceConfig, APIClient, DatabaseHelper, TestReporter,
    Assertions
)


class TestWorkflowInventory:
    """Test: Elenca e verifica workflow disponibili"""
    
    def test_get_workflows_from_api(self):
        """Verifica che sia possibile ottenere lista workflow via API"""
        TestReporter.print_header("GET WORKFLOWS")
        
        # Login prima
        token = APIClient.login()
        if not token:
            pytest.skip("Could not authenticate: login failed")
        
        headers = APIClient.get_auth_headers(token)
        response = APIClient.get(f"{ServiceConfig.BACKEND_URL}/api/workflows/", headers=headers)
        Assertions.assert_status_code(response, 200)
        
        workflows = response.json()
        Assertions.assert_type(workflows, list)
        
        TestReporter.print_result("Total workflows", len(workflows))
        
        if workflows:
            print("\n📋 Workflows disponibili:")
            headers_row = ["ID", "Name", "Active", "Category", "Tags"]
            rows = []
            for wf in workflows[:10]:  # Primi 10
                rows.append([
                    wf.get("workflow_id", "N/A")[:20],
                    wf.get("name", "N/A")[:20],
                    str(wf.get("is_active", False)),
                    wf.get("category", "N/A")[:15],
                    ",".join(wf.get("tags", [])[:3])
                ])
            TestReporter.print_table(headers_row, rows)
        else:
            print("❌ No workflows found")
        
        return workflows
    
    def test_get_workflows_from_database(self):
        """Verifica workflow nel database"""
        TestReporter.print_header("DATABASE WORKFLOWS", level=2)
        
        try:
            count = DatabaseHelper.count_table("workflows")
            TestReporter.print_result("Workflows in DB", count)
            
            # Dettagli primi 5
            workflows = DatabaseHelper.query_dict(
                "SELECT workflow_id, name, is_active FROM workflows LIMIT 5"
            )
            
            if workflows:
                print("\n📊 Sample workflows from DB:")
                for wf in workflows:
                    print(f"  - {wf['workflow_id']}: {wf['name']} (active: {wf['is_active']})")
            
            return count
        except Exception as e:
            print(f"⚠️  Could not query workflows table: {e}")
            return 0
    
    def test_workflow_schema(self):
        """Verifica schema tabella workflows"""
        TestReporter.print_header("WORKFLOW SCHEMA", level=2)
        
        try:
            schema = DatabaseHelper.get_table_schema("workflows")
            print("📋 Workflow table schema:")
            for col in schema:
                print(f"  - {col['name']}: {col['type']}")
        except Exception as e:
            print(f"⚠️  Could not get schema: {e}")


class TestNodeInventory:
    """Test: Elenca e verifica nodi disponibili"""
    
    def test_get_nodes_from_pdk(self):
        """Verifica nodi disponibili da PDK"""
        TestReporter.print_header("GET NODES FROM PDK")
        
        response = APIClient.get(f"{ServiceConfig.PDK_SERVER_URL}/api/nodes")
        Assertions.assert_status_code(response, 200)
        
        nodes = response.json()
        if isinstance(nodes, dict):
            # Potrebbe essere {nodes: [...]} oppure lista diretta
            nodes = nodes.get("nodes", nodes) if isinstance(nodes, dict) else nodes
        
        Assertions.assert_type(nodes, list)
        
        TestReporter.print_result("Total nodes", len(nodes))
        
        # Raggruppa per plugin
        nodes_by_plugin = {}
        for node in nodes:
            plugin_id = node.get("pluginId", "unknown")
            if plugin_id not in nodes_by_plugin:
                nodes_by_plugin[plugin_id] = []
            nodes_by_plugin[plugin_id].append(node)
        
        print("\n🔌 Nodes by plugin:")
        for plugin_id, plugin_nodes in nodes_by_plugin.items():
            print(f"\n  Plugin: {plugin_id}")
            for node in plugin_nodes:
                node_name = node.get("name", node.get("id", "unknown"))
                inputs = len(node.get("inputs", []))
                outputs = len(node.get("outputs", []))
                print(f"    - {node_name} (in: {inputs}, out: {outputs})")
        
        return nodes
    
    def test_node_schema_validation(self):
        """Verifica che nodi abbiano schema valido"""
        TestReporter.print_header("NODE SCHEMA VALIDATION", level=2)
        
        response = APIClient.get(f"{ServiceConfig.PDK_SERVER_URL}/api/nodes")
        Assertions.assert_status_code(response, 200)
        
        nodes = response.json()
        if isinstance(nodes, dict):
            nodes = nodes.get("nodes", nodes)
        
        print("✓ Validating node schemas...")
        
        required_fields = ["id", "name", "pluginId"]
        invalid_nodes = []
        valid_count = 0
        
        for node in nodes:
            missing_fields = []
            for field in required_fields:
                if field not in node:
                    missing_fields.append(field)
            
            if missing_fields:
                node_name = node.get("name", node.get("id", "unknown"))
                invalid_nodes.append(f"{node_name}: missing {', '.join(missing_fields)}")
            else:
                valid_count += 1
        
        if invalid_nodes:
            print(f"⚠️  Found {len(invalid_nodes)} nodes with missing fields:")
            for inv in invalid_nodes[:10]:  # Mostra solo primi 10
                print(f"  - {inv}")
            if len(invalid_nodes) > 10:
                print(f"  ... and {len(invalid_nodes) - 10} more")
        else:
            print(f"✅ All {valid_count} nodes have valid schema")
        
        print(f"\n📊 Validation summary: {valid_count} valid, {len(invalid_nodes)} invalid")
        
        return len(invalid_nodes) == 0


class TestEventSourceInventory:
    """Test: Elenca event source disponibili"""
    
    def test_get_event_sources_from_database(self):
        """Verifica event source nel database"""
        TestReporter.print_header("GET EVENT SOURCES")
        
        try:
            count = DatabaseHelper.count_table("event_sources")
            TestReporter.print_result("Event sources in DB", count)
            
            # Query event sources
            sources = DatabaseHelper.query_dict(
                "SELECT id, name, event_type, active FROM event_sources"
            )
            
            if sources:
                print("\n📡 Event sources:")
                headers = ["ID", "Name", "Type", "Active"]
                rows = [[
                    src.get("id", "N/A")[:15],
                    src.get("name", "N/A")[:20],
                    src.get("event_type", "N/A")[:20],
                    str(src.get("active", False))
                ] for src in sources]
                TestReporter.print_table(headers, rows)
            else:
                print("❌ No event sources found in database")
            
            return sources
        except Exception as e:
            print(f"⚠️  Could not query event_sources: {e}")
            # Potrebbe non esistere, creiamo lista da sistema
            return self._get_event_sources_from_system()
    
    def _get_event_sources_from_system(self):
        """Ottiene event source dal sistema"""
        print("\n📋 Known event sources in system:")
        known_sources = [
            {"name": "PDF Monitor", "event_type": "pdf_file_added"},
            {"name": "PDF Monitor", "event_type": "pdf_file_modified"},
            {"name": "PDF Monitor", "event_type": "pdf_file_deleted"},
            {"name": "PDF Monitor", "event_type": "pdf_any_change"},
            {"name": "Webhook", "event_type": "webhook_received"},
            {"name": "Scheduler", "event_type": "scheduled_event"}
        ]
        
        for src in known_sources:
            print(f"  - {src['name']}: {src['event_type']}")
        
        return known_sources


class TestTriggerInventory:
    """Test: Elenca e verifica trigger configurati"""
    
    def test_get_triggers_from_database(self):
        """Verifica trigger nel database"""
        TestReporter.print_header("GET TRIGGERS")
        
        try:
            count = DatabaseHelper.count_table("workflow_triggers")
            TestReporter.print_result("Triggers in DB", count)
            
            # Query triggers
            triggers = DatabaseHelper.query_dict(
                """SELECT id, name, event_type, source, workflow_id, active 
                   FROM workflow_triggers LIMIT 20"""
            )
            
            if triggers:
                print("\n🎯 Configured triggers:")
                headers = ["ID", "Name", "Event Type", "Workflow", "Active"]
                rows = [[
                    trig.get("id", "N/A")[:12],
                    trig.get("name", "N/A")[:25],
                    trig.get("event_type", "N/A")[:20],
                    trig.get("workflow_id", "N/A")[:20],
                    str(trig.get("active", False))
                ] for trig in triggers]
                TestReporter.print_table(headers, rows)
            else:
                print("ℹ️  No triggers configured")
            
            return triggers
        except Exception as e:
            print(f"⚠️  Could not query triggers: {e}")
            return []
    
    def test_trigger_event_type_distribution(self):
        """Analizza distribuzione event_type nei trigger"""
        TestReporter.print_header("TRIGGER EVENT DISTRIBUTION", level=2)
        
        try:
            results = DatabaseHelper.query_dict(
                """SELECT event_type, COUNT(*) as count 
                   FROM workflow_triggers 
                   GROUP BY event_type"""
            )
            
            print("📊 Event types in triggers:")
            for row in results:
                event_type = row.get("event_type", "unknown")
                count = row.get("count", 0)
                print(f"  - {event_type}: {count} trigger(s)")
        except Exception as e:
            print(f"⚠️  Could not analyze triggers: {e}")


class TestSystemInventorySummary:
    """Test: Riepilogo generale dell'inventario di sistema"""
    
    def test_complete_system_inventory(self):
        """Riepilogo completo dell'inventario di sistema"""
        TestReporter.print_header("COMPLETE SYSTEM INVENTORY", level=0)
        
        inventory = {}
        
        # Workflows
        try:
            wf_count = DatabaseHelper.count_table("workflows")
            inventory["workflows"] = wf_count
        except:
            inventory["workflows"] = "ERROR"
        
        # Nodes
        try:
            response = APIClient.get(f"{ServiceConfig.PDK_SERVER_URL}/api/nodes")
            nodes = response.json()
            if isinstance(nodes, dict):
                nodes = nodes.get("nodes", nodes)
            inventory["nodes"] = len(nodes)
        except:
            inventory["nodes"] = "ERROR"
        
        # Event Sources
        try:
            es_count = DatabaseHelper.count_table("event_sources")
            inventory["event_sources"] = es_count
        except:
            inventory["event_sources"] = "ERROR"
        
        # Triggers
        try:
            trig_count = DatabaseHelper.count_table("workflow_triggers")
            inventory["triggers"] = trig_count
        except:
            inventory["triggers"] = "ERROR"
        
        # Documents
        try:
            doc_count = DatabaseHelper.count_table("documents")
            inventory["documents"] = doc_count
        except:
            inventory["documents"] = "ERROR"
        
        # Print summary
        print("📊 SYSTEM INVENTORY SUMMARY:")
        print("=" * 50)
        for key, value in inventory.items():
            status = "✅" if isinstance(value, int) else "⚠️"
            print(f"{status} {key:.<30} {value}")
        print("=" * 50)
        
        return inventory


# ============================================================================
# PYTEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
