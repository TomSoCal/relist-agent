"""Theme manager for light/dark mode switching"""

import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

class ThemeManager:
    LIGHT = "light"
    DARK = "dark"

    def __init__(self):
        self.current_theme = self.LIGHT
        self.themes_dir = os.path.join(os.path.dirname(__file__), "themes")
        self.settings = QSettings("TrashedPanda", "PandaProfit")
        self.load_saved_theme()

    def load_saved_theme(self):
        """Load theme preference from settings"""
        saved_theme = self.settings.value("theme", self.LIGHT)
        self.current_theme = saved_theme if saved_theme in [self.LIGHT, self.DARK] else self.LIGHT

    def get_theme_stylesheet(self, theme=None):
        """Get stylesheet for a theme"""
        if theme is None:
            theme = self.current_theme

        theme_file = os.path.join(self.themes_dir, f"{theme}_theme.qss")

        if not os.path.exists(theme_file):
            print(f"Warning: Theme file not found: {theme_file}")
            return ""

        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading theme: {e}")
            return ""

    def apply_theme(self, theme):
        """Apply theme to QApplication"""
        if theme not in [self.LIGHT, self.DARK]:
            print(f"Invalid theme: {theme}")
            return

        self.current_theme = theme
        stylesheet = self.get_theme_stylesheet(theme)

        app_instance = QApplication.instance()
        if app_instance:
            app_instance.setStyleSheet(stylesheet)

        # Save preference
        self.settings.setValue("theme", theme)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = self.DARK if self.current_theme == self.LIGHT else self.LIGHT
        self.apply_theme(new_theme)
        return new_theme

    def get_current_theme(self):
        """Get current theme"""
        return self.current_theme

    def is_dark_mode(self):
        """Check if dark mode is enabled"""
        return self.current_theme == self.DARK


# Global theme manager instance
_theme_manager = None

def get_theme_manager():
    """Get or create global theme manager"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
