"""
MEMBER 3 — Telegram Bot Family Alert System
==========================================
SETUP STEPS:
1. Open Telegram → search @BotFather → type /newbot
2. Give your bot a name e.g. "MedEmergencyBot"
3. Copy the TOKEN it gives you → paste below as BOT_TOKEN
4. Open your bot in Telegram → send any message
5. Run: python get_chat_id.py to get your CHAT_ID
6. Paste CHAT_ID below
7. Run: python telegram_alert.py to test
"""

import requests
import json
from datetime import datetime

# ── CONFIG — Fill these in ──────────────────────────
BOT_TOKEN = "7622745127:AAGbWp6X8m2vIM_fQwwtL4JgkwRMQNr53vQ"   # From @BotFather
CHAT_ID   = "5412048580"     # Your Telegram chat ID
# ────────────────────────────────────────────────────

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_alert(patient_name, disease, doctor, severity, confidence, location_link=None):
    """
    Send emergency alert to family via Telegram.

    Args:
        patient_name  : Patient's name
        disease       : AI predicted disease
        doctor        : Recommended specialist
        severity      : Low / Medium / Critical
        confidence    : AI confidence percentage
        location_link : Google Maps link (optional)
    """
    severity_icon = {
        "Critical": "🔴",
        "Medium":   "🟡",
        "Low":      "🟢"
    }.get(severity, "🟡")

    time_now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    message = f"""
🏥 *MEDICAL EMERGENCY ALERT*

{severity_icon} *Severity: {severity}*

👤 *Patient:* {patient_name}
🦠 *Condition:* {disease}
👨‍⚕️ *Doctor Needed:* {doctor}
📊 *AI Confidence:* {confidence}%
🕐 *Time:* {time_now}
"""

    if location_link:
        message += f"\n📍 *Live Location:* [Click Here]({location_link})"

    message += "\n\n_This is an automated alert from Medical Emergency Response System._"

    payload = {
        "chat_id":    CHAT_ID,
        "text":       message,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(TELEGRAM_URL, json=payload, timeout=10)
        data = res.json()
        if data.get("ok"):
            print(f"✅ Telegram alert sent to family for patient: {patient_name}")
            return True
        else:
            print(f"❌ Telegram error: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")
        return False


def send_custom_message(message):
    """Send any custom message to the Telegram chat."""
    payload = {
        "chat_id":    CHAT_ID,
        "text":       message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(TELEGRAM_URL, json=payload, timeout=10)
        return res.json().get("ok", False)
    except:
        return False


# ── Test it ──────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Telegram Bot alert...")
    send_alert(
        patient_name  = "Ravi Kumar",
        disease       = "Heart attack",
        doctor        = "Cardiologist",
        severity      = "Critical",
        confidence    = 96.5,
        location_link = "https://maps.google.com/?q=19.0760,72.8777"
    )
