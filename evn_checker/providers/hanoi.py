import requests
from ..models import BillCheckResult, BillItem, EVNRegion
from .base import BaseEVNProvider

class HanoiProvider(BaseEVNProvider):
    """Provider for EVNHANOI (TP. Hà Nội) - Code prefix: PD"""

    @property
    def region(self) -> EVNRegion:
        return EVNRegion.HANOI

    def check(self, customer_code: str) -> BillCheckResult:
        customer_code = customer_code.strip().upper()
        
        try:
            url = "https://cskh.evnhanoi.com.vn/TraCuu/GetTienDienByMaKh"
            params = {"maKh": customer_code}
            
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        is_paid = data.get("isPaid", True) or len(data.get("bills", [])) == 0
                        bills = []
                        total_debt = 0.0
                        for item in data.get("bills", []):
                            amt = float(item.get("amount", 0))
                            total_debt += amt
                            bills.append(BillItem(
                                period=item.get("kyThanhToan", "N/A"),
                                amount=amt,
                                bill_id=item.get("maHoaDon"),
                                due_date=item.get("hanThanhToan")
                            ))
                        return BillCheckResult(
                            customer_code=customer_code,
                            region=self.region,
                            success=True,
                            is_paid=(total_debt == 0),
                            customer_name=data.get("tenKhachHang"),
                            address=data.get("diaChi"),
                            total_debt=total_debt,
                            bills=bills,
                            raw_message="Tra cứu thành công từ EVNHANOI"
                        )
                except Exception:
                    html = resp.text
                    if "không có dư nợ" in html.lower() or "đã thanh toán" in html.lower() or "không tìm thấy" in html.lower():
                        return BillCheckResult(
                            customer_code=customer_code,
                            region=self.region,
                            success=True,
                            is_paid=True,
                            total_debt=0.0,
                            bills=[],
                            raw_message="Hóa đơn đã được thanh toán (Không dư nợ)"
                        )
        except Exception:
            pass

        if self.use_playwright_fallback:
            return self._check_via_playwright(customer_code)

        return BillCheckResult(
            customer_code=customer_code,
            region=self.region,
            success=False,
            is_paid=True,
            error="Không thể truy cập dịch vụ EVNHANOI"
        )

    def _check_via_playwright(self, customer_code: str) -> BillCheckResult:
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("https://evnhanoi.vn/tra-cuu/hoa-don-tien-dien", timeout=15000)

                
                if page.locator("#txtMaKh").is_visible(timeout=3000):
                    page.fill("#txtMaKh", customer_code)
                    page.click("#btnTraCuu")
                    page.wait_for_timeout(2000)
                
                content = page.content()
                browser.close()
                
                if "không" in content.lower() and ("nợ" in content.lower() or "hóa đơn" in content.lower()):
                    return BillCheckResult(
                        customer_code=customer_code,
                        region=self.region,
                        success=True,
                        is_paid=True,
                        total_debt=0.0,
                        raw_message="Không có dư nợ (Đã thanh toán hết)"
                    )
                else:
                    return BillCheckResult(
                        customer_code=customer_code,
                        region=self.region,
                        success=True,
                        is_paid=False,
                        raw_message="Có hóa đơn nợ chưa thanh toán"
                    )
        except Exception as e:
            return BillCheckResult(
                customer_code=customer_code,
                region=self.region,
                success=False,
                is_paid=True,
                error=f"Lỗi Playwright EVNHANOI: {str(e)}"
            )
