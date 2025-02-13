# Adguard-Discord-notifier

## 🌐 ENG: Monitor AdGuardHome DNS queries & notify Discord  
A Python-based script that monitors **AdGuardHome** DNS queries and sends notifications to a **Discord webhook**.

## 🇸🇰 SVK: Monitorovanie DNS požiadaviek v AdGuardHome s notifikáciami  
Skript v **Pythone**, ktorý sleduje **DNS požiadavky v AdGuardHome** a odosiela upozornenia na **Discord webhook**.

---

## 🚀 Features / Funkcie  
✅ **ENG:**  
- 🔍 Monitors **AdGuardHome** DNS queries  
- 🔔 Sends **notifications** to a Discord webhook  
- 📋 **Custom watchlist** for monitored domains  
- 🚀 Configurable **notification interval** to prevent spam  
- 🌐 **Optional subdomain filtering**  

✅ **SVK:**  
- 🔍 Monitoruje **DNS požiadavky** v AdGuardHome  
- 🔔 Posiela **notifikácie** na Discord webhook  
- 📋 **Sledovaný zoznam domén** na monitorovanie  
- 🚀 Konfigurovateľný **interval notifikácií** proti spamu  
- 🌐 Možnosť **filtrovania subdomén**  

---

## 📋 Requirements / Požiadavky  
- ✅ **Python 3.x**  
- ✅ **AdGuardHome** (s povoleným logovaním)  
- ✅ **Git** (na klonovanie repozitára)  
- ✅ **Systemd** (ak chceš automatický štart služby)  

---

## ⚙️ Installation / Inštalácia  

### 1️⃣ **Clone the repository / Klonovanie repozitára**  
```bash
cd /opt
git clone https://github.com/peterfromslovakia/Adguard-Discord-notifier.git
cd Adguard-Discord-notifier
2️⃣ Install dependencies / Inštalácia závislostí

pip3 install -r requirements.txt
📑 Configuration / Konfigurácia
🔗 Discord Webhook Setup

    Open Discord → Server Settings > Integrations > Webhooks
    Create a new webhook and copy the URL
    Edit the script adguard_discord_notifier.py:

    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"

    Save and exit

📋 Watchlist (domains to monitor) / Zoznam sledovaných domén

Modify the file watchlist.txt:

nano /opt/watchlist.txt

Example domains:

example.com
markiza.sk
joj.sk

🚀 Running the script manually / Spustenie manuálne

python3 /opt/Adguard-Discord-notifier/adguard_discord_notifier.py

🔄 Systemd Service (Auto-start) / Automatické spustenie cez systemd

    Copy service file to systemd directory

cp /opt/Adguard-Discord-notifier/adguard_notifier.service /etc/systemd/system/

Reload systemd

sudo systemctl daemon-reload

Enable & start the service

sudo systemctl enable adguard_notifier
sudo systemctl start adguard_notifier

Check status

    sudo systemctl status adguard_notifier

📜 License / Licencia

MIT License – Free to use, modify, and distribute.
📧 Contact / Kontakt

GitHub: peterfromslovakia
Feel free to contribute! 🚀

