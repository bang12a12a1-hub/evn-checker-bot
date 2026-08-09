import os
import sys
import time
import threading
import requests
import argparse

from typing import Optional, Dict, List

# Fix UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evn_checker.checker import EVNBillChecker, detect_region
from evn_checker.cli import extract_customer_codes
from evn_checker.models import EVNRegion



class EVNTelegramBot:
    def __init__(self, token: str):
        self.token = token.strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.checker = EVNBillChecker(use_playwright_fallback=False)
        self.offset = 0

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML"):
        """Sends message to a Telegram chat."""
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Loi gui tin nhan Telegram: {e}")

    def format_bot_response(self, results) -> str:
        """Formats bill check results into clean Telegram HTML text.
        
        Always uses same clean format:
        - is_paid=True  -> checkmark + DA THANH TOAN
        - is_paid=False -> X + CHUA THANH TOAN + debt amount
        - error/fail    -> X + CHUA THANH TOAN (Khong tra cuu duoc)
        """
        total = len(results)
        paid_count = sum(1 for r in results if r.is_paid)
        unpaid_count = total - paid_count

        lines = []
        lines.append(f"<b>\u26a1 K\u1ebe\u0301T QUA\u0309 TRA C\u01af\u0301U EVN ({total} M\u00c3)</b>\n")
        if paid_count > 0:
            lines.append(f"\u2705 <b>\u0110\u00e3 thanh to\u00e1n:</b> {paid_count} m\u00e3")
        if unpaid_count > 0:
            lines.append(f"\u274c <b>Ch\u01b0a thanh to\u00e1n:</b> {unpaid_count} m\u00e3")
        lines.append("\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n")

        for idx, r in enumerate(results, 1):
            code = r.customer_code
            region = r.region.value

            lines.append(f"<b>{idx}. \ud83d\udccc <code>{code}</code></b>")
            lines.append(f"   \ud83c\udfe2 {region}")

            if r.is_paid:
                lines.append(f"   \u2705 <b>Tr\u1ea1ng th\u00e1i:</b> \u0110\u00c3 THANH TO\u00c1N (0 VN\u0110)\n")
            else:
                debt = r.total_debt
                if debt > 0:
                    lines.append(f"   \u274c <b>Tr\u1ea1ng th\u00e1i:</b> CH\u01af\u0301A THANH TO\u00c1N ({debt:,.0f} VN\u0110)\n")
                else:
                    lines.append(f"   \u274c <b>Tr\u1ea1ng th\u00e1i:</b> CH\u01af\u0301A THANH TO\u00c1N\n")

        return "\n".join(lines)

    def process_message(self, message: dict):
        """Processes an incoming Telegram message."""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            return

        if text.startswith("/start") or text.startswith("/help"):
            welcome_msg = (
                "\ud83d\udc4b <b>Xin ch\u00e0o! T\u00f4i l\u00e0 Bot Tra C\u01b0\u0301u H\u00f3a \u0110\u01a1n \u0110i\u1ec7n EVN To\u00e0n Qu\u1ed1c.</b>\n\n"
                "\ud83d\udca1 <b>C\u00e1ch d\u00f9ng:</b> B\u1ea1n ch\u1ec9 c\u1ea7n d\u00e1n \u0111o\u1ea1n v\u0103n b\u1ea3n ch\u1ee9a 1 ho\u1eb7c nhi\u1ec1u M\u00e3 KH \u0111i\u1ec7n v\u00e0o \u0111\u00e2y.\n"
                "<i>V\u00ed d\u1ee5:</i>\n"
                "<code>PC01BB0290022  1,530,403</code>\n"
                "<code>PC01BB0308544  1,536,207</code>"
            )
            self.send_message(chat_id, welcome_msg)
            return

        # Extract codes
        codes = extract_customer_codes(text)

        if not codes:
            self.send_message(
                chat_id,
                "\u26a0\ufe0f Kh\u00f4ng t\u00ecm th\u1ea5y M\u00e3 Kh\u00e1ch H\u00e0ng EVN h\u1ee3p l\u1ec7 trong tin nh\u1eafn c\u1ee7a b\u1ea1n.\n"
                "M\u00e3 EVN h\u1ee3p l\u1ec7 b\u1eaft \u0111\u1ea7u b\u1eb1ng: <code>PE</code> (HCM), <code>PD</code> (H\u00e0 N\u1ed9i), <code>PA/PB</code> (Mi\u1ec1n B\u1eafc), <code>PC/PS</code> (Mi\u1ec1n Nam), <code>PP/PQ</code> (Mi\u1ec1n Trung)."
            )
            return

        # Send status update
        self.send_message(chat_id, f"\u23f3 \u0110ang tra c\u01b0\u0301u {len(codes)} m\u00e3 EVN, vui l\u00f2ng \u0111\u1ee3i gi\u00e2y l\u00e1t...")

        # Run checks
        results = self.checker.check_batch(codes)
        response_text = self.format_bot_response(results)

        # Send result back
        self.send_message(chat_id, response_text)

    def run_polling(self):
        """Runs long-polling loop to listen for new Telegram updates."""
        print("Telegram Bot EVN Bill Checker dang chay...")
        print("Nhan Ctrl+C de dung Bot.")
        
        while True:
            try:
                url = f"{self.api_url}/getUpdates"
                params = {"offset": self.offset, "timeout": 20}
                resp = requests.get(url, params=params, timeout=25)
                
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        self.offset = update["update_id"] + 1
                        if "message" in update:
                            self.process_message(update["message"])
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nBot da dung.")
                break
            except Exception as e:
                print(f"Loi ket noi polling Telegram: {e}")
                time.sleep(3)

def start_dummy_http_server():
    """Starts a minimal HTTP server so Render Web Service health checks pass."""
    import http.server
    import socketserver
    port = int(os.environ.get("PORT", 8080))
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"EVN Bot is running!")
        def log_message(self, format, *args):
            pass  # Suppress logs
    try:
        httpd = socketserver.TCPServer(("", port), HealthHandler)
        print(f"HTTP Health Check Server running on port {port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"HTTP server notice: {e}")

def main():
    parser = argparse.ArgumentParser(description="Chay Telegram Bot Tra Cuu EVN")
    parser.add_argument("token", nargs="?", help="Telegram Bot Token lay tu @BotFather")
    args = parser.parse_args()

    DEFAULT_TOKEN = "8972194053:AAFk83IeojjcLXxUBe_jFJuYO4Lg24rsS-k"
    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN") or DEFAULT_TOKEN

    if not token:
        print("Thieu Telegram Bot Token!")
        sys.exit(1)

    # Start dummy HTTP server in a daemon thread if PORT is defined (for Render Web Service)
    if "PORT" in os.environ:
        t = threading.Thread(target=start_dummy_http_server, daemon=True)
        t.start()

    bot = EVNTelegramBot(token)
    bot.run_polling()


if __name__ == "__main__":
    main()
