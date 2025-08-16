"""
Unified Translation Engine for VezylTranslator
Centralized translation system supporting multiple providers
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import os
import sys
import threading
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

# Language detection
try:
    from langdetect import detect
except ImportError:
    detect = None

# Google Translate
try:
    from googletrans import Translator as GoogleTranslator
except ImportError:
    GoogleTranslator = None

from VezylTranslatorNeutron import constant


# === Marian Model Manager (merged from marian_module.py) ===
class MarianModelManager:
    """Marian MT Model Manager - Simple version"""
    
    def __init__(self):
        self.models_dir = Path(constant.MARIAN_MODELS_DIR)
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


class TranslationModel(Enum):
    """Supported translation models"""
    GOOGLE = "google"
    DEEPL = "deepl"
    BING = "bing"
    MARIAN = "marian"
    OPUS = "opus"


@dataclass
class TranslationResult:
    """Translation result container"""
    text: str
    src_lang: str
    dest_lang: str
    model: str
    confidence: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            "text": self.text,
            "src": self.src_lang,
            "dest": self.dest_lang,
            "model": self.model,
            "confidence": self.confidence,
            "error": self.error
        }


class BaseTranslationProvider(ABC):
    """Abstract base class for translation providers"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_available = False
        self._check_availability()
    
    @abstractmethod
    def _check_availability(self):
        """Check if this provider is available"""
        pass
    
    @abstractmethod
    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "vi") -> TranslationResult:
        """Translate text using this provider"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported language pairs"""
        pass


