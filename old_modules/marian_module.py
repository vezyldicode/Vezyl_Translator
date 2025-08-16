"""
Marian MT Model Manager - Simple version
Quản lý và phát hiện các models Marian MT có sẵn
"""
import os
from pathlib import Path
from VezylTranslatorNeutron.constant import MARIAN_MODELS_DIR

class MarianModelManager:
    def __init__(self):
        self.models_dir = Path(MARIAN_MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def get_downloaded_models(self):
        """Get list of successfully downloaded models"""
        downloaded = []
        if not self.models_dir.exists():
            return downloaded
            
        try:
            for item in os.listdir(self.models_dir):
                model_path = self.models_dir / item
                
                if model_path.is_dir() and "-" in item:
                    # Check if model has required files
                    required_files = ["pytorch_model.bin", "config.json"]
                    has_all_files = all((model_path / file).exists() for file in required_files)
                    
                    if has_all_files:
                        downloaded.append(item)
                        
        except Exception as e:
            print(f"Error scanning models directory: {e}")
            
        return downloaded
    
    def is_model_downloaded(self, model_key):
        """Check if a model is already downloaded and complete"""
        model_path = self.models_dir / model_key
        if not model_path.exists():
            return False
            
        required_files = ["pytorch_model.bin", "config.json"]
        return all((model_path / file).exists() for file in required_files)
    
    def get_model_path(self, model_key):
        """Get path to a downloaded model"""
        if self.is_model_downloaded(model_key):
            return str(self.models_dir / model_key)
        return None
    
    def get_model_size(self, model_key):
        """Get size of a downloaded model in MB"""
        model_path = self.models_dir / model_key
        if not model_path.exists():
            return 0
            
        total_size = 0
        try:
            for file_path in model_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            return 0
        
        return round(total_size / (1024 * 1024), 1)
    
    def get_supported_language_pairs(self):
        """
        Tự động phát hiện các cặp ngôn ngữ được hỗ trợ từ models có sẵn
        Returns: list of tuples (src_lang, dest_lang)
        """
        pairs = []
        downloaded_models = self.get_downloaded_models()
        
        for model_key in downloaded_models:
            if "-" in model_key:
                parts = model_key.split("-", 1)  # Split only on first dash
                if len(parts) == 2:
                    src_lang, dest_lang = parts
                    pairs.append((src_lang, dest_lang))
        
        return pairs
    
    def get_available_languages(self):
        """
        Lấy tất cả ngôn ngữ có thể sử dụng (tự động từ models)
        """
        languages = set()
        pairs = self.get_supported_language_pairs()
        
        for src, dest in pairs:
            languages.add(src)
            languages.add(dest)
            
        return sorted(list(languages))
