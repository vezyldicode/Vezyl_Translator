import base64

def encode_base64(data, filename=None):
    """
    Mã hóa dữ liệu sang base64.
    - Nếu gọi từ main (filename != None): ghi ra file .txt và return None.
    - Nếu import từ chương trình khác (filename=None): trả về chuỗi base64.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    encoded = base64.b64encode(data).decode('utf-8')
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(encoded)
        return None
    return encoded

def decode_base64(encoded_data):
    """
    Giải mã base64, trả về dữ liệu gốc dạng bytes.
    """
    if isinstance(encoded_data, str):
        encoded_data = encoded_data.encode('utf-8')
    return base64.b64decode(encoded_data)

if __name__ == "__main__":
    encode_base64("Hello world!", "Vezylcrypto.txt")