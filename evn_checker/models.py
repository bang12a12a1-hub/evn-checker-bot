from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class EVNRegion(Enum):
    HCMC = "EVNHCMC (TP. Hồ Chí Minh)"
    HANOI = "EVNHANOI (TP. Hà Nội)"
    NPC = "EVNNPC (27 Tỉnh Miền Bắc)"
    SPC = "EVNSPC (21 Tỉnh Miền Nam)"
    CPC = "EVNCPC (Miền Trung & Tây Nguyên)"
    UNKNOWN = "Không xác định"

@dataclass
class BillItem:
    period: str  # Ví dụ: "07/2026"
    amount: float  # Số tiền nợ (VNĐ)
    bill_id: Optional[str] = None  # Mã hóa đơn
    due_date: Optional[str] = None  # Hạn thanh toán
    description: Optional[str] = None

@dataclass
class BillCheckResult:
    customer_code: str
    region: EVNRegion
    success: bool
    is_paid: bool  # True nếu đã thanh toán hết (nợ = 0), False nếu còn nợ
    customer_name: Optional[str] = None
    address: Optional[str] = None
    total_debt: float = 0.0
    bills: List[BillItem] = field(default_factory=list)
    raw_message: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "region": self.region.value,
            "success": self.success,
            "is_paid": self.is_paid,
            "customer_name": self.customer_name or "N/A",
            "address": self.address or "N/A",
            "total_debt": self.total_debt,
            "total_debt_formatted": f"{self.total_debt:,.0f} VNĐ",
            "bills_count": len(self.bills),
            "bills": [
                {
                    "period": b.period,
                    "amount": b.amount,
                    "amount_formatted": f"{b.amount:,.0f} VNĐ",
                    "bill_id": b.bill_id,
                    "due_date": b.due_date,
                    "description": b.description
                }
                for b in self.bills
            ],
            "raw_message": self.raw_message,
            "error": self.error
        }
