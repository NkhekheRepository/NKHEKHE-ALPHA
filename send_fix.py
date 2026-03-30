#!/usr/bin/env python3
import requests
BOT_TOKEN = "8748820504:AAEoIEzrFLIXD2w9H9in5V_2yVd15le3Qx4"
CHAT_ID = "7361240735"
MESSAGE = """🔧 *FIX APPLIED*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *Issue:* Still receiving 30s reports

🔍 *Root Cause:* Old process was still running

✅ *Fix Applied:*
• Killed old process (PID 63851)
• Updated report_interval to 10800 (3 hours)
• Updated startup message
• Updated docstring

📊 *New Bot Started:*
• Reports every 3 hours
• Running on testnet
• 75x leverage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
              data={"chat_id": CHAT_ID, "text": MESSAGE, "parse_mode": "Markdown"})
