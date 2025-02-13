import json
import time
import requests
import subprocess
import os
from datetime import datetime

# 🔧 CONFIGURATION / KONFIGURÁCIA

# 🛑 Insert your Discord Webhook URL here! / Vložte svoj Discord Webhook URL sem!
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")

WATCHLIST_FILE = "/opt/watchlist.txt"  # File with domains to watch / Súbor s doménami na sledovanie
LOG_FILE = "/opt/AdGuardHome/data/querylog.json"  # AdGuard log file / Logovací súbor AdGuard Home
LAST_SEEN_FILE = "/opt/adguard_discord_last_seen.txt"  # File for saving last seen logs / Súbor na ukladanie posledných logov

# 🔄 Notification settings / Nastavenia notifikácií
NOTIFICATION_INTERVAL = int(os.getenv("NOTIFICATION_INTERVAL", 30))  # Min time between notifications (sec) / Min. čas medzi notifikáciami (sek)
CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION", 60))  # Cache expiration time (sec) / Expirácia cache (sek)
FILTER_SUBDOMAINS = bool(int(os.getenv("FILTER_SUBDOMAINS", 1)))  # Filter subdomains? / Filtrovať subdomény? (1 = Yes, 0 = No)

# 🔄 Cache to prevent duplicate notifications / Cache na zamedzenie duplicitných notifikácií
notification_cache = {}

def load_watchlist():
    """Load watched domains from file / Načíta sledované domény zo súboru."""
    try:
        with open(WATCHLIST_FILE, "r") as f:
            domains = [line.strip().replace("http://", "").replace("https://", "") for line in f if line.strip()]
            return set(domains)  # Using set for fast lookup / Používame set na rýchle vyhľadávanie
    except FileNotFoundError:
        return set()

def send_discord_notification(messages):
    """Send notification to Discord / Odoslanie notifikácie na Discord."""
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
                print("✅ Notification sent / Notifikácia odoslaná.")
            else:
                print(f"❌ Error sending to Discord: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error sending to Discord: {e}")

        time.sleep(1)  # Prevent rate-limiting / Prevencia rate-limitov

def parse_time(timestamp_str):
    """Convert ISO8601 time to UNIX timestamp / Konverzia ISO8601 času na UNIX timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp_str.rstrip("Z"))
        return dt.timestamp(), dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"❌ Error parsing time: {e}")
        return 0, "Unknown time / Neznámy čas"

def read_last_seen_time():
    """Load last seen log timestamp / Načíta posledný čas záznamu."""
    try:
        with open(LAST_SEEN_FILE, "r") as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_last_seen_time(timestamp):
    """Save last seen log timestamp / Uloží posledný čas záznamu do súboru."""
    try:
        with open(LAST_SEEN_FILE, "w") as f:
            f.write(str(timestamp))
    except PermissionError:
        print("❌ Error: No permission to write last_seen_time!")

def read_query_log():
    """Read last 100 lines of AdGuard query log / Čítanie posledných 100 riadkov logu."""
    log_entries = []
    try:
        output = subprocess.run(["sudo", "tail", "-n", "100", LOG_FILE], capture_output=True, text=True)
        log_lines = output.stdout.strip().split("\n")

        for line in log_lines:
            try:
                entry = json.loads(line)
                log_entries.append(entry)
            except json.JSONDecodeError:
                print(f"❌ Error decoding JSON: {line[:100]}...")

        return log_entries
    except Exception as e:
        print(f"❌ Error reading logs: {e}")
        return []

def should_notify(domain):
    """Check if domain should be reported (cache and subdomain filtering) / Kontrola, či má byť doména nahlásená (cache a filtrovanie subdomén)."""
    global notification_cache
    now = time.time()

    if FILTER_SUBDOMAINS:
        parts = domain.split(".")
        if len(parts) > 2:
            domain = ".".join(parts[-2:])  # Keep only main domain / Zachovaj len hlavnú doménu

    # Check cache to prevent spam / Kontrola cache na prevenciu spamu
    if domain in notification_cache and (now - notification_cache[domain]) < CACHE_EXPIRATION:
        return False  # Already sent, skipping / Už bolo odoslané, preskakujeme

    notification_cache[domain] = now  # Update cache / Aktualizácia cache
    return True

def monitor_logs():
    """Monitor AdGuard logs and send notifications / Monitorovanie logov a posielanie notifikácií."""
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

            # 🔍 DEBUG: Check read logs / Kontrola načítaných logov
            print(f"📌 DEBUG: {timestamp} - {domain} - {client_ip}")

            # If domain is in watchlist (including subdomains if enabled) / Ak sa doména nachádza v sledovaných
            if any(watch in domain for watch in watchlist):
                if should_notify(domain) and timestamp > last_seen_time:
                    new_notifications.append(f"🔔 **ALERT!**\n📅 **Date & Time:** {readable_time}\n📌 **User:** `{client_ip}`\n🌐 **Website:** `{domain}`")
                    last_seen_time = timestamp

        if new_notifications and (time.time() - last_notification_time) >= NOTIFICATION_INTERVAL:
            send_discord_notification(new_notifications)
            save_last_seen_time(last_seen_time)
            last_notification_time = time.time()

        time.sleep(5)

if __name__ == "__main__":
    monitor_logs()
