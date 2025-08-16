"""
Optimized startup wrapper để delay load các thư viện nặng
"""
import sys
import time

class LazyTransformers:
    """Lazy loader cho transformers library"""
    
    def __init__(self):
        self._transformers = None
        self._available = None
    
    @property
    def available(self):
        if self._available is None:
            try:
                import transformers
                self._available = True
                print("[OK] Transformers available (lazy loaded)")
            except ImportError:
                self._available = False
                print("[WARNING] Transformers not available")
        return self._available
    
    def get_transformers(self):
        if self._transformers is None and self.available:
            print("🔄 Loading transformers (first time)...")
            start_time = time.time()
            import transformers
            self._transformers = transformers
            load_time = time.time() - start_time
            print(f"[OK] Transformers loaded in {load_time:.3f}s")
        return self._transformers
    
    def MarianMTModel(self):
        transformers = self.get_transformers()
        if transformers:
            return transformers.MarianMTModel
        return None
    
    def MarianTokenizer(self):
        transformers = self.get_transformers()
        if transformers:
            return transformers.MarianTokenizer
        return None

# Global lazy loader instance
_lazy_transformers = LazyTransformers()

def get_transformers_available():
    """Check if transformers is available without loading it"""
    return _lazy_transformers.available

def get_marian_model():
    """Get MarianMTModel (lazy loaded)"""
    return _lazy_transformers.MarianMTModel()

def get_marian_tokenizer():
    """Get MarianTokenizer (lazy loaded)"""
    return _lazy_transformers.MarianTokenizer()

# Fast startup optimization flags
FAST_STARTUP_MODE = True
DISABLE_HEAVY_MODELS_ON_STARTUP = True
