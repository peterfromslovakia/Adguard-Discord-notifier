import json
import time
import requests
import subprocess
import os
from datetime import datetime

# 🔧 Configuration (Konfigurácia)
# ❗ Replace "YOUR_DISCORD_WEBHOOK_URL" with your actual Discord webhook URL.
# ❗ Nahraďte "YOUR_DISCORD_WEBHOOK_URL" svojím skutočným webhookom.
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL")

WATCHLIST_FILE = "/opt/watchlist.txt"
LOG_FILE = "/opt/AdGuardHome/data/querylog.json"
LAST_SEEN_FILE = "/opt/adguard_discord_last_seen.txt"
NOTIFICATION_INTERVAL = int(os.getenv("NOTIFICATION_INTERVAL", 30))  # Interval medzi notifikáciami
CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION", 60))  # Cache na duplikáty
FILTER_SUBDOMAINS = bool(int(os.getenv("FILTER_SUBDOMAINS", 1)))  # 1 = zapnuté, 0 = vypnuté

# Cache pre už notifikované domény (časové razítka)
notification_cache = {}

def load_watchlist():
    """Načíta sledované domény zo súboru."""
    try:
        with open(WATCHLIST_FILE, "r") as f:
            domains = [line.strip().replace("http://", "").replace("https://", "") for line in f if line.strip()]
            return set(domains)  # Použijeme set pre rýchle vyhľadávanie
    except FileNotFoundError:
        return set()

def send_discord_notification(messages):
    """Odoslanie notifikácie na Discord."""
    if not messages or DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL":
        print("❌ Webhook URL is missing. Please configure DISCORD_WEBHOOK_URL.")
        return

    MAX_LENGTH = 1900
    message_content = "\n".join(messages)
    chunks = [message_content[i:i+MAX_LENGTH] for i in range(0, len(message_content), MAX_LENGTH)]

    for chunk in chunks:
        payload = {"content": chunk}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code == 204:
                print("✅ Notification sent.")
            else:
                print(f"❌ Error sending to Discord: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error sending to Discord: {e}")

        time.sleep(1)  # Prevencia rate-limitov

def parse_time(timestamp_str):
    """Konverzia ISO8601 času na UNIX timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp_str.rstrip("Z"))
        return dt.timestamp(), dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"❌ Chyba pri parsovaní času: {e}")
        return 0, "Neznámy čas"

def read_last_seen_time():
    """Načíta posledný čas záznamu."""
    try:
        with open(LAST_SEEN_FILE, "r") as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_last_seen_time(timestamp):
    """Uloží posledný čas záznamu do súboru."""
    try:
        with open(LAST_SEEN_FILE, "w") as f:
            f.write(str(timestamp))
    except PermissionError:
        print("❌ Chyba: Nemám oprávnenie zapisovať do last_seen_time!")

def read_query_log():
    """Čítanie posledných 100 riadkov logu."""
    log_entries = []
    try:
        output = subprocess.run(["sudo", "tail", "-n", "100", LOG_FILE], capture_output=True, text=True)
        log_lines = output.stdout.strip().split("\n")

        for line in log_lines:
            try:
                entry = json.loads(line)
                log_entries.append(entry)
            except json.JSONDecodeError:
                print(f"❌ Chyba pri dekódovaní JSON: {line[:100]}...")

        return log_entries
    except Exception as e:
        print(f"❌ Chyba pri čítaní logov: {e}")
        return []

def should_notify(domain):
    """Kontrola, či má byť doména nahlásená (podľa cache a filtra poddomén)."""
    global notification_cache
    now = time.time()

    if FILTER_SUBDOMAINS:
        parts = domain.split(".")
        if len(parts) > 2:
            domain = ".".join(parts[-2:])

    if domain in notification_cache and (now - notification_cache[domain]) < CACHE_EXPIRATION:
        return False  # Už sme poslali notifikáciu, počkáme

    notification_cache[domain] = now
    return True

def monitor_logs():
    """Monitorovanie logov a posielanie notifikácií."""
    last_seen_time = read_last_seen_time()
    last_notification_time = time.time()

    while True:
        watchlist = load_watchlist()
        log_data = read_query_log()
        if not log_data:
            time.sleep(5)
            continue

        new_notifications = []
        for entry in log_data:
            timestamp_str = entry.get("T", "")
            timestamp, readable_time = parse_time(timestamp_str)
            domain = entry.get("QH", "").replace("http://", "").replace("https://", "")
            client_ip = entry.get("IP", "")

            print(f"📌 DEBUG: {timestamp} - {domain} - {client_ip}")

            if any(watch in domain for watch in watchlist):
                if should_notify(domain) and timestamp > last_seen_time:
                    new_notifications.append(f"🔔 **Alert!**\n📅 **Date & Time:** {readable_time}\n📌 **User:** `{client_ip}`\n🌐 **Site:** `{domain}`")
                    last_seen_time = timestamp

        if new_notifications and (time.time() - last_notification_time) >= NOTIFICATION_INTERVAL:
            send_discord_notification(new_notifications)
            save_last_seen_time(last_seen_time)
            last_notification_time = time.time()

        time.sleep(5)

if __name__ == "__main__":
    monitor_logs()