class GoogleTranslationProvider(BaseTranslationProvider):
    """Google Translation provider"""
    
    def __init__(self):
        self.translator = None
        super().__init__("google")
    
    def _check_availability(self):
        """Check if Google Translate is available"""
        try:
            if GoogleTranslator is not None:
                self.translator = GoogleTranslator()
                if self.translator is not None:
                    self.is_available = True
                    print("[OK] Google Translator available")
                else:
                    self.is_available = False
                    print("[ERROR] Google Translator creation returned None")
            else:
                print("[WARNING] Google Translator library not imported")
                self.is_available = False
        except Exception as e:
            print(f"[ERROR] Google Translator initialization failed: {e}")
            self.is_available = False
            self.translator = None
    
    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "vi") -> TranslationResult:
        """Translate using Google Translate"""
        if not self.is_available or not self.translator:
            return TranslationResult(
                text=f"Google Translate không khả dụng: {text}",
                src_lang=src_lang,
                dest_lang=dest_lang,
                model="google",
                error="Google Translate not available"
            )
        
        try:
            import asyncio
            import inspect
            import concurrent.futures
            
            # Function to run translation in a clean thread
            def run_translation_in_thread():
                try:
                    # Create fresh translator instance in thread
                    from googletrans import Translator
                    thread_translator = Translator()
                    
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Call translate method
                        if src_lang == "auto":
                            coro = thread_translator.translate(text, dest=dest_lang)
                        else:
                            coro = thread_translator.translate(text, src=src_lang, dest=dest_lang)
                        
                        # Run the coroutine
                        result = loop.run_until_complete(coro)
                        return result
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    raise e
            
            # Always use thread for Google Translate to avoid async conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_translation_in_thread)
                result = future.result(timeout=15)  # 15 second timeout
            
            # Process the result
            if hasattr(result, 'text') and hasattr(result, 'src'):
                return TranslationResult(
                    text=result.text,
                    src_lang=result.src,
                    dest_lang=dest_lang,
                    model="google",
                    confidence=1.0
                )
            else:
                # Fallback if result format is unexpected
                return TranslationResult(
                    text=str(result),
                    src_lang=src_lang,
                    dest_lang=dest_lang,
                    model="google",
                    confidence=0.5
                )
                
        except Exception as e:
            return TranslationResult(
                text=f"Lỗi dịch Google: {text}",
                src_lang=src_lang,
                dest_lang=dest_lang,
                model="google",
                error=str(e)
            )
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get Google Translate supported languages"""
        return {
            "auto": "🔍 Tự động phát hiện",
            "en": "🇺🇸 English",
            "vi": "🇻🇳 Tiếng Việt",
            "ja": "🇯🇵 日本語",
            "ko": "🇰🇷 한국어",
            "zh-cn": "🇨🇳 中文(简体)",
            "zh-tw": "🇹🇼 中文(繁體)",
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "ru": "🇷🇺 Русский",
            "es": "🇪🇸 Español",
            "th": "🇹🇭 ไทย"
        }


class MarianTranslationProvider(BaseTranslationProvider):
    """Marian MT translation provider"""
    
    def __init__(self):
        super().__init__("marian")
        self.model_manager = None
        self.transformers_available = False
        self.model_cache = {}
        self.tokenizer_cache = {}
        self._check_transformers()
        self._load_dictionaries()
    
    def _check_availability(self):
        """Check if Marian MT is available"""
        try:
            self.model_manager = MarianModelManager()
            
            # Check if any models are available
            downloaded_models = self.model_manager.get_downloaded_models()
            if downloaded_models:
                self.is_available = True
                print(f"[OK] Marian MT available with {len(downloaded_models)} models")
            else:
                print("[WARNING] Marian MT: No models found")
        except Exception as e:
            print(f"[ERROR] Marian MT initialization failed: {e}")
    
    def _check_transformers(self):
        """Check if transformers library is available"""
        try:
            from transformers import MarianMTModel, MarianTokenizer
            self.transformers_available = True
            self.MarianMTModel = MarianMTModel
            self.MarianTokenizer = MarianTokenizer
            print("[OK] Transformers library available for Marian MT")
        except ImportError:
            self.transformers_available = False
            print("[WARNING] Transformers library not available for Marian MT")
    
    def _load_dictionaries(self):
        """Load simple translation dictionaries for fallback"""
        self.dictionaries = {
            ("en", "vi"): {
                "hello": "xin chào",
                "world": "thế giới",
                "hello world": "xin chào thế giới",
                "good morning": "chào buổi sáng",
                "good evening": "chào buổi tối",
                "good night": "chúc ngủ ngon",
                "thank you": "cảm ơn",
                "goodbye": "tạm biệt",
                "how are you": "bạn khỏe không",
                "what is your name": "tên bạn là gì",
                "my name is": "tên tôi là",
                "nice to meet you": "rất vui được gặp bạn",
                "please": "xin vui lòng",
                "sorry": "xin lỗi",
                "yes": "có",
                "no": "không",
                "maybe": "có thể",
                "i love you": "tôi yêu bạn",
                "help": "giúp đỡ",
                "water": "nước",
                "food": "đồ ăn",
            },
            ("vi", "en"): {
                "xin chào": "hello",
                "thế giới": "world",
                "xin chào thế giới": "hello world",
                "chào buổi sáng": "good morning",
                "chào buổi tối": "good evening",
                "chúc ngủ ngon": "good night",
                "cảm ơn": "thank you",
                "tạm biệt": "goodbye",
                "bạn khỏe không": "how are you",
                "tên bạn là gì": "what is your name",
                "tên tôi là": "my name is",
                "rất vui được gặp bạn": "nice to meet you",
                "xin vui lòng": "please",
                "xin lỗi": "sorry",
                "có": "yes",
                "không": "no",
                "có thể": "maybe",
                "tôi yêu bạn": "i love you",
                "giúp đỡ": "help",
                "nước": "water",
                "đồ ăn": "food",
            },
            ("de", "en"): {
                "hallo": "hello",
                "welt": "world",
                "guten tag": "good day",
                "guten morgen": "good morning",
                "danke": "thank you",
                "auf wiedersehen": "goodbye"
            },
            ("en", "de"): {
                "hello": "hallo",
                "world": "welt",
                "good day": "guten tag",
                "good morning": "guten morgen",
                "thank you": "danke",
                "goodbye": "auf wiedersehen"
            }
        }
    
    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "vi") -> TranslationResult:
        """Translate using Marian MT"""
        if not self.is_available or not self.model_manager:
            return TranslationResult(
                text=f"Marian MT không khả dụng: {text}",
                src_lang=src_lang,
                dest_lang=dest_lang,
                model="marian",
                error="Marian MT not available"
            )
        
        try:
            # Auto-detect language if needed
            if src_lang == "auto":
                detected = self._detect_language(text)
                if detected == 'unknown':
                    src_lang = "en"  # Fallback
                elif detected == 'mixed':
                    return self._handle_mixed_language(text, dest_lang)
                else:
                    src_lang = detected
            
            # Try dictionary first for simple/common phrases
            dict_key = (src_lang, dest_lang)
            if dict_key in self.dictionaries:
                text_lower = text.lower().strip()
                if text_lower in self.dictionaries[dict_key]:
                    translated = self.dictionaries[dict_key][text_lower]
                    return TranslationResult(
                        text=translated,
                        src_lang=src_lang,
                        dest_lang=dest_lang,
                        model="marian",
                        confidence=0.9
                    )
            
            # Try AI model if transformers available
            if self.transformers_available:
                result = self._translate_with_ai_model(text, src_lang, dest_lang)
                if result:
                    return result
            
            # Fallback: return original text
            return TranslationResult(
                text=text,
                src_lang=src_lang,
                dest_lang=dest_lang,
                model="marian",
                confidence=0.1,
                error="No suitable model found"
            )
            
        except Exception as e:
            return TranslationResult(
                text=f"Lỗi Marian: {text}",
                src_lang=src_lang,
                dest_lang=dest_lang,
                model="marian",
                error=str(e)
            )
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        if not detect:
            return "unknown"
        
        try:
            detected = detect(text)
            return detected
        except:
            return "unknown"
    
    def _handle_mixed_language(self, text: str, dest_lang: str) -> TranslationResult:
        """Handle mixed language text"""
        # Simple mixed language handling
        return TranslationResult(
            text=f"[Mixed] {text}",
            src_lang="mixed",
            dest_lang=dest_lang,
            model="marian",
            confidence=0.3
        )
    
    def _translate_with_ai_model(self, text: str, src_lang: str, dest_lang: str) -> Optional[TranslationResult]:
        """Translate using AI model"""
        model_key = f"{src_lang}-{dest_lang}"
        model_path = self.model_manager.get_model_path(model_key)
        
        # Try direct translation
        if model_path:
            result = self._translate_with_model(text, model_path, src_lang, dest_lang)
            if result:
                return result
        
        # Try two-step translation through English
        if src_lang != "en" and dest_lang != "en":
            # Step 1: src -> en
            en_model_key = f"{src_lang}-en"
            en_model_path = self.model_manager.get_model_path(en_model_key)
            
            if en_model_path:
                en_result = self._translate_with_model(text, en_model_path, src_lang, "en")
                if en_result and en_result.text:
                    # Step 2: en -> dest
                    dest_model_key = f"en-{dest_lang}"
                    dest_model_path = self.model_manager.get_model_path(dest_model_key)
                    
                    if dest_model_path:
                        final_result = self._translate_with_model(en_result.text, dest_model_path, "en", dest_lang)
                        if final_result:
                            final_result.src_lang = src_lang  # Keep original source
                            return final_result
        
        return None
    
    def _translate_with_model(self, text: str, model_path: str, src_lang: str, dest_lang: str) -> Optional[TranslationResult]:
        """Translate using specific model"""
        try:
            # Check required files
            required_files = ["pytorch_model.bin", "config.json"]
            for file in required_files:
                if not os.path.exists(os.path.join(model_path, file)):
                    return None
            
            # Load model and tokenizer with caching
            if model_path not in self.model_cache:
                print(f"Loading Marian model: {model_path}")
                self.model_cache[model_path] = self.MarianMTModel.from_pretrained(model_path, local_files_only=True)
                self.tokenizer_cache[model_path] = self.MarianTokenizer.from_pretrained(model_path, local_files_only=True)
            
            model = self.model_cache[model_path]
            tokenizer = self.tokenizer_cache[model_path]
            
            # Prepare inputs
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # Generate with timeout
            result_container = [None]
            exception_container = [None]
            
            def generate_with_timeout():
                try:
                    outputs = model.generate(
                        **inputs,
                        max_length=min(len(text.split()) * 3 + 10, 128),
                        min_length=1,
                        num_beams=2,
                        early_stopping=True,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.5,
                        do_sample=False,
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                    result_container[0] = outputs
                except Exception as e:
                    exception_container[0] = e
            
            thread = threading.Thread(target=generate_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout=5.0)
            
            if thread.is_alive():
                print(f"Model generation timeout: {text}")
                return None
            
            if exception_container[0]:
                raise exception_container[0]
            
            if result_container[0] is None:
                return None
            
            outputs = result_container[0]
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Check for repetition
            words = translated_text.split()
            if len(words) > 10:
                unique_words = set(words)
                if len(unique_words) / len(words) < 0.5:
                    return None  # Too much repetition
            
            return TranslationResult(
                text=translated_text,
                src_lang=src_lang,
                dest_lang=dest_lang,
                model="marian",
                confidence=0.8
            )
            
        except Exception as e:
            print(f"Model translation error: {e}")
            return None
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get Marian supported languages"""
        if not self.model_manager:
            return {"error": "Marian MT not available"}
        
        try:
            language_pairs = self.model_manager.get_supported_language_pairs()
            if not language_pairs:
                return {"no-models": "No Marian models found"}
            
            lang_names = {
                "en": "English", "vi": "Vietnamese", "de": "German", "fr": "French",
                "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
                "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ar": "Arabic"
            }
            
            supported = {}
            pairs_processed = set()
            
            for src_lang, dest_lang in language_pairs:
                pair_key = tuple(sorted([src_lang, dest_lang]))
                
                if pair_key in pairs_processed:
                    continue
                
                pairs_processed.add(pair_key)
                
                # Check bidirectional support
                has_reverse = (dest_lang, src_lang) in language_pairs
                
                src_name = lang_names.get(src_lang, src_lang.upper())
                dest_name = lang_names.get(dest_lang, dest_lang.upper())
                
                if has_reverse and src_lang != dest_lang:
                    key = f"{src_lang}↔{dest_lang}"
                    if src_lang == "en":
                        display = f"{src_name} ↔ {dest_name}"
                    elif dest_lang == "en":
                        display = f"{dest_name} ↔ {src_name}"
                    else:
                        display = f"{src_name} ↔ {dest_name}" if src_name < dest_name else f"{dest_name} ↔ {src_name}"
                    supported[key] = display
                else:
                    key = f"{src_lang}-{dest_lang}"
                    supported[key] = f"{src_name} -> {dest_name}"
            
            return supported
            
        except Exception as e:
            return {"error": f"Error loading models: {e}"}


