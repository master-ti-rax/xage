from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
import os
import zipfile
from dotenv import load_dotenv

load_dotenv()

class SketchfabClient:
    """Sketchfab API helper for searching and downloading models."""

    def __init__(self, token: str, session: requests.Session, download_dir: Path) -> None:
        self._token = token
        self._session = session
        self._download_dir = download_dir
        self._base_url = os.getenv("SKETCHFAB_BASE_URL", "https://api.sketchfab.com/v3")

    def download_models(
        self,
        model_names: list[str],
        search_limit: int,
        download_limit: int,
    ) -> list[Path]:
        """Download models by searching for each model name and downloading the top results."""

        downloaded_paths: list[Path] = []
        
        for model_name in model_names:
            
            models = self._search_models(model_name, search_limit)
            
            for model in models[:download_limit]:
                uid = model.get("uid")
                name = model.get("name")
                if uid:
                    zip_path = self._download_model(uid, name)
                    gltf_path = self._extract_model(zip_path)
                    if gltf_path:
                        downloaded_paths.append(gltf_path)
        print(f"Downloaded model paths: {downloaded_paths}")
        return downloaded_paths

    def _search_models(self, query: str, limit: int) -> list[dict[str, Any]]:
        print(f"Query: {query}")

        headers = {"Authorization": f"Token {self._token}"}
        params = {
            "type": "models",
            "q": query,
            "downloadable": "true",
            "count": limit,
        }
        response = self._session.get(f"{self._base_url}/search", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        results: list[dict[str, Any]] = []
        for item in response.json().get("results", []):
            results.append({
                "uid": item.get("uid"),
                "name": item.get("name"),
            })
        return results

    def _download_model(self, uid: str, name: str | None) -> Path:
        headers = {"Authorization": f"Token {self._token}"}
        response = self._session.get(f"{self._base_url}/models/{uid}/download", headers=headers, timeout=30)
        response.raise_for_status()

        download_info = response.json()
        file_url = self._get_download_url(download_info)

        safe_name = (name or uid).replace(" ", "_")
        self._download_dir.mkdir(parents=True, exist_ok=True)
        destination = self._download_dir / f"{safe_name}.zip"

        with self._session.get(file_url, stream=True, timeout=60) as file_response:
            file_response.raise_for_status()
            with destination.open("wb") as handle:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)

        return destination

    def _get_download_url(self, download_info: dict[str, Any]) -> str:
        for key in ("gltf", "source"):
            entry = download_info.get(key)
            if entry and entry.get("url"):
                return entry["url"]
        for entry in download_info.values():
            if isinstance(entry, dict) and entry.get("url"):
                return entry["url"]
        return ""

    def _extract_model(self, zip_path: Path) -> Path | None:
        """Extract zip file, rename the .gltf file, and return its path without extension."""
        extract_dir = zip_path.with_suffix('')
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        for file_path in extract_dir.rglob("*.gltf"):
            # Rename the gltf file to match the zip name (model name)
            new_name = "model.gltf"
            new_path = file_path.parent / new_name
            file_path.rename(new_path)
            
            # Return path without extension
            return new_path.with_suffix('')
            
        return None
