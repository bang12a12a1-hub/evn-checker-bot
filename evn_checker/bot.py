import os
import sys
import time
import threading
import requests
import argparse

from typing import Optional

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

from evn_checker.checker import EVNBillChecker
from evn_checker.cli import extract_customer_codes



class EVNTelegramBot:
    def __init__(self, token: str):
        self.token = token.strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.checker = EVNBillChecker(use_playwright_fallback=True)
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
            print(f"Lỗi gửi tin nhắn Telegram: {e}")

    def format_bot_response(self, results) -> str:
        """Formats bill check results into clean Telegram HTML text."""
        total = len(results)
        paid_count = sum(1 for r in results if r.is_paid and r.success)
        unpaid_count = sum(1 for r in results if not r.is_paid and r.success)

        msg = [f"<b>⚡ KẾT QUẢ TRA CỨU EVN ({total} MÃ)</b>\n"]
        msg.append(f"✅ <b>Đã thanh toán:</b> {paid_count} mã")
        if unpaid_count > 0:
            msg.append(f"⚠️ <b>Chưa thanh toán:</b> {unpaid_count} mã")
        msg.append("─────────────────────\n")

        for idx, r in enumerate(results, 1):
            dict_res = r.to_dict()
            code = dict_res["customer_code"]
            region = dict_res["region"]

            if not dict_res["success"]:
                msg.append(f"<b>{idx}. 📌 <code>{code}</code></b>")
                msg.append(f"   🏢 {region}")
                msg.append(f"   ❌ <i>Lỗi: {dict_res['error']}</i>\n")
            elif dict_res["is_paid"]:
                msg.append(f"<b>{idx}. 📌 <code>{code}</code></b>")
                msg.append(f"   🏢 {region}")
                msg.append(f"   ✅ <b>Trạng thái:</b> ĐÃ THANH TOÁN (0 VNĐ)\n")
            else:
                msg.append(f"<b>{idx}. 📌 <code>{code}</code></b>")
                msg.append(f"   🏢 {region}")
                msg.append(f"   ⚠️ <b>Trạng thái:</b> CHƯA THANH TOÁN")
                msg.append(f"   💰 <b>Nợ:</b> <code>{dict_res['total_debt_formatted']}</code>\n")

        return "\n".join(msg)

    def process_message(self, message: dict):
        """Processes an incoming Telegram message."""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            return

        if text.startswith("/start") or text.startswith("/help"):
            welcome_msg = (
                "👋 <b>Xin chào! Tôi là Bot Tra Cứu Hóa Đơn Điện EVN Toàn Quốc.</b>\n\n"
                "💡 <b>Cách dùng:</b> Bạn chỉ cần dán đoạn văn bản chứa 1 hoặc nhiều Mã KH điện vào đây.\n"
                "<i>Ví dụ:</i>\n"
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
                "⚠️ Không tìm thấy Mã Khách Hàng EVN hợp lệ trong tin nhắn của bạn.\n"
                "Mã EVN hợp lệ bắt đầu bằng: <code>PE</code> (HCM), <code>PD</code> (Hà Nội), <code>PA/PB</code> (Miền Bắc), <code>PC/PS</code> (Miền Nam), <code>PP/PQ</code> (Miền Trung)."
            )
            return

        # Send status update
        self.send_message(chat_id, f"⏳ Đang tra cứu {len(codes)} mã EVN, vui lòng đợi giây lát...")

        # Run checks
        results = self.checker.check_batch(codes)
        response_text = self.format_bot_response(results)

        # Send result back
        self.send_message(chat_id, response_text)

    def run_polling(self):
        """Runs long-polling loop to listen for new Telegram updates."""
        print("🤖 Telegram Bot EVN Bill Checker đang chạy...")
        print("👉 Nhấn Ctrl+C để dừng Bot.")
        
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
                print("\n🛑 Bot đã dừng.")
                break
            except Exception as e:
                print(f"⚠️ Lỗi kết nối polling Telegram: {e}")
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
        print(f"🌐 HTTP Health Check Server running on port {port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"HTTP server notice: {e}")

def main():
    parser = argparse.ArgumentParser(description="Chạy Telegram Bot Tra Cứu EVN")
    parser.add_argument("token", nargs="?", help="Telegram Bot Token lấy từ @BotFather")
    args = parser.parse_args()

    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ Thiếu Telegram Bot Token!")
        print("Hướng dẫn chạy:")
        print("  python -m evn_checker.bot <YOUR_TELEGRAM_BOT_TOKEN>")
        print("Hoặc gán biến môi trường TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    # Start dummy HTTP server in a daemon thread if PORT is defined (for Render Web Service)
    if "PORT" in os.environ:
        t = threading.Thread(target=start_dummy_http_server, daemon=True)
        t.start()

    bot = EVNTelegramBot(token)
    bot.run_polling()


if __name__ == "__main__":
    main()