class DeepLTranslationProvider(BaseTranslationProvider):
    """DeepL translation provider (placeholder)"""
    
    def __init__(self):
        super().__init__("deepl")
    
    def _check_availability(self):
        """DeepL not implemented yet"""
        self.is_available = False
        print("[WARNING] DeepL Translator not implemented")
    
    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "vi") -> TranslationResult:
        """DeepL translate placeholder"""
        return TranslationResult(
            text=f"[DeepL] {text} (Chưa hỗ trợ)",
            src_lang=src_lang,
            dest_lang=dest_lang,
            model="deepl",
            error="DeepL not implemented"
        )
    
    def get_supported_languages(self) -> Dict[str, str]:
        return {"deepl": "DeepL (Chưa hỗ trợ)"}


class BingTranslationProvider(BaseTranslationProvider):
    """Bing translation provider (placeholder)"""
    
    def __init__(self):
        super().__init__("bing")
    
    def _check_availability(self):
        """Bing not implemented yet"""
        self.is_available = False
        print("[WARNING] Bing Translator not implemented")
    
    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "vi") -> TranslationResult:
        """Bing translate placeholder"""
        return TranslationResult(
            text=f"[Bing] {text} (Chưa hỗ trợ)",
            src_lang=src_lang,
            dest_lang=dest_lang,
            model="bing",
            error="Bing not implemented"
        )
    
    def get_supported_languages(self) -> Dict[str, str]:
        return {"bing": "Bing (Chưa hỗ trợ)"}


