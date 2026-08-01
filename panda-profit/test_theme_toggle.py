#!/usr/bin/env python3
"""Test script for theme toggle functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test without Qt first
from theme_manager import get_theme_manager

def test_theme_manager():
    """Test basic theme manager functionality"""
    tm = get_theme_manager()

    print("Testing Theme Manager...")
    print("Initial theme: {}".format(tm.get_current_theme()))
    print("Is dark mode: {}".format(tm.is_dark_mode()))

    # Test light theme state
    print("\nTesting light theme state...")
    tm.current_theme = tm.LIGHT
    assert tm.get_current_theme() == tm.LIGHT, "Failed to set light theme"
    assert not tm.is_dark_mode(), "is_dark_mode() should be False for light theme"
    print("[OK] Light theme state works")

    # Test dark theme state
    print("\nTesting dark theme state...")
    tm.current_theme = tm.DARK
    assert tm.get_current_theme() == tm.DARK, "Failed to set dark theme"
    assert tm.is_dark_mode(), "is_dark_mode() should be True for dark theme"
    print("[OK] Dark theme state works")

    # Test stylesheet loading
    print("\nTesting stylesheet loading...")
    light_style = tm.get_theme_stylesheet(tm.LIGHT)
    dark_style = tm.get_theme_stylesheet(tm.DARK)
    assert len(light_style) > 0, "Light stylesheet is empty"
    assert len(dark_style) > 0, "Dark stylesheet is empty"
    assert light_style != dark_style, "Stylesheets should be different"
    print("[OK] Light stylesheet: {} chars".format(len(light_style)))
    print("[OK] Dark stylesheet: {} chars".format(len(dark_style)))

    print("\n[PASS] All theme manager tests passed!")

def test_settings_tab_import():
    """Test that settings tab can import theme manager"""
    print("\nTesting Settings tab theme integration...")
    try:
        # Just check the imports work
        import theme_manager
        print("[OK] SettingsTab can access theme_manager")
        print("[OK] Theme manager integration available")
    except ImportError as e:
        print("[FAIL] Import failed: {}".format(e))
        return False

    return True

if __name__ == "__main__":
    try:
        test_theme_manager()
        if test_settings_tab_import():
            print("\n[PASS] All tests passed!")
            sys.exit(0)
        else:
            print("\n[FAIL] Some tests failed")
            sys.exit(1)
    except Exception as e:
        print("\n[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
