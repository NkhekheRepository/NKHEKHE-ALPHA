#!/usr/bin/env python3
"""
Send update notification to Telegram
"""

import requests

BOT_TOKEN = "8748820504:AAEoIEzrFLIXD2w9H9in5V_2yVd15le3Qx4"
CHAT_ID = "7361240735"

MESSAGE = """
🔔 *SYSTEM UPDATE*

✅ Autonomous Trading Decision Reports
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *Change Made:*
• Report Interval: 30 seconds → 3 hours

📁 *Files Updated:*
• autonomous_trading.py
• paper_trading/config/unified.yaml

💡 *Note:* Daily reports still work as before.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 GitHub: github.com/NkhekheRepository/NKHEKHE-ALPHA
"""

def send_message(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data, timeout=30)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    success = send_message(BOT_TOKEN, CHAT_ID, MESSAGE)
    print("✅ Update sent" if success else "❌ Failed")
