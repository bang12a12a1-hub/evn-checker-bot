from abc import ABC, abstractmethod
from ..models import BillCheckResult, EVNRegion

class BaseEVNProvider(ABC):
    """Abstract base class for all regional EVN bill checking providers."""
    
    def __init__(self, use_playwright_fallback: bool = True, timeout: int = 15):
        self.use_playwright_fallback = use_playwright_fallback
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    @property
    @abstractmethod
    def region(self) -> EVNRegion:
        pass

    @abstractmethod
    def check(self, customer_code: str) -> BillCheckResult:
        """Check bill status for a given customer code."""
        pass
