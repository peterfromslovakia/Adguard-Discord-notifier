import json
import time
import requests
import subprocess
import os
from datetime import datetime

# 🔧 Konfigurácia
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://ptb.discord.com/api/webhooks/1339233888425214034/-EKfY9udBgIrpSztd2ftKlMqxMql7Wa4vN6rgb8x4d4tfl-EUAVrcg6DTg6dTSPFumiQ")

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
    if not messages:
        return

    MAX_LENGTH = 1900
    message_content = "\n".join(messages)
    chunks = [message_content[i:i+MAX_LENGTH] for i in range(0, len(message_content), MAX_LENGTH)]

    for chunk in chunks:
        payload = {"content": chunk}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code == 204:
                print("✅ Notifikácia odoslaná.")
            else:
                print(f"❌ Chyba pri odosielaní na Discord: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Chyba pri odosielaní na Discord: {e}")

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
        # Extrahujeme hlavnú doménu
        parts = domain.split(".")
        if len(parts) > 2:
            domain = ".".join(parts[-2:])

    # Kontrola cache (zamedzenie spamu)
    if domain in notification_cache and (now - notification_cache[domain]) < CACHE_EXPIRATION:
        return False  # Už sme poslali notifikáciu, počkáme

    notification_cache[domain] = now  # Aktualizácia cache
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

            # 🔍 DEBUG výpis – kontrolujeme načítané záznamy
            print(f"📌 DEBUG: {timestamp} - {domain} - {client_ip}")

            # Ak sa doména nachádza v sledovaných (vrátane subdomén, ak FILTER_SUBDOMAINS je zapnuté)
            if any(watch in domain for watch in watchlist):
                if should_notify(domain) and timestamp > last_seen_time:
                    new_notifications.append(f"🔔 **Upozornenie!**\n📅 **Dátum & Čas:** {readable_time}\n📌 **Používateľ:** `{client_ip}`\n🌐 **Stránka:** `{domain}`")
                    last_seen_time = timestamp

        if new_notifications and (time.time() - last_notification_time) >= NOTIFICATION_INTERVAL:
            send_discord_notification(new_notifications)
            save_last_seen_time(last_seen_time)
            last_notification_time = time.time()

        time.sleep(5)

if __name__ == "__main__":
    monitor_logs()
