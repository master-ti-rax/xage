"""Asset Manager Agent for retrieving required knowledge and models."""

from __future__ import annotations

import os
import csv
import math
import ast
from pathlib import Path
from typing import Any

import requests
from langchain_ollama import OllamaEmbeddings

from src.tools.langchain_tools import query_knowledge_graph
from src.tools.sketchfab_tools import SketchfabClient
from dotenv import load_dotenv

load_dotenv()

class AssetManager:
    """Asset Manager pipeline for retrieving required resources.
    
    The asset manager receives an execution plan with required_knowledge and
    required_assets lists, then retrieves documentation and 3D models through
    a two-stage pipeline: local search followed by advanced search.
    """


    def __init__(
            self,
            models_path: Path = Path(os.getenv("3D_MODELS_PATH", "./assets")),
            sketchfab_token: str | None = os.getenv("SKETCHFAB_TOKEN", None),
    ) -> None:
        """Initialize the Asset Manager Agent."""

        self.models_path = models_path
        self.sketchfab_token = sketchfab_token

    def retrieve(
        self,
        assets: list[dict[str, Any]],
        knowledge: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Retrieve required knowledge and assets through two-stage pipeline."""

        retrieved_knowledge = self._retrieve_knowledge(knowledge)
        retrieved_models = self._retrieve_resources(assets)
        
        return {
            "retrieved_knowledge": retrieved_knowledge,
            "retrieved_models": retrieved_models,
        }

    def _retrieve_knowledge(self, knowledge_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Retrieve knowledge through local search then advanced search if needed."""
        retrieved = []
        
        for knowledge_item in knowledge_list:
            #local search
            pass
            
            #if not local_result:
                #advanced search
            
            #retrieved.append(local_result)
        
        return retrieved

    def _retrieve_resources(self, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Retrieve assets through local search then advanced search if needed."""
        retrieved = []
        
        for resource in resources:
            resource_type = resource.get("type", "").lower().strip()
            
            if resource_type == "3d model":
                result = self._retrieve_3d_model(resource)
            elif resource_type == "texture":
                result = self._retrieve_texture(resource)
            elif resource_type == "audio":
                result = self._retrieve_audio(resource)
            elif resource_type == "script":
                result = self._retrieve_script(resource)
            else:
                result = {"requested_resource": resource.get("name"), "status": "unsupported_type"}
            
            retrieved.append(result)
        
        return retrieved


    def _find_model_file(self, path: Path) -> Path | None:
        """Find the model file within a directory."""
        if path.is_file():
            return path
            
        # If directory, look for common model formats
        extensions = {".gltf", ".glb", ".fbx", ".obj"}
        
        # Look for any model file with supported extension
        for item in path.rglob("*"):
            if item.is_file() and item.suffix.lower() in extensions:
                return item
                
        return None

    def _process_path_for_unity(self, file_path: str) -> str:
        """Process path to be compatible with Unity Resources.Load.
        
        Removes the part of the path before 'Resources/' and strips the file extension.
        """
        try:
            path_obj = Path(file_path)
            parts = path_obj.parts
            
            # Find 'Resources' in path parts
            if 'Resources' in parts:
                res_index = parts.index('Resources')
                # Reconstruct path relative to Resources
                rel_path = Path(*parts[res_index + 1:])
                # Remove extension
                return str(rel_path.with_suffix(''))
            
            return file_path
        except Exception:
            return file_path

    def _retrieve_3d_model(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Retrieve 3D model from local directories or Sketchfab API."""

        resource_name = resource.get("name", "")
        
        print(f"Retrieving 3D model: {resource_name}")
        # Local Search
        if self.models_path.exists():
            for item in self.models_path.iterdir():
                if resource_name.lower() in item.name.lower():
                    model_file = self._find_model_file(item)
                    if model_file:
                        return {
                            "name": resource_name,
                            "path": self._process_path_for_unity(str(model_file)),
                            "source": "local",
                            "status": "found"
                        }
            
            # Semantic Search
            semantic_path = self._semantic_search_local(resource_name, self.models_path)
            if semantic_path:
                model_file = self._find_model_file(semantic_path)
                if model_file:
                    return {
                        "name": resource_name,
                        "path": self._process_path_for_unity(str(model_file)),
                        "source": "local_semantic",
                        "status": "found"
                    }

        # Advanced Search
        if self.sketchfab_token:
            try:
                with requests.Session() as session:

                    client = SketchfabClient(self.sketchfab_token, session, self.models_path)
                    downloaded_paths = client.download_models(
                        model_names=[resource_name],
                        search_limit=5,
                        download_limit=1
                    )
                    if downloaded_paths:
                        # Add embedding for the new model
                        new_model_path = downloaded_paths[0]
                        # Calculate the top-level folder name relative to models_path
                        try:
                            relative_path = new_model_path.relative_to(self.models_path)
                            asset_folder_name = relative_path.parts[0]
                        except ValueError:
                            # Fallback if path is not relative to models_path (should not happen)
                            asset_folder_name = new_model_path.parent.name

                        self._add_embedding_for_folder(asset_folder_name, self.models_path, search_query=resource_name)

                        return {
                            "name": resource_name,
                            "path": self._process_path_for_unity(str(downloaded_paths[0])),
                            "source": "sketchfab",
                            "status": "found"
                        }
            except Exception as e:
                print(f"Advanced search failed: {e}")
        else:
            print("Sketchfab token not provided; skipping advanced search.")
        
        return {"name": resource_name, "status": "not_found"}

    
    def _retrieve_texture(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Retrieve texture from local directories or external resources."""
        # implement local retrieval logic here
         # if found locally, return the result
        # implement advanced retrieval logic here
        pass

    def _retrieve_audio(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Retrieve audio from local directories or external resources."""
        # implement local retrieval logic here
         # if found locally, return the result
        # implement advanced retrieval logic here
        pass

    def _retrieve_script(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Retrieve script from local directories or knowledge graph."""
        # implement local retrieval logic here
         # if found locally, return the result
        # implement advanced retrieval logic here
        pass

    def _local_search(self, resource: dict[str, Any], search_path: Path) -> dict[str, Any]:
        """Perform local search for the given query in the specified path."""
        # implement local search logic here
        pass
    
    def _semantic_search_local(self, query: str, search_path: Path) -> Path | None:
        """Perform semantic search on local folders using embeddings."""
        embeddings_file = search_path / "embeddings.csv"
        embedding_model = OllamaEmbeddings(model="nomic-embed-text:v1.5")
        
        embeddings_list = []
        
        # 1. Load Embeddings
        if not embeddings_file.exists():
            return None
            
        try:
            with open(embeddings_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    folder_name = row.get("folder_name")
                    if not folder_name:
                        continue
                        
                    # Handle folder_embedding (new) or embedding (old)
                    folder_emb_str = row.get("folder_embedding") or row.get("embedding")

                    emb = ast.literal_eval(folder_emb_str)
                    embeddings_list.append((folder_name, emb))


                    # Handle query_embedding (new)
                    query_emb_str = row.get("query_embedding")

                    if query_emb_str:
                        try:
                            emb = ast.literal_eval(query_emb_str)
                            embeddings_list.append((folder_name, emb))
                        except (ValueError, SyntaxError):
                            pass

        except Exception as e:
            print(f"Failed to load embeddings: {e}")
            return None

        # 2. Embed Query
        try:
            query_embedding = embedding_model.embed_query(query)
        except Exception as e:
            print(f"Failed to embed query: {e}")
            return None
        
        # 3. Find Best Match
        best_score = -1.0
        best_folder = None
        
        for name, emb in embeddings_list:
            # Cosine similarity
            dot_product = sum(a*b for a, b in zip(query_embedding, emb))
            magnitude1 = math.sqrt(sum(a*a for a in query_embedding))
            magnitude2 = math.sqrt(sum(b*b for b in emb))
            
            if magnitude1 == 0 or magnitude2 == 0:
                score = 0.0
            else:
                score = dot_product / (magnitude1 * magnitude2)
                
            if score > best_score:
                # Verify the folder actually exists to avoid stale/incorrect embeddings
                if (search_path / name).exists():
                    best_score = score
                    best_folder = name
        
        if best_score > 0.6: # Threshold
             return search_path / best_folder
             
        return None
    
    def _add_embedding_for_folder(self, folder_name: str, search_path: Path, search_query: str | None = None) -> None:
        """Generate and save embedding for a new folder."""
        embeddings_file = search_path / "embeddings.csv"
        embedding_model = OllamaEmbeddings(model="nomic-embed-text:v1.5")
        
        try:
            folder_embedding = embedding_model.embed_query(folder_name)
            query_embedding = None
            if search_query and search_query != folder_name:
                query_embedding = embedding_model.embed_query(search_query)
            
            fieldnames = ["folder_name", "folder_embedding", "query_embedding"]
            
            # Check for migration
            if embeddings_file.exists():
                with open(embeddings_file, 'r') as f:
                    reader = csv.DictReader(f)
                    if "folder_embedding" not in reader.fieldnames:
                        # Old format detected. Read all and convert.
                        rows = []
                        # Re-open to read from start
                        f.seek(0)
                        reader = csv.DictReader(f)
                        for row in reader:
                            rows.append({
                                "folder_name": row["folder_name"],
                                "folder_embedding": row["embedding"],
                                "query_embedding": ""
                            })
                        # Rewrite file with new format
                        with open(embeddings_file, 'w', newline='') as f_out:
                            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(rows)

            # If file doesn't exist, create it
            if not embeddings_file.exists():
                with open(embeddings_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
            
            # Append new row
            with open(embeddings_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow({
                    "folder_name": folder_name,
                    "folder_embedding": str(folder_embedding),
                    "query_embedding": str(query_embedding) if query_embedding else ""
                })
                
        except Exception as e:
            print(f"Failed to add embedding for {folder_name}: {e}")