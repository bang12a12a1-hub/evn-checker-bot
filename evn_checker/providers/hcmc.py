import requests
from ..models import BillCheckResult, BillItem, EVNRegion
from .base import BaseEVNProvider

class HCMCProvider(BaseEVNProvider):
    """Provider for EVNHCMC (TP. Hồ Chí Minh) - Code prefix: PE"""

    @property
    def region(self) -> EVNRegion:
        return EVNRegion.HCMC

    def check(self, customer_code: str) -> BillCheckResult:
        customer_code = customer_code.strip().upper()
        
        # 1. Try direct HTTP request first
        try:
            url = "https://cskh.evnhcm.vn/TraCuu/tracuutiendien_process"
            payload = {"maKH": customer_code}
            
            resp = requests.post(url, data=payload, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # Handle JSON response if returned
                    if isinstance(data, dict):
                        is_paid = data.get("is_paid", True) or (len(data.get("bills", [])) == 0)
                        bills = []
                        total_debt = 0.0
                        for item in data.get("bills", []):
                            amt = float(item.get("amount", 0))
                            total_debt += amt
                            bills.append(BillItem(
                                period=item.get("period", "N/A"),
                                amount=amt,
                                bill_id=item.get("bill_id"),
                                due_date=item.get("due_date")
                            ))
                        return BillCheckResult(
                            customer_code=customer_code,
                            region=self.region,
                            success=True,
                            is_paid=(total_debt == 0),
                            customer_name=data.get("customer_name"),
                            address=data.get("address"),
                            total_debt=total_debt,
                            bills=bills,
                            raw_message="Tra cứu thành công từ EVNHCMC"
                        )
                except Exception:
                    # If HTML returned, check text content
                    html = resp.text
                    if "Không tìm thấy" in html or "không có hóa đơn" in html.lower() or "đã thanh toán" in html.lower():
                        return BillCheckResult(
                            customer_code=customer_code,
                            region=self.region,
                            success=True,
                            is_paid=True,
                            total_debt=0.0,
                            bills=[],
                            raw_message="Không có hóa đơn nợ (Đã thanh toán hết)"
                        )
        except Exception as e:
            pass

        # 2. Playwright Fallback if direct request didn't parse or encountered JS protection
        if self.use_playwright_fallback:
            return self._check_via_playwright(customer_code)

        return BillCheckResult(
            customer_code=customer_code,
            region=self.region,
            success=False,
            is_paid=True,
            error="Không thể kết nối dịch vụ EVNHCMC"
        )

    def _check_via_playwright(self, customer_code: str) -> BillCheckResult:
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("https://cskh.evnhcm.vn/TraCuu/tracuutiendien", timeout=15000)
                
                # Fill customer code input
                if page.locator("#txtMaKH").is_visible(timeout=3000):
                    page.fill("#txtMaKH", customer_code)
                    page.click("#btnTraCuu")
                    page.wait_for_timeout(2000)
                
                content = page.content()
                browser.close()
                
                if "Không tìm thấy" in content or "không có hóa đơn" in content.lower() or "đã thanh toán" in content.lower():
                    return BillCheckResult(
                        customer_code=customer_code,
                        region=self.region,
                        success=True,
                        is_paid=True,
                        total_debt=0.0,
                        raw_message="Đã thanh toán hết (Không có hóa đơn nợ)"
                    )
                else:
                    return BillCheckResult(
                        customer_code=customer_code,
                        region=self.region,
                        success=True,
                        is_paid=False,
                        raw_message="Phát hiện hóa đơn nợ chưa thanh toán"
                    )
        except Exception as e:
            return BillCheckResult(
                customer_code=customer_code,
                region=self.region,
                success=False,
                is_paid=True,
                error=f"Lỗi Playwright EVNHCMC: {str(e)}"
            )
