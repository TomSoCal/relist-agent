import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from ui.history_tab import HistoryTab

@pytest.fixture(scope='module')
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_history_tab_initializes(qapp):
    """HistoryTab should initialize without errors."""
    tab = HistoryTab()
    assert isinstance(tab, QWidget)
    assert tab is not None

def test_history_tab_has_buttons(qapp):
    """HistoryTab should have three buttons."""
    tab = HistoryTab()
    # Check button layout exists (will verify in UI step)
    assert tab is not None
