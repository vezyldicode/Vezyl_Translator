import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def get_aes_key(language_interface, theme_interface):
    theme_ui = language_interface + theme_interface
    return base64.b64decode(theme_ui)

def pad(data: bytes) -> bytes:
    pad_len = 16 - len(data) % 16
    return data + bytes([pad_len] * pad_len)

def unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    return data[:-pad_len]

def encrypt_aes(text, key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = text.encode('utf-8')
    ct_bytes = cipher.encrypt(pad(data))
    return base64.b64encode(iv + ct_bytes).decode('utf-8')

def decrypt_aes(enc_text, key):
    raw = base64.b64decode(enc_text)
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = cipher.decrypt(ct)
    return unpad(pt).decode('utf-8')