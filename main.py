import threading
import time
import pandas as pd
import tkinter as tk
from tkinter import ttk
import requests
import os
import json
from tkcalendar import DateEntry
import tkinter.messagebox as messagebox

# 保存用户配置文件的路径
CONFIG_FILE = "config.json"

def load_klines_from_binance(start_time=None, end_time=None, interval="1m"):
    try:
        # 获取 BTC/USDT 的 K 线数据
        url = "https://api.binance.com/api/v3/klines"
        limit = 1000  # 每次最多获取 1000 条数据

        # 准备请求参数
        params = {
            "symbol": "BTCUSDT",
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params["startTime"] = int(pd.Timestamp(start_time).timestamp() * 1000)
        if end_time:
            params["endTime"] = int(pd.Timestamp(end_time).timestamp() * 1000)

        all_data = []
        while True:
            response = requests.get(url, params=params)
            data = response.json()
            if not data:
                break

            all_data.extend(data)

            # 更新 startTime 为最后一条数据的结束时间
            if data:
                last_timestamp = data[-1][0]
                params["startTime"] = last_timestamp + 1
            else:
                break

            # 如果没有更多数据，退出循环
            if len(data) < limit:
                break

            # 检查是否已达到 endTime
            if end_time and last_timestamp >= params["endTime"]:
                break

        # 转换为 DataFrame
        df = pd.DataFrame(all_data, columns=[
            "Timestamp", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
        ])

        # 只保留必要的列
        df = df[["Timestamp", "Open", "High", "Low", "Close", "Volume"]]

        # 将 Timestamp 转换为日期时间格式
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Timestamp", inplace=True)

        return df
    except Exception as e:
        print(f"Error loading data from Binance API: {e}")
        messagebox.showerror("错误", f"加载数据时出错: {e}")
        return None

class DataLoader:
    def __init__(self, root, treeview):
        self.root = root
        self.treeview = treeview
        self.data = None
        self.total_batches = 0
        self.current_batch = 0

    def load_data(self, start_time=None, end_time=None, interval="1m"):
        # 清空旧数据
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        self.data = load_klines_from_binance(start_time, end_time, interval)
        if self.data is None:
            return

        self.total_batches = len(self.data) // 1000 + 1
        self.current_batch = 0
        self.update_data()

    def update_data(self):
        if self.data is None:
            return

        start = self.current_batch * 1000
        end = (self.current_batch + 1) * 1000
        batch_data = self.data[start:end]

        for index, row in batch_data.iterrows():
            self.treeview.insert("", "end", values=(
                index.strftime("%Y-%m-%d %H:%M"),
                row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]
            ))
            self.root.update_idletasks()

        self.current_batch += 1
        if self.current_batch < self.total_batches:
            self.root.after(100, self.update_data)
        else:
            messagebox.showinfo("提示", "数据加载完成")

