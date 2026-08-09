import sys
import os
import json
import argparse
from typing import List

# Fix UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from .checker import EVNBillChecker, detect_region

import re

def extract_customer_codes(text: str) -> List[str]:
    """Extracts all EVN customer codes matching patterns (PD, PE, PA, PC, PP...) from raw text."""
    pattern = r'\b(P[A-Z0-9]{9,12})\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for m in matches:
        upper_m = m.upper()
        if upper_m not in seen:
            seen.add(upper_m)
            result.append(upper_m)
    return result

def print_result_pretty(result):
    dict_res = result.to_dict()
    print("=" * 60)
    print(f"📌 MÃ KHÁCH HÀNG : {dict_res['customer_code']}")
    print(f"🏢 KHU VỰC EVN   : {dict_res['region']}")
    print(f"👤 KHÁCH HÀNG    : {dict_res['customer_name']}")
    print(f"📍 ĐỊA CHỈ       : {dict_res['address']}")
    
    if not dict_res['success']:
        print(f"❌ THẤT BẠI      : {dict_res['error']}")
    elif dict_res['is_paid']:
        print(f"✅ TRẠNG THÁI    : ĐÃ THANH TOÁN (Hóa đơn không nợ tiền)")
    else:
        print(f"⚠️  TRẠNG THÁI    : CHƯA THANH TOÁN")
        print(f"💰 TỔNG TIỀN NỢ   : {dict_res['total_debt_formatted']}")
        if dict_res['bills']:
            print("📋 CHI TIẾT HÓA ĐƠN NỢ:")
            for b in dict_res['bills']:
                print(f"   - Kỳ: {b['period']} | Số tiền: {b['amount_formatted']} | Hạn TT: {b['due_date'] or 'N/A'}")
    
    print(f"💬 THÔNG BÁO     : {dict_res['raw_message']}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Tool Tra Cứu Hóa Đơn Điện EVN Toàn Quốc (Không Cần API Key)")
    parser.add_argument("codes", nargs="*", help="Danh sách Mã Khách Hàng EVN hoặc văn bản dán trực tiếp")
    parser.add_argument("-f", "--file", help="Đường dẫn file chứa văn bản/danh sách Mã KH")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả dưới dạng JSON")
    parser.add_argument("--no-playwright", action="store_true", help="Tắt Playwright fallback (chỉ dùng HTTP request)")

    args = parser.parse_args()

    raw_input_text = " ".join(args.codes)

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            raw_input_text += " " + f.read()

    codes_to_check = extract_customer_codes(raw_input_text)

    if not codes_to_check:
        print("💡 Hướng dẫn sử dụng CLI:")
        print("  Dán trực tiếp văn bản có mã KH vào dòng lệnh:")
        print('  python -m evn_checker.cli "PC01BB0290022  1,530,403  PC01BB0308544  1,536,207"')
        print("  Hoặc đọc từ file text:")
        print("  python -m evn_checker.cli -f input.txt")
        sys.exit(0)


    checker = EVNBillChecker(use_playwright_fallback=not args.no_playwright)
    results = checker.check_batch(codes_to_check)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
    else:
        for r in results:
            print_result_pretty(r)

if __name__ == "__main__":
    main()
