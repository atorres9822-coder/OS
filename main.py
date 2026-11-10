#!/usr/bin/env python3
"""
Mini OS — Interactive Operating System Simulator
Main entry point for the application.
"""

import tkinter as tk
from gui.desktop import DesktopApp


def main():
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()