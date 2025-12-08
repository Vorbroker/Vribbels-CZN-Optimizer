
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\stayp\OneDrive\Documents\czn_capture_tool\fresh\captures")

class Addon:
    def __init__(self):
        self.inventory_data = None
        self.character_data = None
        self.saved_path = None
    
    def websocket_message(self, flow):
        msg = flow.websocket.messages[-1]
        if msg.from_client:
            return
        try:
            data = json.loads(msg.text)
            if data.get("res") != "ok":
                return
            
            keys = list(data.keys())
            print(f">>> API response keys: {keys}")
            
            if "piece_items" in data:
                self.inventory_data = data
                print(f">>> Captured inventory: {len(data.get('piece_items', []))} pieces")
                self._save_data()
            
            has_characters = "characters" in data and isinstance(data.get("characters"), list)
            has_user = "user" in data
            
            if has_characters or has_user:
                self.character_data = data
                char_count = len(data.get("characters", []))
                print(f">>> Captured character data: {char_count} chars")
                self._save_data()
                
        except Exception as e:
            print(f"Error: {e}")
    
    def _save_data(self):
        if not self.inventory_data:
            return
            
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not self.saved_path:
            self.saved_path = OUTPUT_DIR / f"memory_fragments_{ts}.json"
        
        save_data = {
            "capture_time": datetime.now().isoformat(),
            "inventory": self.inventory_data,
            "characters": self.character_data,
        }
        
        with open(self.saved_path, "w") as f:
            json.dump(save_data, f, indent=2)
        
        count = len(self.inventory_data.get("piece_items", []))
        has_chars = "Yes" if self.character_data else "No"
        print(f">>> SAVED {count} Memory Fragments (char data: {has_chars}) to {self.saved_path.name}")

addons = [Addon()]
