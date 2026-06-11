import os
import json
from datetime import datetime

RECENT_FILE = r"D:\vizhi-spatial-software\recent_projects.json"
DATASETS_DIR = r"D:\vizhi-spatial-software\datasets"

class ProjectManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ProjectManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.recent_projects = []
            cls._instance.load_recent_list()
        return cls._instance

    def load_recent_list(self):
        try:
            if os.path.exists(RECENT_FILE):
                with open(RECENT_FILE, "r", encoding="utf-8") as f:
                    self.recent_projects = json.load(f)
            else:
                self.save_recent_list()
        except Exception as e:
            print(f"Error loading recent projects: {e}")

    def save_recent_list(self):
        try:
            os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)
            with open(RECENT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.recent_projects, f, indent=4)
        except Exception as e:
            print(f"Error saving recent projects: {e}")

    def get_recent_projects(self):
        # Sync with actual folders to ensure directories still exist
        valid_projects = []
        changed = False
        for p in self.recent_projects:
            if os.path.exists(p.get("path", "")):
                valid_projects.append(p)
            else:
                changed = True
                
        # Scan datasets directory and auto-add any subdirectories not in the list
        if os.path.exists(DATASETS_DIR):
            for name in os.listdir(DATASETS_DIR):
                path = os.path.join(DATASETS_DIR, name)
                if os.path.isdir(path):
                    # Check if already in recent list
                    exists = any(p.get("path") == path for p in valid_projects)
                    if not exists:
                        try:
                            mtime = os.path.getmtime(path)
                            dt_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        entry = {
                            "name": name,
                            "path": path,
                            "last_opened": dt_str,
                            "pinned": False
                        }
                        valid_projects.append(entry)
                        changed = True
                        
        if changed:
            self.recent_projects = valid_projects
            self.save_recent_list()
        return self.recent_projects

    def add_recent_project(self, name, path):
        # Remove if already exists to move to top
        self.recent_projects = [p for p in self.recent_projects if p.get("path") != path]
        
        project_entry = {
            "name": name,
            "path": path,
            "last_opened": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pinned": False
        }
        self.recent_projects.insert(0, project_entry)
        self.save_recent_list()

    def set_pinned(self, path, pinned):
        for p in self.recent_projects:
            if p.get("path") == path:
                p["pinned"] = pinned
                break
        self.save_recent_list()

    def remove_recent_project(self, path):
        self.recent_projects = [p for p in self.recent_projects if p.get("path") != path]
        self.save_recent_list()

    def create_project(self, name, location, description, capture_type, auto_save_interval):
        # Subfolders setup
        project_path = os.path.join(location, name)
        subfolders = ["captures", "thumbnails", "sparse", "gaussian", "exports", "logs", "images"]
        
        for f in subfolders:
            os.makedirs(os.path.join(project_path, f), exist_ok=True)
            
        metadata = {
            "name": name,
            "location": location,
            "path": project_path,
            "description": description,
            "capture_type": capture_type,
            "auto_save_interval": auto_save_interval,
            "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_opened": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "frames_count": 0,
            "reconstruction_status": "Not Started",
            "gaussian_status": "Not Started"
        }
        
        meta_file = os.path.join(project_path, "metadata.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        self.add_recent_project(name, project_path)
        return project_path

    def load_project_metadata(self, path):
        meta_file = os.path.join(path, "metadata.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    
                # Sync frame count on load
                images_dir = os.path.join(path, "images")
                if os.path.exists(images_dir):
                    meta["frames_count"] = len([f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                    
                # Update last opened
                meta["last_opened"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=4)
                    
                return meta
            except Exception as e:
                print(f"Error loading project metadata: {e}")
        return None

    def update_project_metadata(self, path, updates):
        meta_file = os.path.join(path, "metadata.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta.update(updates)
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=4)
                return meta
            except Exception as e:
                print(f"Error updating project metadata: {e}")
        return None
