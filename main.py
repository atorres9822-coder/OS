#!/usr/bin/env python3
"""
Mini OS — Interactive Operating System Simulator
Main entry point for the application.
"""

import sys


def check_dependencies():
    """Check that required dependencies are available."""
    missing = []
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")

    if missing:
        print("Missing required dependencies:", ", ".join(missing))
        print()
        if "tkinter" in missing:
            print("tkinter is required but not installed.")
            print("On Fedora:  sudo dnf install python3-tkinter")
            print("On Ubuntu:  sudo apt install python3-tk")
            print()
            print("Alternatively, use the conda Python which includes tkinter:")
            print("  /home/saint/miniconda3/bin/python main.py")
        if "matplotlib" in missing:
            print("Install matplotlib:  pip install matplotlib")
        sys.exit(1)


def main():
    check_dependencies()
    import tkinter as tk
    from gui.desktop import DesktopApp

    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
