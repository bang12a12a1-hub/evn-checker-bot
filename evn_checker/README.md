# 🔌 EVN Bill Checker (Toàn Quốc - KHÔNG API Key)

Thư viện Python tra cứu trạng thái hóa đơn điện EVN **toàn quốc (63 tỉnh thành)** hoàn toàn **miễn phí**, không cần đăng ký API Key qua bất kỳ bên thứ 3 nào.

---

## 🌟 Tính năng nổi bật

- **Tự động nhận biết khu vực (Prefix Routing):** Tự phân tích 2 ký tự đầu mã KH để gửi request đến đúng cổng CSKH EVN (Hà Nội, TP.HCM, Miền Bắc, Miền Nam, Miền Trung).
- **Cơ chế kép (Hybrid Mode):** Ưu tiên gửi HTTP Request siêu nhanh (~0.5s), tự động kích hoạt Playwright Headless Browser nếu gặp trang bảo mật/JS.
- **Không phụ thuộc API bên thứ 3:** Chạy độc lập 100% trên máy nội bộ.
- **Xuất kết quả chuẩn hóa:** Trả về kết quả JSON / Data Class gồm `is_paid` (True/False), số tiền nợ, tên khách hàng, chi tiết kỳ nợ.

---

## 📂 Cấu trúc thư mục `evn_checker`

```
evn_checker/
├── __init__.py          # Export chính (EVNBillChecker, detect_region,...)
├── checker.py           # Orchestration chính tự động điều hướng khu vực
├── models.py            # Data classes (BillCheckResult, BillItem, EVNRegion)
├── cli.py               # Chạy giao diện dòng lệnh (CLI)
├── README.md            # Tài liệu hướng dẫn
└── providers/           # Các adapter khu vực EVN
    ├── base.py          # Class cơ sở cho provider
    ├── hcmc.py          # EVNHCMC (TP. Hồ Chí Minh - Mã PE...)
    ├── hanoi.py         # EVNHANOI (Hà Nội - Mã PD...)
    ├── npc.py           # EVNNPC (Miền Bắc - Mã PA, PB, PH, PN...)
    ├── spc.py           # EVNSPC (Miền Nam - Mã PC, PS...)
    └── cpc.py           # EVNCPC (Miền Trung & Tây Nguyên - Mã PP, PQ, PK...)
```

---

## 🚀 Hướng dẫn sử dụng

### 1. Sử dụng trong code Python của bạn

```python
from evn_checker import EVNBillChecker

# 1. Khởi tạo checker
checker = EVNBillChecker(use_playwright_fallback=True)

# 2. Kiểm tra 1 mã khách hàng bất kỳ
result = checker.check("PE01000123456")

# 3. Kiểm tra kết quả
if result.success:
    if result.is_paid:
        print(f"✅ Mã {result.customer_code}: ĐÃ THANH TOÁN (Hết nợ)")
    else:
        print(f"⚠️ Mã {result.customer_code}: CHƯA THANH TOÁN")
        print(f"💰 Số tiền nợ: {result.total_debt:,.0f} VNĐ")
        for bill in result.bills:
            print(f"   - Kỳ: {bill.period} | Tiền: {bill.amount:,.0f} VNĐ")
else:
    print(f"❌ Tra cứu thất bại: {result.error}")

# 4. Chuyển sang định dạng Dictionary / JSON
print(result.to_dict())
```

---

### 2. Kiểm tra hàng loạt (Batch Check)

```python
from evn_checker import EVNBillChecker

checker = EVNBillChecker()
danh_sach_ma = ["PE01000123456", "PD02000654321", "PA12000987654"]

results = checker.check_batch(danh_sach_ma)

for r in results:
    status = "ĐÃ THANH TOÁN" if r.is_paid else f"NỢ {r.total_debt:,.0f} VNĐ"
    print(f"Mã KH: {r.customer_code} [{r.region.value}] -> {status}")
```

---

### 3. Chạy từ Dòng lệnh CLI

Tra cứu nhanh các mã trực tiếp trên Terminal / CMD:

```bash
# Tra cứu 1 hoặc nhiều mã trực tiếp:
python -m evn_checker.cli PE01000123456 PD02000654321

# Tra cứu mã từ file text (mỗi dòng 1 mã KH):
python -m evn_checker.cli -f list_ma_kh.txt

# Xuất dạng JSON:
python -m evn_checker.cli PE01000123456 --json
```

---

## 🗺️ Bảng Mã Tiền Tố (Prefix Routing)

| Tiền tố | Khu vực EVN | Phạm vi |
| :--- | :--- | :--- |
| **`PD`** | EVNHANOI | TP. Hà Nội |
| **`PE`** | EVNHCMC | TP. Hồ Chí Minh |
| **`PA`, `PB`, `PH`, `PN`** | EVNNPC | 27 Tỉnh miền Bắc |
| **`PC`, `PS`** | EVNSPC | 21 Tỉnh miền Nam |
| **`PP`, `PQ`, `PK`** | EVNCPC | Miền Trung & Tây Nguyên |
