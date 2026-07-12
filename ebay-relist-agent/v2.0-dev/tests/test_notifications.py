import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_format_report_includes_relisted_items():
    from notifications import format_report
    report = format_report(
        relisted=[{"old_id": "111", "new_id": "999", "title": "Cool Shirt"}],
        ended_zero_qty=[],
        failures=[],
    )
    assert "111" in report and "999" in report and "Cool Shirt" in report


def test_format_report_includes_zero_qty_items():
    from notifications import format_report
    report = format_report(
        relisted=[],
        ended_zero_qty=[{"item_id": "555", "title": "Old Hat"}],
        failures=[],
    )
    assert "555" in report and "Old Hat" in report


def test_format_report_includes_failures():
    from notifications import format_report
    report = format_report(
        relisted=[],
        ended_zero_qty=[],
        failures=[{"item_id": "777", "title": "Bad Item", "reason": "API error"}],
    )
    assert "777" in report and "API error" in report


def test_format_subject_includes_date_and_brand():
    from notifications import format_subject
    subject = format_subject("2026-05-24")
    assert "2026-05-24" in subject and "eBay" in subject
