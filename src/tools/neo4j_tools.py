import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jUploader:
    def __init__(self, uri=None, user=None, password=None):
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = user or os.getenv("NEO4J_USER", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def upload_execution_graph(self, log_path: str):
        if not os.path.exists(log_path):
            print(f"Log file not found at {log_path}")
            return

        with open(log_path, 'r', encoding='utf-8') as f:
            try:
                graph_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from {log_path}: {e}")
                return

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        with self.driver.session() as session:
            for node in nodes:
                session.execute_write(self._create_node, node)
            for edge in edges:
                session.execute_write(self._create_edge, edge)
        
        print(f"Successfully uploaded {len(nodes)} nodes and {len(edges)} edges to Neo4j.")

    @staticmethod
    def _create_node(tx, data):
        query = (
            "MERGE (n:AgentExecution {id: $id}) "
            "SET n.agent = $agent, "
            "    n.timestamp = $timestamp, "
            "    n.inputs = $inputs, "
            "    n.outputs = $outputs"
        )
        tx.run(query, 
               id=data.get("id"), 
               agent=data.get("agent_name"),
               timestamp=data.get("timestamp"),
               inputs=json.dumps(data.get("inputs", {})),
               outputs=json.dumps(data.get("outputs", {})))

    @staticmethod
    def _create_edge(tx, data):
        query = (
            "MATCH (source:AgentExecution {id: $source_id}) "
            "MATCH (target:AgentExecution {id: $target_id}) "
            "MERGE (source)-[r:NEXT]->(target)"
        )
        tx.run(query, source_id=data.get("source"), target_id=data.get("target"))

def upload_to_neo4j(log_path: str = "artifacts/graph_execution_log.json", uri=None, user=None, password=None):
    print(f"Connecting to Neo4j to upload graph from {log_path}...")
    try:
        uploader = Neo4jUploader(uri, user, password)
        uploader.upload_execution_graph(log_path)
        uploader.close()
    except Exception as e:
        print(f"Failed to upload to Neo4j: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload Xage Execution Graph to Neo4j.")
    parser.add_argument("--log-path", type=str, default="artifacts/graph_execution_log.json", 
                        help="Path to the graph execution log JSON file.")
    parser.add_argument("--uri", type=str, help="Neo4j URI (overrides env var NEO4J_URI)")
    parser.add_argument("--user", type=str, help="Neo4j Username (overrides env var NEO4J_USER)")
    parser.add_argument("--password", type=str, help="Neo4j Password (overrides env var NEO4J_PASSWORD)")
    
    args = parser.parse_args()
    
    upload_to_neo4j(
        log_path=args.log_path, 
        uri=args.uri, 
        user=args.user, 
        password=args.password
    )

