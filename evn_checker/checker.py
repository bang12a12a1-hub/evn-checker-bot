import re
from typing import List, Dict, Optional
from .models import BillCheckResult, EVNRegion
from .providers import (
    BaseEVNProvider,
    HCMCProvider,
    HanoiProvider,
    NPCProvider,
    SPCProvider,
    CPCProvider
)

def detect_region(customer_code: str) -> EVNRegion:
    """Detects EVN region enum based on 2-letter customer code prefix."""
    code = customer_code.strip().upper()
    if code.startswith("PD"):
        return EVNRegion.HANOI
    elif code.startswith("PE"):
        return EVNRegion.HCMC
    elif code.startswith(("PA", "PB", "PH", "PN")):
        return EVNRegion.NPC
    elif code.startswith(("PC", "PS")):
        return EVNRegion.SPC
    elif code.startswith(("PP", "PQ", "PK")):
        return EVNRegion.CPC
    return EVNRegion.UNKNOWN

class EVNBillChecker:
    """Main EVN Bill Checker Orchestrator for nationwide bill lookups."""

    def __init__(self, use_playwright_fallback: bool = True, timeout: int = 15):
        self.use_playwright_fallback = use_playwright_fallback
        self.timeout = timeout
        
        # Instantiate regional providers
        self.providers: Dict[EVNRegion, BaseEVNProvider] = {
            EVNRegion.HCMC: HCMCProvider(use_playwright_fallback, timeout),
            EVNRegion.HANOI: HanoiProvider(use_playwright_fallback, timeout),
            EVNRegion.NPC: NPCProvider(use_playwright_fallback, timeout),
            EVNRegion.SPC: SPCProvider(use_playwright_fallback, timeout),
            EVNRegion.CPC: CPCProvider(use_playwright_fallback, timeout),
        }

    def check(self, customer_code: str) -> BillCheckResult:
        """
        Check bill payment status for any nationwide EVN customer code.
        
        :param customer_code: Mã khách hàng EVN (ví dụ: PE01000123456, PD02000654321, PA1200...)
        :return: BillCheckResult dataclass object
        """
        code = customer_code.strip().upper()
        if not code or len(code) < 5:
            return BillCheckResult(
                customer_code=customer_code,
                region=EVNRegion.UNKNOWN,
                success=False,
                is_paid=True,
                error="Mã khách hàng EVN không hợp lệ (Quá ngắn)"
            )

        region = detect_region(code)
        if region == EVNRegion.UNKNOWN or region not in self.providers:
            return BillCheckResult(
                customer_code=code,
                region=EVNRegion.UNKNOWN,
                success=False,
                is_paid=True,
                error=f"Không xác định được khu vực EVN cho tiền tố: {code[:2]}"
            )

        provider = self.providers[region]
        return provider.check(code)

    def check_batch(self, customer_codes: List[str]) -> List[BillCheckResult]:
        """Check multiple EVN customer codes sequentially."""
        results = []
        for code in customer_codes:
            if code.strip():
                results.append(self.check(code.strip()))
        return results
