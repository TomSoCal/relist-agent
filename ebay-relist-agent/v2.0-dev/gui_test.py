#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("eBay Relist - Test")
root.geometry("400x300")

ttk.Label(root, text="GUI is working!").pack(pady=20)
ttk.Button(root, text="Close", command=root.quit).pack(pady=10)

root.mainloop()
