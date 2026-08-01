#!/usr/bin/env python3
"""Test script for Settings UI with theme toggle"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def test_settings_tab_ui():
    """Test that Settings tab creates with theme controls"""
    print("Testing Settings Tab UI...")

    app = QApplication(sys.argv)

    try:
        from ui.settings_tab import SettingsTab
        from theme_manager import get_theme_manager

        # Create settings tab
        settings_tab = SettingsTab()
        print("[OK] SettingsTab instantiated")

        # Verify theme controls exist
        assert hasattr(settings_tab, 'light_radio'), "Missing light_radio attribute"
        assert hasattr(settings_tab, 'dark_radio'), "Missing dark_radio attribute"
        assert hasattr(settings_tab, 'theme_group'), "Missing theme_group attribute"
        print("[OK] Theme radio buttons created")

        # Test initial state
        theme_manager = get_theme_manager()
        is_dark = theme_manager.is_dark_mode()
        if is_dark:
            assert settings_tab.dark_radio.isChecked(), "Dark radio should be checked"
            print("[OK] Dark mode radio button initially checked")
        else:
            assert settings_tab.light_radio.isChecked(), "Light radio should be checked"
            print("[OK] Light mode radio button initially checked")

        # Test theme switching via radio buttons
        print("\nTesting theme switching...")

        # Switch to dark
        settings_tab.dark_radio.setChecked(True)
        # Simulate signal
        settings_tab.on_theme_changed(settings_tab.dark_radio)
        assert theme_manager.is_dark_mode(), "Should be in dark mode"
        print("[OK] Switched to dark mode")

        # Switch to light
        settings_tab.light_radio.setChecked(True)
        settings_tab.on_theme_changed(settings_tab.light_radio)
        assert not theme_manager.is_dark_mode(), "Should be in light mode"
        print("[OK] Switched to light mode")

        print("\n[PASS] Settings UI test passed!")
        return True

    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_settings_tab_ui():
        sys.exit(0)
    else:
        sys.exit(1)