class TranslationEngine:
    """Main translation engine that coordinates all providers"""
    
    def __init__(self):
        self.providers: Dict[str, BaseTranslationProvider] = {}
        self.default_model = "google"
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all translation providers"""
        print("Initializing translation providers...")
        
        # Initialize providers
        self.providers["google"] = GoogleTranslationProvider()
        self.providers["marian"] = MarianTranslationProvider()
        self.providers["deepl"] = DeepLTranslationProvider()
        self.providers["bing"] = BingTranslationProvider()
        
        # Set default to first available provider
        for name, provider in self.providers.items():
            if provider.is_available:
                self.default_model = name
                print(f"Set default translation model to: {name}")
                break
    
    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "vi", model: str = None) -> TranslationResult:
        """Translate text using specified or default model"""
        if not text.strip():
            return TranslationResult(
                text="",
                src_lang=src_lang,
                dest_lang=dest_lang,
                model=model or self.default_model
            )
        
        # Use specified model or default
        model_name = model or self.default_model
        
        if model_name not in self.providers:
            model_name = self.default_model
        
        provider = self.providers[model_name]
        
        if not provider.is_available:
            # Fall back to Google if available
            if "google" in self.providers and self.providers["google"].is_available:
                provider = self.providers["google"]
                model_name = "google"
            else:
                # Return error result
                return TranslationResult(
                    text=f"Không có provider khả dụng: {text}",
                    src_lang=src_lang,
                    dest_lang=dest_lang,
                    model=model_name,
                    error="No available translation provider"
                )
        
        try:
            result = provider.translate(text, src_lang, dest_lang)
            result.model = model_name  # Ensure correct model name
            return result
        except Exception as e:
            return TranslationResult(
                text=f"Lỗi dịch: {text}",
                src_lang=src_lang,
                dest_lang=dest_lang,
                model=model_name,
                error=str(e)
            )
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available translation models"""
        available = {}
        for name, provider in self.providers.items():
            if provider.is_available:
                model_names = {
                    "google": "🌐 Google Translator",
                    "deepl": "🔬 DeepL Translator", 
                    "marian": "🤖 Marian MT (Offline)",
                    "bing": "🔍 Bing Translator"
                }
                available[name] = model_names.get(name, name.title())
        
        return available
    
    def get_supported_languages(self, model: str = None) -> Dict[str, str]:
        """Get supported languages for specified model"""
        model_name = model or self.default_model
        
        if model_name in self.providers:
            return self.providers[model_name].get_supported_languages()
        
        return {}
    
    def set_default_model(self, model: str):
        """Set default translation model"""
        if model in self.providers and self.providers[model].is_available:
            self.default_model = model
            print(f"Default translation model set to: {model}")
        else:
            print(f"Model {model} not available")
    
    def get_provider(self, model: str) -> Optional[BaseTranslationProvider]:
        """Get specific provider"""
        return self.providers.get(model)


