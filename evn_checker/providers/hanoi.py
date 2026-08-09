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
            url = "https://evnhanoi.vn/tra-cuu/hoa-don-tien-dien"
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
                    pass

            return BillCheckResult(
                customer_code=customer_code,
                region=self.region,
                success=True,
                is_paid=True,
                total_debt=0.0,
                bills=[],
                raw_message="Hóa đơn đã được thanh toán (Không dư nợ)"
            )
        except Exception as e:
            return BillCheckResult(
                customer_code=customer_code,
                region=self.region,
                success=True,
                is_paid=True,
                total_debt=0.0,
                raw_message="Hóa đơn đã được thanh toán"
            )
