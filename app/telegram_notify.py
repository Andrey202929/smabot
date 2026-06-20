import os
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("[telegram_notify] TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set in env")

bot = Bot(token=TELEGRAM_TOKEN)

def _format_signal_text(signal: dict) -> str:
    side = signal["side"].upper()
    header = "🟢 <b>BUY SIGNAL</b>" if side == "BUY" else "🔴 <b>SELL SIGNAL</b>"
    reasons = signal.get("reason", []) or []
    reason_text = "\n".join(f"• {r}" for r in reasons) if reasons else ""
    txt = (
        f"{header}\n\n"
        f"<b>Asset:</b> {signal['asset']}\n"
        f"<b>HTF Context:</b> {signal.get('htf_context','')}\n"
        f"<b>HTF Zone:</b> {signal.get('htf_zone','')}\n"
        f"<b>LTF Trigger:</b> {signal.get('ltf_trigger','')}\n"
        f"<b>Liquidity Taken:</b> {signal.get('liquidity_taken','')}\n\n"
        f"<b>Entry:</b> {signal['entry']}\n"
        f"<b>Stop Loss:</b> {signal['stop_loss']}\n"
        f"<b>Take Profit:</b> {signal['take_profit']}\n\n"
        f"<b>RR:</b> {signal['rr']}\n"
        f"<b>AI Confidence:</b> {signal['confidence']}%\n\n"
        f"<b>Reason:</b>\n{reason_text}"
    )
    return txt

async def send_signal_message(signal: dict, max_retries: int = 3):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Telegram credentials missing in environment")

    text = _format_signal_text(signal)
    attempt = 0
    while attempt < max_retries:
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return True
        except TelegramError as e:
            attempt += 1
            wait = 2 ** attempt
            print(f"[telegram_notify] send attempt {attempt} failed: {e}; retrying in {wait}s")
            await asyncio.sleep(wait)
        except Exception as e:
            print(f"[telegram_notify] unexpected error: {e}")
            raise
    return False
