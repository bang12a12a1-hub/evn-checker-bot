from .models import BillCheckResult, BillItem, EVNRegion
from .checker import EVNBillChecker, detect_region

try:
    from .gui import launch_gui
except (ImportError, ModuleNotFoundError):
    launch_gui = None

__version__ = "1.0.0"
__all__ = [
    "EVNBillChecker",
    "detect_region",
    "launch_gui",
    "BillCheckResult",
    "BillItem",
    "EVNRegion"
]




