import os
import requests

def send_log_to_discord_webhook(log_path, webhook_url):
    with open(log_path, "rb") as f:
        files = {
            "file": (os.path.basename(log_path), f, "text/plain")
        }
        data = {
            "content": "Test: Crash log file attached."
        }
        response = requests.post(webhook_url, data=data, files=files)
        response.raise_for_status()
        print("Sent successfully!")

if __name__ == "__main__":
    log_path = "local/log/test_log.txt"
    # Cách 1: Lấy từ biến môi trường
    # webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    # Cách 2: Gán trực tiếp
    webhook_url = "https://discord.com/api/webhooks/1383762481184505856/F9v2CDRnkiMs13PzDsGEPAgV5XB-RkPwDo56FCK53qygYmrcg61zl_Fcsy2sfKODG4B7"

    if not os.path.exists(log_path):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("This is a test log for Discord webhook.\n")

    if not webhook_url:
        print("Please set the DISCORD_WEBHOOK_URL environment variable or assign webhook_url directly.")
    else:
        try:
            send_log_to_discord_webhook(log_path, webhook_url)
        except Exception as e:
            print(f"Failed to send log to Discord: {e}")