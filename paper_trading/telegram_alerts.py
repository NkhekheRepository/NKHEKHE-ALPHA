#!/usr/bin/env python3
"""
Telegram Alert Module for Live Trading
======================================
Sends alerts to Telegram when trades are executed.
"""

import os
import requests
from typing import Dict, Any, Optional
from loguru import logger

TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"


class TelegramAlerts:
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = chat_id or os.getenv('ADMIN_CHAT_IDS', '')
        self.enabled = bool(self.token and self.chat_id)
        
        if self.enabled:
            logger.info(f"Telegram alerts enabled for chat {self.chat_id}")
        else:
            logger.warning("Telegram alerts disabled - no token/chat_id")
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        if not self.enabled:
            return False
        
        try:
            url = TELEGRAM_API_URL.format(self.token)
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram alert sent: {text[:50]}...")
                return True
            else:
                logger.error(f"Telegram send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    def send_trade_alert(self, action: str, symbol: str, quantity: float, price: float):
        emoji = "🟢" if action.upper() == "BUY" else "🔴"
        
        text = f"""
{emoji} <b>TRADE EXECUTED</b>

<b>Action:</b> {action.upper()}
<b>Symbol:</b> {symbol}
<b>Quantity:</b> {quantity}
<b>Price:</b> ${price:,.2f}
<b>Total:</b> ${quantity * price:,.2f}
"""
        return self.send_message(text)
    
    def send_signal_alert(self, signal: str, symbol: str, price: float, confidence: float):
        emoji = "📈" if signal.upper() == "BUY" else "📉" if signal.upper() == "SELL" else "⏸️"
        
        text = f"""
{emoji} <b>TRADING SIGNAL</b>

<b>Signal:</b> {signal.upper()}
<b>Symbol:</b> {symbol}
<b>Price:</b> ${price:,.2f}
<b>Confidence:</b> {confidence:.1%}
"""
        return self.send_message(text)
    
    def send_status_alert(self, status: Dict[str, Any]):
        text = f"""
🔄 <b>SYSTEM STATUS</b>

<b>Running:</b> {status.get('running', False)}
<b>Symbol:</b> {status.get('symbol', 'N/A')}
<b>Balance:</b> ${status.get('balance', 0):,.2f}
<b>Price:</b> ${status.get('price', 0):,.2f}
"""
        return self.send_message(text)
    
    def send_error_alert(self, error: str):
        text = f"""
⚠️ <b>ERROR ALERT</b>

{error}
"""
        return self.send_message(text)


telegram_alerts = TelegramAlerts()
