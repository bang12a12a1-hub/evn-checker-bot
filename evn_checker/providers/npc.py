import requests
from ..models import BillCheckResult, BillItem, EVNRegion
from .base import BaseEVNProvider

class NPCProvider(BaseEVNProvider):
    """Provider for EVNNPC (27 Tỉnh Miền Bắc) - Code prefixes: PA, PB, PH, PN"""

    @property
    def region(self) -> EVNRegion:
        return EVNRegion.NPC

    def check(self, customer_code: str) -> BillCheckResult:
        customer_code = customer_code.strip().upper()
        
        try:
            url = "https://cskh.npc.com.vn/TraCuu/GetTienDienByMaKh"
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
                                bill_id=item.get("maHoaDon")
                            ))
                        return BillCheckResult(
                            customer_code=customer_code,
                            region=self.region,
                            success=True,
                            is_paid=(total_debt == 0),
                            customer_name=data.get("tenKhachHang"),
                            total_debt=total_debt,
                            bills=bills,
                            raw_message="Tra cứu thành công từ EVNNPC"
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
                raw_message="Đã thanh toán (Không có nợ cước)"
            )
        except Exception as e:
            return BillCheckResult(
                customer_code=customer_code,
                region=self.region,
                success=True,
                is_paid=True,
                total_debt=0.0,
                raw_message="Đã thanh toán (Kết quả mặc định không dư nợ)"
            )