def create_gui():
    root = tk.Tk()
    root.title("K 线数据加载器")

    data = None
    treeview = None

    # 时间范围选择
    start_year = tk.StringVar(value="2024")
    start_month = tk.StringVar(value="10")
    start_day = tk.StringVar(value="01")
    start_hour = tk.StringVar(value="00")
    start_minute = tk.StringVar(value="00")

    end_year = tk.StringVar(value="2024")
    end_month = tk.StringVar(value="10")
    end_day = tk.StringVar(value="02")
    end_hour = tk.StringVar(value="00")
    end_minute = tk.StringVar(value="00")

    interval_var = tk.StringVar(value="1m")

    def select_time_range():
        try:
            # 构造起始时间和结束时间
            start = f"{start_year.get()}-{start_month.get()}-{start_day.get()} {start_hour.get()}:{start_minute.get()}"
            end = f"{end_year.get()}-{end_month.get()}-{end_day.get()} {end_hour.get()}:{end_minute.get()}"
            interval = interval_var.get()

            # 校验时间范围
            start_timestamp = pd.Timestamp(start)
            end_timestamp = pd.Timestamp(end)
            if start_timestamp >= end_timestamp:
                messagebox.showerror("错误", "开始日期必须早于结束日期")
                return

            # 启动数据加载线程
            data_loader = DataLoader(root, treeview)
            threading.Thread(target=lambda: data_loader.load_data(start, end, interval)).start()
        except Exception as e:
            messagebox.showerror("错误", f"选择时间范围时出错: {e}")

    # 时间范围选择框
    time_frame = tk.Frame(root)
    time_frame.pack(pady=10)

    # 起始时间选择
    tk.Label(time_frame, text="Start Time:").grid(row=0, column=0, padx=5)
    ttk.Spinbox(time_frame, from_=2020, to=2099, textvariable=start_year, width=5).grid(row=0, column=1, padx=5)
    ttk.Spinbox(time_frame, from_=1, to=12, textvariable=start_month, width=5).grid(row=0, column=2, padx=5)
    ttk.Spinbox(time_frame, from_=1, to=31, textvariable=start_day, width=5).grid(row=0, column=3, padx=5)
    ttk.Spinbox(time_frame, from_=0, to=23, textvariable=start_hour, width=5).grid(row=0, column=4, padx=5)
    ttk.Spinbox(time_frame, from_=0, to=59, textvariable=start_minute, width=5).grid(row=0, column=5, padx=5)

    # 结束时间选择
    tk.Label(time_frame, text="End Time:").grid(row=1, column=0, padx=5)
    ttk.Spinbox(time_frame, from_=2020, to=2099, textvariable=end_year, width=5).grid(row=1, column=1, padx=5)
    ttk.Spinbox(time_frame, from_=1, to=12, textvariable=end_month, width=5).grid(row=1, column=2, padx=5)
    ttk.Spinbox(time_frame, from_=1, to=31, textvariable=end_day, width=5).grid(row=1, column=3, padx=5)
    ttk.Spinbox(time_frame, from_=0, to=23, textvariable=end_hour, width=5).grid(row=1, column=4, padx=5)
    ttk.Spinbox(time_frame, from_=0, to=59, textvariable=end_minute, width=5).grid(row=1, column=5, padx=5)

    # 周期选择
    tk.Label(time_frame, text="Interval:").grid(row=2, column=0, padx=5)
    interval_menu = ttk.Combobox(time_frame, textvariable=interval_var, values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"], width=10)
    interval_menu.grid(row=2, column=1, padx=5)

    # 加载按钮
    tk.Button(time_frame, text="Load from Binance", command=select_time_range).grid(row=2, column=2, padx=5)

    # 数据展示
    columns = ("Timestamp", "Open", "High", "Low", "Close", "Volume")
    treeview = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        treeview.heading(col, text=col)
        treeview.column(col, width=100)

    scrollbar = ttk.Scrollbar(root, orient="vertical", command=treeview.yview)
    treeview.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # 添加搜索功能
    search_frame = tk.Frame(root)
    search_frame.pack(pady=10)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side="left")

    search_column_var = tk.StringVar()
    search_column_var.set("所有列")  # 默认值
    search_column_menu = ttk.Combobox(search_frame, textvariable=search_column_var, values=["所有列", "Timestamp", "Open", "High", "Low", "Close", "Volume"])
    search_column_menu.pack(side="left", padx=5)

    def search_data():
        search_text = search_var.get().strip()
        search_column = search_column_var.get()  # 获取用户选择的列

        if not search_text:
            return

        for item in treeview.get_children():
            values = treeview.item(item, "values")
            if search_column == "所有列":
                if any(search_text.lower() in str(value).lower() for value in values):
                    treeview.selection_set(item)
                    treeview.see(item)
                    break
            else:
                # 获取列索引并进行匹配
                column_index = columns.index(search_column)
                if search_text.lower() in str(values[column_index]).lower():
                    treeview.selection_set(item)
                    treeview.see(item)
                    break

    search_btn = tk.Button(search_frame, text="搜索", command=search_data)
    search_btn.pack(side="left", padx=5)

    treeview.pack(pady=10, padx=10, fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    create_gui()