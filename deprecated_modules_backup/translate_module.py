from googletrans import Translator as GoogleTranslator
from langdetect import detect
import os
import sys
import threading
import time
import json
from pathlib import Path
# Lazy import for transformers to avoid PyInstaller issues
# from transformers import MarianMTModel, MarianTokenizer  # Moved to runtime import

# Global model cache to avoid reloading models
_model_cache = {}
_tokenizer_cache = {}

# Global transformers availability cache
_transformers_available = None
_transformers_models = None

def _check_transformers_availability():
    """
    Check transformers availability once and cache the result
    """
    global _transformers_available, _transformers_models
    
    if _transformers_available is None:
        try:
            from transformers import MarianMTModel, MarianTokenizer
            _transformers_available = True
            _transformers_models = {
                'MarianMTModel': MarianMTModel,
                'MarianTokenizer': MarianTokenizer
            }
            print("[OK] Transformers loaded and cached successfully")
        except ImportError:
            _transformers_available = False
            _transformers_models = None
            print("[WARNING] Transformers not available")
    
    return _transformers_available

# Simple approach for Marian MT using pre-installed models

def _get_marian_translations_dict():
    """
    Lấy dictionary translation cho Marian MT - centralized source
    
    Returns:
        dict: Dictionary chứa tất cả translations
    """
    return {
        ("en", "vi"): {
            "hello": "xin chào",
            "hi": "chào",
            "world": "thế giới", 
            "hello world": "xin chào thế giới",
            "good morning": "chào buổi sáng",
            "good evening": "chào buổi tối",
            "good night": "chúc ngủ ngon",
            "good day": "chào buổi trưa",
            "thank you": "cảm ơn",
            "thanks": "cảm ơn",
            "goodbye": "tạm biệt",
            "bye": "tạm biệt",
            "see you": "hẹn gặp lại",
            "how are you": "bạn khỏe không",
            "what is your name": "tên bạn là gì",
            "my name is": "tên tôi là",
            "nice to meet you": "rất vui được gặp bạn",
            "please": "xin vui lòng",
            "sorry": "xin lỗi",
            "excuse me": "xin lỗi",
            "yes": "có",
            "no": "không",
            "maybe": "có thể",
            "i love you": "tôi yêu bạn",
            "i like": "tôi thích",
            "i want": "tôi muốn",
            "i need": "tôi cần",
            "help": "giúp đỡ",
            "help me": "giúp tôi",
            "water": "nước",
            "food": "đồ ăn",
            "house": "nhà",
            "car": "xe hơi",
            "money": "tiền",
            "time": "thời gian",
            "today": "hôm nay",
            "tomorrow": "ngày mai",
            "yesterday": "hôm qua",
            "hell": "địa ngục"
        },
        ("vi", "en"): {
            "xin chào": "hello",
            "chào": "hi",
            "thế giới": "world",
            "xin chào thế giới": "hello world", 
            "chào buổi sáng": "good morning",
            "chào buổi tối": "good evening",
            "chúc ngủ ngon": "good night",
            "chào buổi trưa": "good day",
            "cảm ơn": "thank you",
            "tạm biệt": "goodbye",
            "hẹn gặp lại": "see you",
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
            "tôi thích": "i like",
            "tôi muốn": "i want",
            "tôi cần": "i need",
            "giúp đỡ": "help",
            "giúp tôi": "help me",
            "nước": "water",
            "đồ ăn": "food",
            "nhà": "house",
            "xe hơi": "car",
            "tiền": "money",
            "thời gian": "time",
            "hôm nay": "today",
            "ngày mai": "tomorrow",
            "hôm qua": "yesterday",
            "địa ngục": "hell"
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

def get_marian_supported_languages():
    """
    Tự động phát hiện các ngôn ngữ được hỗ trợ từ models có sẵn
    
    Returns:
        dict: Dictionary chứa các cặp ngôn ngữ hỗ trợ (đã rút gọn)
    """
    try:
        from VezylTranslatorProton.marian_module import MarianModelManager
        manager = MarianModelManager()
        
        # Lấy tất cả cặp ngôn ngữ được hỗ trợ
        language_pairs = manager.get_supported_language_pairs()
        
        if not language_pairs:
            return {"no-models": "No Marian models found in directory."}
        
        # Tạo mapping từ language codes thành language names (có thể mở rộng)
        lang_names = {
            "en": "English",
            "vi": "Vietnamese", 
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "th": "Thai",
            "tr": "Turkish",
            "pl": "Polish",
            "nl": "Dutch",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish",
            "mul": "Multilingual"
        }
        
        # Xây dựng dictionary chứa thông tin supported languages
        supported_languages = {}
        
        # Nhóm các cặp ngôn ngữ theo bidirectional
        pairs_processed = set()
        
        for src_lang, dest_lang in language_pairs:
            pair_key = tuple(sorted([src_lang, dest_lang]))
            
            if pair_key in pairs_processed:
                continue
                
            pairs_processed.add(pair_key)
            
            # Kiểm tra xem có hỗ trợ 2 chiều không
            has_reverse = (dest_lang, src_lang) in language_pairs
            
            src_name = lang_names.get(src_lang, src_lang.upper())
            dest_name = lang_names.get(dest_lang, dest_lang.upper())
            
            if has_reverse and src_lang != dest_lang:
                # Bidirectional
                key = f"{src_lang}↔{dest_lang}"
                # Sắp xếp để có thứ tự nhất quán (English trước, sau đó alphabetical)
                if src_lang == "en":
                    display = f"{src_name} ↔ {dest_name}"
                elif dest_lang == "en":
                    display = f"{dest_name} ↔ {src_name}"
                else:
                    # Alphabetical order
                    if src_name < dest_name:
                        display = f"{src_name} ↔ {dest_name}"
                    else:
                        display = f"{dest_name} ↔ {src_name}"
                
                supported_languages[key] = display
            else:
                # Unidirectional
                key = f"{src_lang}-{dest_lang}"
                supported_languages[key] = f"{src_name} -> {dest_name}"
        
        return supported_languages
        
    except Exception as e:
        print(f"Error getting Marian supported languages: {e}")
        return {"error": f"Error loading models: {e}"}

def _translate_mixed_language_smart(text, dest_lang):
    """
    Xử lý thông minh cho mixed language:
    - Phát hiện từng từ thuộc ngôn ngữ nào
    - Chỉ dịch từ có thể dịch, giữ nguyên từ không dịch được
    - Trả về kết quả hỗn hợp nhưng có ý nghĩa
    """
    try:
        # Tách từng từ trong câu
        words = text.split()
        translated_words = []
        
        # Dictionary translations
        translations = _get_marian_translations_dict()
        
        # Các ngôn ngữ có thể detect
        language_word_sets = {
            'en': {'hello', 'world', 'good', 'morning', 'evening', 'thank', 'you', 'goodbye', 'how', 'are', 'what', 'is', 'your', 'name', 'the', 'and', 'or', 'but', 'yes', 'no', 'maybe', 'help', 'water', 'food', 'house', 'car', 'money', 'time'},
            'vi': {'xin', 'chào', 'cảm', 'ơn', 'tạm', 'biệt', 'bạn', 'khỏe', 'không', 'tên', 'là', 'gì', 'thế', 'giới', 'việt', 'nam', 'có', 'thể', 'tôi', 'nước', 'đồ', 'ăn', 'nhà', 'xe', 'tiền', 'thời', 'gian'},
            'de': {'hallo', 'welt', 'guten', 'tag', 'morgen', 'danke', 'auf', 'wiedersehen', 'wie', 'geht', 'dir'}
        }
        
        for word in words:
            word_lower = word.lower().strip('.,!?;:"()[]{}')
            translated = False
            
            # Thử dịch từng từ theo thứ tự ưu tiên
            for src_lang, word_set in language_word_sets.items():
                if word_lower in word_set and src_lang != dest_lang:
                    # Tìm thấy từ thuộc ngôn ngữ này, thử dịch
                    dict_key = (src_lang, dest_lang)
                    if dict_key in translations and word_lower in translations[dict_key]:
                        # Dịch được từ dictionary
                        translated_word = translations[dict_key][word_lower]
                        # Giữ nguyên case của từ gốc
                        if word.isupper():
                            translated_word = translated_word.upper()
                        elif word[0].isupper():
                            translated_word = translated_word.capitalize()
                        translated_words.append(translated_word)
                        translated = True
                        print(f"Translated '{word}' ({src_lang}) to '{translated_word}' ({dest_lang})")
                        break
            
            if not translated:
                # Không dịch được - giữ nguyên
                translated_words.append(word)
                print(f"Kept original word: '{word}'")
        
        result_text = ' '.join(translated_words)
        
        return {
            "text": result_text,
            "src": "mixed", 
            "dest": dest_lang
        }
        
    except Exception as e:
        print(f"Smart mixed translation error: {e}")
        return {
            "text": text,  # Fallback: trả về nguyên bản
            "src": "mixed",
            "dest": dest_lang
        }

def detect_language(text):
    """
    Detect language of text using langdetect with improved accuracy
    Also detects mixed language scenarios
    
    Args:
        text (str): Text to detect language for
        
    Returns:
        str: Language code (e.g., 'en', 'vi', 'de') or 'mixed' for mixed languages
    """
    try:
        # Clean text for better detection
        clean_text = text.strip().lower()
        if len(clean_text) < 2:
            return 'unknown'
            
        # Simple rules for common words
        english_words = {'hello', 'world', 'good', 'morning', 'evening', 'thank', 'you', 'goodbye', 'how', 'are', 'what', 'is', 'your', 'name', 'the', 'and', 'or', 'but'}
        vietnamese_words = {'xin', 'chào', 'cảm', 'ơn', 'tạm', 'biệt', 'bạn', 'khỏe', 'không', 'tên', 'là', 'gì', 'thế', 'giới', 'việt', 'nam'}
        german_words = {'hallo', 'welt', 'guten', 'tag', 'morgen', 'danke', 'auf', 'wiedersehen', 'wie', 'geht', 'dir'}
        
        text_words = set(clean_text.split())
        
        # Check for mixed language scenarios
        lang_matches = 0
        detected_languages = []
        
        if text_words.intersection(english_words):
            lang_matches += 1
            detected_languages.append('en')
        if text_words.intersection(vietnamese_words):
            lang_matches += 1
            detected_languages.append('vi')
        if text_words.intersection(german_words):
            lang_matches += 1
            detected_languages.append('de')
        
        # If multiple languages detected in same text, it's mixed
        if lang_matches > 1:
            print(f"Mixed language detected: {detected_languages} in text: '{text}'")
            return 'mixed'
        
        # Single language detection
        if lang_matches == 1:
            return detected_languages[0]
            
        # Fall back to langdetect for longer texts
        if len(clean_text) >= 10:
            detected_lang = detect(clean_text)
            
            # Map some language codes to our supported codes
            lang_mapping = {
                'zh-cn': 'zh',
                'zh-tw': 'zh',
                'ja': 'ja',
                'ko': 'ko'
            }
            
            return lang_mapping.get(detected_lang, detected_lang)
        
        # Default to English for short unknown texts
        return 'en'
        
    except Exception as e:
        print(f"Language detection error: {e}")
        return 'en'  # Default to English instead of unknown

def google_translate(text, src_lang="auto", dest_lang="vi"):
    """
    Hàm dịch sử dụng Google Translator.
    
    Args:
        text (str): Văn bản cần dịch
        src_lang (str): Ngôn ngữ nguồn (mặc định "auto")
        dest_lang (str): Ngôn ngữ đích (mặc định "vi")
        
    Returns:
        dict: Kết quả dịch với các trường text, src, dest
    """
    try:
        model = GoogleTranslator()
        
        if src_lang == "auto":
            result = model.translate(text, dest=dest_lang)
        else:
            result = model.translate(text, src=src_lang, dest=dest_lang)
        
        # Handle both sync and async results
        if hasattr(result, '__await__'):
            # If result is a coroutine, we need to handle it differently
            import asyncio
            try:
                # Try to run the coroutine
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create a new thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, result)
                        result = future.result(timeout=10)
                else:
                    result = loop.run_until_complete(result)
            except:
                # If async handling fails, try sync approach
                result = asyncio.run(result)
        
        # Now handle the result
        if hasattr(result, 'text') and hasattr(result, 'src'):
            return {
                "text": result.text,
                "src": result.src,
                "dest": dest_lang
            }
        else:
            # If result format is unexpected, try to extract text
            return {
                "text": str(result),
                "src": src_lang,
                "dest": dest_lang
            }
            
    except Exception as e:
        return {
            "text": f"Lỗi dịch: {e}",
            "src": src_lang,
            "dest": dest_lang
        }

def bing_translate(text, src_lang="auto", dest_lang="vi"):
    """
    Hàm dịch sử dụng Bing Translator (placeholder - cần cài đặt thư viện).
    """
    # TODO: Implement Bing Translator
    return {
        "text": f"[Bing] {text} (Chưa hỗ trợ)",
        "src": src_lang,
        "dest": dest_lang
    }

def deepl_translate(text, src_lang="auto", dest_lang="vi"):
    """
    Hàm dịch sử dụng DeepL Translator (placeholder - cần cài đặt thư viện).
    """
    # TODO: Implement DeepL Translator
    return {
        "text": f"[DeepL] {text} (Chưa hỗ trợ)",
        "src": src_lang,
        "dest": dest_lang
    }

def marian_translate(text, src_lang="auto", dest_lang="vi"):
    """
    Hàm dịch sử dụng Marian MT với models đã download - Dynamic version
    With fallback for PyInstaller builds
    
    Args:
        text (str): Văn bản cần dịch
        src_lang (str): Ngôn ngữ nguồn (mặc định "auto")
        dest_lang (str): Ngôn ngữ đích (mặc định "vi")
        
    Returns:
        dict: Kết quả dịch với các trường text, src, dest
    """
    try:
        # Check transformers availability (cached check)
        transformers_available = _check_transformers_availability()
        
        from VezylTranslatorProton.marian_module import MarianModelManager
        manager = MarianModelManager()
        
        # Auto-detect language if needed
        if src_lang == "auto":
            detected_lang = detect_language(text)
            if detected_lang == 'unknown':
                # Fallback to English
                src_lang = "en"
            elif detected_lang == 'mixed':
                # Mixed language detected - use smart mixed handling
                print(f"Mixed language detected in '{text}', using smart translation")
                return _translate_mixed_language_smart(text, dest_lang)
            else:
                src_lang = detected_lang
        
        # FIRST: Try dictionary for basic/common words (more reliable)
        translations = _get_marian_translations_dict()
        model_dict_key = (src_lang, dest_lang)
        if model_dict_key in translations:
            text_lower = text.lower().strip()
            if text_lower in translations[model_dict_key]:
                translated = translations[model_dict_key][text_lower]
                return {
                    "text": translated,
                    "src": src_lang,
                    "dest": dest_lang
                }
        
        # SECOND: Try AI model for complex sentences (only if transformers available)
        if transformers_available:
            model_key = f"{src_lang}-{dest_lang}"
            model_path = manager.get_model_path(model_key)
            
            # Try direct translation first
            if model_path:
                try:
                    result = _translate_with_model(text, model_path, src_lang, dest_lang)
                    if result:
                        return result
                except Exception as e:
                    print(f"Error with direct model {model_key}: {e}")
            
            # Try through English if no direct model
            if src_lang != "en" and dest_lang != "en":
                # Step 1: src -> en
                en_model_key = f"{src_lang}-en"
                en_model_path = manager.get_model_path(en_model_key)
                
                if en_model_path:
                    try:
                        en_result = _translate_with_model(text, en_model_path, src_lang, "en")
                        if en_result and en_result.get("text"):
                            english_text = en_result["text"]
                            
                            # Step 2: en -> dest
                            dest_model_key = f"en-{dest_lang}"
                            dest_model_path = manager.get_model_path(dest_model_key)
                            
                            if dest_model_path:
                                final_result = _translate_with_model(english_text, dest_model_path, "en", dest_lang)
                                if final_result:
                                    final_result["src"] = src_lang  # Keep original source
                                    return final_result
                                    
                    except Exception as e:
                        print(f"Error with two-step translation: {e}")
        else:
            print("Skipping AI model translation (transformers not available)")
        
        # Final fallback: return original with model indicator
        return {
            "text": f"{text}",
            "src": src_lang,
            "dest": dest_lang
        }
        
    except Exception as e:
        print(f"Marian translation error: {e}")
        return {
            "text": f"[Error: {text}]",
            "src": src_lang,
            "dest": dest_lang
        }

def _translate_with_model(text, model_path, src_lang, dest_lang):
    """
    Helper function to translate using a specific model path
    """
    try:
        # Check if required files exist
        required_files = ["pytorch_model.bin", "config.json"]
        for file in required_files:
            if not os.path.exists(os.path.join(model_path, file)):
                return None
        
        # Try to use transformers for actual translation
        try:
            # Use cached transformers (no repeated imports)
            if not _check_transformers_availability():
                print(f"Transformers not available for model {model_path}")
                return None
            
            MarianMTModel = _transformers_models['MarianMTModel']
            MarianTokenizer = _transformers_models['MarianTokenizer']
            
            # Load model and tokenizer with caching
            if model_path not in _model_cache:
                print(f"Loading model for {model_path}...")
                _model_cache[model_path] = MarianMTModel.from_pretrained(model_path, local_files_only=True)
                _tokenizer_cache[model_path] = MarianTokenizer.from_pretrained(model_path, local_files_only=True)
                print(f"Model loaded and cached for {model_path}")
            
            model = _model_cache[model_path]
            tokenizer = _tokenizer_cache[model_path]
            
            # Prepare text for translation
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # Use threading for timeout
            result_container = [None]
            exception_container = [None]
            
            def generate_with_timeout():
                try:
                    # Generate translation with anti-repetition parameters
                    outputs = model.generate(
                        **inputs, 
                        max_length=min(len(text.split()) * 3 + 10, 128),  # Dynamic max length
                        min_length=1,
                        num_beams=2,  # Reduced beams for speed
                        early_stopping=True,
                        no_repeat_ngram_size=3,  # Prevent 3-gram repetition
                        repetition_penalty=1.5,  # Higher penalty for repetition
                        do_sample=False,
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                    result_container[0] = outputs
                except Exception as e:
                    exception_container[0] = e
            
            # Start generation in thread with timeout
            thread = threading.Thread(target=generate_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout=5.0)  # 5 second timeout
            
            if thread.is_alive():
                print(f"Model generation timed out for text: {text}")
                return None  # Force fallback
            
            if exception_container[0]:
                raise exception_container[0]
            
            if result_container[0] is None:
                print(f"Model generation failed for text: {text}")
                return None
            
            outputs = result_container[0]
            
            # Decode the result
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Additional check for repetition
            words = translated_text.split()
            if len(words) > 10:
                # Check if more than 50% of words are the same
                unique_words = set(words)
                if len(unique_words) / len(words) < 0.5:
                    print(f"Warning: Detected repetition in output, using fallback")
                    return None  # Force fallback to dictionary
            
            return {
                "text": translated_text,
                "src": src_lang,
                "dest": dest_lang
            }
            
        except ImportError:
            # If transformers is not available, use simple mapping
            print("Transformers library not available, using simple mapping")
            return None
        except Exception as e:
            print(f"Model execution error: {e}")
            return None
            
    except Exception as e:
        print(f"Model loading error: {e}")
        return None

def opus_translate(text, src_lang="auto", dest_lang="vi"):
    """
    Hàm dịch sử dụng OPUS-MT (placeholder - cần model local).
    """
    # TODO: Implement OPUS-MT
    return {
        "text": f"[OPUS] {text} (Chưa hỗ trợ)",
        "src": src_lang,
        "dest": dest_lang
    }

def translate_with_model(text, src_lang="auto", dest_lang="vi", model_name="google"):
    """
    Hàm dịch trung gian, dễ thay đổi model dịch sau này.
    
    Args:
        text (str): Văn bản cần dịch
        src_lang (str): Ngôn ngữ nguồn (mặc định "auto")
        dest_lang (str): Ngôn ngữ đích (mặc định "vi")
        model_name (str): Tên model dịch (google, bing, deepl, marian, opus)
        model: Model dịch tùy chỉnh (nếu có)
        
    Returns:
        dict: Kết quả dịch với các trường text, src, dest
    """
    # Sử dụng model theo tên
    if model_name == "google":
        return google_translate(text, src_lang, dest_lang)
    elif model_name == "bing":
        return bing_translate(text, src_lang, dest_lang)
    elif model_name == "deepl":
        return deepl_translate(text, src_lang, dest_lang)
    elif model_name == "marian":
        return marian_translate(text, src_lang, dest_lang)
    elif model_name == "opus":
        return opus_translate(text, src_lang, dest_lang)
    else:
        # Fallback to Google Translator
        return google_translate(text, src_lang, dest_lang)