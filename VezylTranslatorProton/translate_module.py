from googletrans import Translator as GoogleTranslator

def translate_with_model(text, src_lang="auto", dest_lang="vi", model=None):
    """
    Hàm dịch trung gian, dễ thay đổi model dịch sau này.
    """
    if not model:
        model = GoogleTranslator()
        print("Google Translator")
    else:
        print("Using custom model:", model)
    try:
        print("trying to translate")
        if src_lang == "auto":
            result = model.translate(text, dest=dest_lang)
        else:
            result = model.translate(text, src=src_lang, dest=dest_lang)
        return {
            "text": result.text,
            "src": result.src,
            "dest": dest_lang
        }
    except Exception as e:
        return {
            "text": f"Lỗi dịch: {e}",
            "src": src_lang,
            "dest": dest_lang
        }