# === Global Translation Engine Instance ===
_global_translation_engine: Optional[TranslationEngine] = None


def get_translation_engine() -> TranslationEngine:
    """Get the global translation engine instance"""
    global _global_translation_engine
    if _global_translation_engine is None:
        _global_translation_engine = TranslationEngine()
    return _global_translation_engine


def reset_translation_engine():
    """Reset the global translation engine (for testing)"""
    global _global_translation_engine
    _global_translation_engine = None


# === Legacy Support Functions ===

def translate_with_model(text: str, src_lang: str = "auto", dest_lang: str = "vi", model_name: str = "google") -> Union[Dict[str, Any], TranslationResult]:
    """Legacy function for backward compatibility"""
    engine = get_translation_engine()
    result = engine.translate(text, src_lang, dest_lang, model_name)
    
    # Return dictionary for backward compatibility
    return result.to_dict()


def google_translate(text: str, src_lang: str = "auto", dest_lang: str = "vi") -> Dict[str, Any]:
    """Legacy Google translate function"""
    return translate_with_model(text, src_lang, dest_lang, "google")


def marian_translate(text: str, src_lang: str = "auto", dest_lang: str = "vi") -> Dict[str, Any]:
    """Legacy Marian translate function"""
    return translate_with_model(text, src_lang, dest_lang, "marian")


def deepl_translate(text: str, src_lang: str = "auto", dest_lang: str = "vi") -> Dict[str, Any]:
    """Legacy DeepL translate function"""
    return translate_with_model(text, src_lang, dest_lang, "deepl")


def bing_translate(text: str, src_lang: str = "auto", dest_lang: str = "vi") -> Dict[str, Any]:
    """Legacy Bing translate function"""
    return translate_with_model(text, src_lang, dest_lang, "bing")


def get_marian_supported_languages() -> Dict[str, str]:
    """Legacy function to get Marian supported languages"""
    engine = get_translation_engine()
    marian_provider = engine.get_provider("marian")
    if marian_provider:
        return marian_provider.get_supported_languages()
    return {"error": "Marian provider not available"}


def detect_language(text: str) -> str:
    """Detect language of text"""
    if not detect:
        return "unknown"
    
    try:
        return detect(text)
    except:
        return "unknown"


# === Convenience Functions ===

def quick_translate(text: str, dest_lang: str = "vi", model: str = None) -> str:
    """Quick translation that returns just the text"""
    engine = get_translation_engine()
    result = engine.translate(text, "auto", dest_lang, model)
    return result.text


def batch_translate(texts: List[str], dest_lang: str = "vi", model: str = None) -> List[TranslationResult]:
    """Translate multiple texts"""
    engine = get_translation_engine()
    results = []
    
    for text in texts:
        result = engine.translate(text, "auto", dest_lang, model)
        results.append(result)
    
    return results


def get_available_translation_models() -> Dict[str, str]:
    """Get available translation models"""
    engine = get_translation_engine()
    return engine.get_available_models()


def set_default_translation_model(model: str):
    """Set default translation model"""
    engine = get_translation_engine()
    engine.set_default_model(model)
