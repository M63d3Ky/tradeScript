import tkinter as tk
from gui import TradingViewGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingViewGUI(root)
    root.mainloop()