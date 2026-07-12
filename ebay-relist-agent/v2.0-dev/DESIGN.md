# Design System - eBay Relist Agent

## Color Palette

Based on the official Relist Agent branding:

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Background | Black | `#1a1a1a` | Main window background |
| Primary Accent | Vibrant Blue | `#0066FF` | Buttons, highlights, active states |
| Secondary Accent | Bright Red | `#FF3333` | Alerts, warnings, critical actions |
| Tertiary Accent | Bright Yellow | `#FFD700` | Success, completion, positive feedback |
| Text Primary | White | `#FFFFFF` | Main text, readable on dark |
| Text Secondary | Light Gray | `#CCCCCC` | Secondary text, labels |
| Border | Dark Gray | `#333333` | Subtle borders, separators |
| Success | Lime Green | `#00FF00` | Success messages |
| Error | Red | `#FF3333` | Error messages |
| Warning | Yellow | `#FFA500` | Warning messages |

## Typography

- **Headings:** Arial, 14pt, Bold, White
- **Labels:** Arial, 10pt, Regular, Light Gray
- **Body:** Arial, 9pt, Regular, White
- **Monospace:** Courier, 9pt, Regular, White (for IDs, technical info)

## UI Elements

### Buttons
- Background: `#0066FF` (Blue)
- Hover: `#0052CC` (Darker Blue)
- Text: White
- Border: None
- Padding: 8px 16px

### Inputs / Text Fields
- Background: `#2a2a2a`
- Text: White
- Border: `#333333`
- Focus: Border becomes `#0066FF`

### Success State (Green)
- Background: `#1a3a1a` (Dark Green)
- Text: `#00FF00` (Bright Green)

### Error State (Red)
- Background: `#3a1a1a` (Dark Red)
- Text: `#FF3333` (Bright Red)

### Warning State (Yellow)
- Background: `#3a2a1a` (Dark Yellow)
- Text: `#FFD700` (Bright Yellow)

## Implementation

Apply to all GUI components:
- Main window background: `#1a1a1a`
- Dialog backgrounds: `#2a2a2a`
- Button colors: Blue `#0066FF`
- Banner backgrounds: `#2a2a2a` with border `#0066FF`
- Success messages: Green `#00FF00`
- Error messages: Red `#FF3333`
- Warning messages: Yellow `#FFA500`

---

**Status:** Design standard for all versions
**Last Updated:** 2026-06-02
