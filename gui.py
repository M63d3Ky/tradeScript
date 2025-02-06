import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import pandas as pd
import threading
import tkinter.messagebox as messagebox
from data_loader import DataLoader
from kline_plotter import plot_kline

class TradingViewGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("K 线数据加载器")

        self.treeview = None

        # 时间范围选择
        self.start_year = tk.StringVar(value="2024")
        self.start_month = tk.StringVar(value="10")
        self.start_day = tk.StringVar(value="01")
        self.start_hour = tk.StringVar(value="00")
        self.start_minute = tk.StringVar(value="00")

        self.end_year = tk.StringVar(value="2024")
        self.end_month = tk.StringVar(value="10")
        self.end_day = tk.StringVar(value="02")
        self.end_hour = tk.StringVar(value="00")
        self.end_minute = tk.StringVar(value="00")

        self.interval_var = tk.StringVar(value="1m")

        self.create_widgets()

    def create_widgets(self):
        # 时间范围选择框
        time_frame = tk.Frame(self.root)
        time_frame.pack(pady=10)

        # 起始时间选择
        tk.Label(time_frame, text="Start Time:").grid(row=0, column=0, padx=5)
        ttk.Spinbox(time_frame, from_=2020, to=2099, textvariable=self.start_year, width=6).grid(row=0, column=1, padx=5)
        tk.Label(time_frame, text="-").grid(row=0, column=2, padx=2)
        ttk.Spinbox(time_frame, from_=1, to=12, textvariable=self.start_month, width=4).grid(row=0, column=3, padx=5)
        tk.Label(time_frame, text="-").grid(row=0, column=4, padx=2)
        ttk.Spinbox(time_frame, from_=1, to=31, textvariable=self.start_day, width=4).grid(row=0, column=5, padx=5)
        tk.Label(time_frame, text=" ").grid(row=0, column=6, padx=2)
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.start_hour, width=4).grid(row=0, column=7, padx=5)
        tk.Label(time_frame, text=":").grid(row=0, column=8, padx=2)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.start_minute, width=4).grid(row=0, column=9, padx=5)

        # 结束时间选择
        tk.Label(time_frame, text="End Time:").grid(row=1, column=0, padx=5)
        ttk.Spinbox(time_frame, from_=2020, to=2099, textvariable=self.end_year, width=6).grid(row=1, column=1, padx=5)
        tk.Label(time_frame, text="-").grid(row=1, column=2, padx=2)
        ttk.Spinbox(time_frame, from_=1, to=12, textvariable=self.end_month, width=4).grid(row=1, column=3, padx=5)
        tk.Label(time_frame, text="-").grid(row=1, column=4, padx=2)
        ttk.Spinbox(time_frame, from_=1, to=31, textvariable=self.end_day, width=4).grid(row=1, column=5, padx=5)
        tk.Label(time_frame, text=" ").grid(row=1, column=6, padx=2)
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.end_hour, width=4).grid(row=1, column=7, padx=5)
        tk.Label(time_frame, text=":").grid(row=1, column=8, padx=2)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.end_minute, width=4).grid(row=1, column=9, padx=5)

        # 周期选择
        tk.Label(time_frame, text="Interval:").grid(row=2, column=0, padx=5)
        interval_menu = ttk.Combobox(time_frame, textvariable=self.interval_var, values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"], width=10)
        interval_menu.grid(row=2, column=1, padx=5)

        # 加载按钮
        tk.Button(time_frame, text="Load from Binance", command=self.load_data).grid(row=2, column=2, padx=5)

        # 数据展示
        columns = ("Timestamp", "Open", "High", "Low", "Close", "Volume")
        self.treeview = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 添加搜索功能
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=10)

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left")

        search_column_var = tk.StringVar()
        search_column_var.set("所有列")  # 默认值
        search_column_menu = ttk.Combobox(search_frame, textvariable=search_column_var, values=["所有列", "Timestamp", "Open", "High", "Low", "Close", "Volume"])
        search_column_menu.pack(side="left", padx=5)

        # 添加绘制 K 线图的按钮
        tk.Button(time_frame, text="Plot K-line", command=self.plot_kline).grid(row=3, column=0, padx=5)

        def search_data():
            search_text = search_var.get().strip()
            search_column = search_column_var.get()  # 获取用户选择的列

            if not search_text:
                return

            for item in self.treeview.get_children():
                values = self.treeview.item(item, "values")
                if search_column == "所有列":
                    if any(search_text.lower() in str(value).lower() for value in values):
                        self.treeview.selection_set(item)
                        self.treeview.see(item)
                        break
                else:
                    # 获取列索引并进行匹配
                    column_index = columns.index(search_column)
                    if search_text.lower() in str(values[column_index]).lower():
                        self.treeview.selection_set(item)
                        self.treeview.see(item)
                        break

        search_btn = tk.Button(search_frame, text="搜索", command=search_data)
        search_btn.pack(side="left", padx=5)

        self.treeview.pack(pady=10, padx=10, fill="both", expand=True)

    def load_data(self):
        try:
            # 构造起始时间和结束时间
            start = f"{self.start_year.get()}-{self.start_month.get()}-{self.start_day.get()} {self.start_hour.get()}:{self.start_minute.get()}"
            end = f"{self.end_year.get()}-{self.end_month.get()}-{self.end_day.get()} {self.end_hour.get()}:{self.end_minute.get()}"
            interval = self.interval_var.get()

            # 校验时间范围
            start_timestamp = pd.Timestamp(start)
            end_timestamp = pd.Timestamp(end)
            if start_timestamp >= end_timestamp:
                messagebox.showerror("错误", "开始日期必须早于结束日期")
                return

            # 启动数据加载线程
            from data_loader import DataLoader
            data_loader = DataLoader(self.root, self.treeview)
            threading.Thread(target=lambda: data_loader.load_data(start, end, interval)).start()
        except Exception as e:
            messagebox.showerror("错误", f"选择时间范围时出错: {e}")

    def plot_kline(self):
        try:
            # 构造起始时间和结束时间
            start = f"{self.start_year.get()}-{self.start_month.get()}-{self.start_day.get()} {self.start_hour.get()}:{self.start_minute.get()}"
            end = f"{self.end_year.get()}-{self.end_month.get()}-{self.end_day.get()} {self.end_hour.get()}:{self.end_minute.get()}"
            interval = self.interval_var.get()

            # 加载数据
            from data_loader import load_klines_from_binance
            data = load_klines_from_binance(start, end, interval)

            # 绘制 K 线图
            plot_kline(data)
        except Exception as e:
            messagebox.showerror("错误", f"绘制 K 线图时出错: {e}")