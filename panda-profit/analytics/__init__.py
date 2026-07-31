"""Analytics module for Panda Profit - Calculations and reporting."""

from .calculations import (
    calculate_profit,
    calculate_roi_by_category,
    calculate_turnover_rate,
    calculate_platform_impact,
)

__all__ = [
    'calculate_profit',
    'calculate_roi_by_category',
    'calculate_turnover_rate',
    'calculate_platform_impact',
]
