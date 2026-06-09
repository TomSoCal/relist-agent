#!/usr/bin/env python3
"""
Relist Agent License Key Generator - GUI Version
Simple click-and-generate interface for beta testers
"""

import hashlib
import secrets
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

LICENSE_SECRET = 'relist-agent-secret'


def generate_license_key(order_id: str = None) -> str:
    """Generate a valid license key"""
    if order_id is None:
        order_id = f"{secrets.randbelow(100):02d}"
    else:
        order_id = order_id.strip()
        if not order_id.isdigit() or len(order_id) > 2:
            order_id = f"{int(order_id):02d}" if order_id.isdigit() else f"{secrets.randbelow(100):02d}"

    random_part = secrets.token_hex(4).upper()
    base_key = f"RA-{order_id}-{random_part}"
    checksum_input = base_key + LICENSE_SECRET
    checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:8].upper()
    return f"{base_key}-{checksum}"


class KeygenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Relist Agent - License Key Generator")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        # Set icon if it exists
        icon_path = Path(__file__).parent / "ERA_Icon.png"
        if icon_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, photo)
            except:
                pass

        # Title
        title = ttk.Label(root, text="License Key Generator", font=("Arial", 14, "bold"))
        title.pack(pady=10)

        # Frame for Order ID input
        input_frame = ttk.Frame(root)
        input_frame.pack(pady=10, padx=20, fill="x")

        ttk.Label(input_frame, text="Order ID (optional):").pack(side="left")
        self.order_id_var = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=self.order_id_var, width=10)
        entry.pack(side="left", padx=10)

        ttk.Button(input_frame, text="Generate", command=self.generate_with_id).pack(side="left", padx=5)
        ttk.Button(input_frame, text="Random", command=self.generate_random).pack(side="left", padx=5)

        # Key display
        ttk.Label(root, text="Generated Key:").pack(pady=(20, 5))
        self.key_var = tk.StringVar()
        key_display = ttk.Entry(root, textvariable=self.key_var, width=50, state="readonly")
        key_display.pack(padx=20, fill="x")

        # Buttons
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="Copy to Clipboard", command=self.copy_key).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Generate 10 Keys", command=self.generate_batch).pack(side="left", padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(root, textvariable=self.status_var, foreground="blue")
        status.pack(pady=10)

    def generate_random(self):
        """Generate key with random Order ID"""
        key = generate_license_key()
        self.key_var.set(key)
        self.status_var.set("✓ Key generated")

    def generate_with_id(self):
        """Generate key with specific Order ID"""
        order_id = self.order_id_var.get().strip()
        if not order_id:
            messagebox.showwarning("Input Error", "Please enter an Order ID")
            return

        try:
            key = generate_license_key(order_id)
            self.key_var.set(key)
            self.status_var.set(f"✓ Key generated for Order {order_id}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Order ID must be a number (1-99)")

    def copy_key(self):
        """Copy key to clipboard"""
        key = self.key_var.get()
        if not key:
            messagebox.showwarning("No Key", "Generate a key first")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        self.status_var.set("✓ Copied to clipboard")

    def generate_batch(self):
        """Generate 10 keys and save to file"""
        keys = [generate_license_key(f"{i+1:02d}") for i in range(10)]

        # Save to file
        output_file = Path(__file__).parent / "beta_keys.txt"
        with open(output_file, 'w') as f:
            f.write("RELIST AGENT - BETA TESTER LICENSE KEYS\n")
            f.write("=" * 50 + "\n\n")
            for i, key in enumerate(keys, 1):
                f.write(f"{i:2d}. {key}\n")
            f.write("\n" + "=" * 50 + "\n")
            f.write("Each key can be used once to activate the Relist Agent.\n")

        messagebox.showinfo("Success", f"Generated 10 keys\nSaved to: {output_file}")
        self.status_var.set(f"✓ 10 keys saved to beta_keys.txt")


if __name__ == "__main__":
    root = tk.Tk()
    app = KeygenApp(root)
    root.mainloop()
