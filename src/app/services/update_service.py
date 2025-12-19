"""
UpdateService - Manages application updates.
Checks for new releases on GitHub and handles downloading.
"""

import os
import requests
import json
import subprocess
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread

from config.config import APP_VERSION, UPDATE_CHECK_URL, USER_DATA_DIR
try:
    from version import FULL_VERSION
except ImportError:
    FULL_VERSION = APP_VERSION

class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
            
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

class UpdateService(QObject):
    """Service to check for updates and manage downloads."""
    
    def __init__(self):
        super().__init__()
        self._latest_release = None

    def check_for_updates(self) -> dict:
        """
        Check GitHub for the latest release.
        Returns a dict with update info if available.
        """
        try:
            # Set User-Agent as required by GitHub API
            headers = {'User-Agent': 'MSA-Desktop-App'}
            response = requests.get(UPDATE_CHECK_URL, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self._latest_release = data
                
                remote_version = data.get('tag_name', '').replace('v', '')
                current_version = APP_VERSION
                
                # Check if remote version is newer
                if self._is_newer(remote_version, current_version):
                    assets = data.get('assets', [])
                    download_url = ""
                    
                    import platform
                    ext = ".exe" if platform.system() == "Windows" else ".dmg"
                    
                    for asset in assets:
                        if asset.get('name', '').endswith(ext):
                            download_url = asset.get('browser_download_url')
                            break
                    
                    if not download_url and assets:
                        download_url = assets[0].get('browser_download_url')

                    return {
                        "update_available": True,
                        "version": remote_version,
                        "name": data.get('name', 'New Update'),
                        "body": data.get('body', 'No release notes available.'),
                        "url": download_url,
                        "published_at": data.get('published_at')
                    }
                else:
                    return {"update_available": False}
            elif response.status_code == 404:
                return {"update_available": False, "error": "Update server or repository not found."}
            else:
                return {"update_available": False, "error": f"Server returned status {response.status_code}"}
        except Exception as e:
            print(f"Update Check Error: {e}")
            return {"update_available": False, "error": str(e)}

    def _is_newer(self, remote, current):
        """Compare version strings like 1.0.3 and 1.0.2"""
        try:
            remote_parts = [int(p) for p in remote.split('.')]
            current_parts = [int(p) for p in current.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(remote_parts), len(current_parts))
            remote_parts += [0] * (max_len - len(remote_parts))
            current_parts += [0] * (max_len - len(current_parts))
            
            return remote_parts > current_parts
        except:
            return remote > current # Fallback to string comparison

    def create_download_thread(self, url, filename):
        """Creates a thread to download the update."""
        dest_dir = os.path.join(USER_DATA_DIR, "updates")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        
        return DownloadThread(url, dest_path)

    def launch_installer(self, path):
        """Launches the downloaded installer file."""
        import platform
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
            return True
        except Exception as e:
            print(f"Failed to launch installer: {e}")
            return False
