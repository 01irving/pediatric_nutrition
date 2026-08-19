"""
Nutrición Pediátrica — Dashboard Principal.
Ejecuta la aplicación de escritorio con Tkinter.
"""
import sys
import os
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import MainWindow


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
