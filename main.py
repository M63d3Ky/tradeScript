import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
import requests
import os
import json

# 保存用户配置文件的路径
CONFIG_FILE = "config.json"


def load_klines_from_binance():
    try:
        # 获取 BTC/USDT 的 K 线数据（1分钟间隔）
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 1000  # 每次最多获取 1000 条数据
        }
        response = requests.get(url, params=params)
        data = response.json()

        # 转换为 DataFrame
        df = pd.DataFrame(data, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Timestamp", inplace=True)

        return df
    except Exception as e:
        print(f"Error loading data from Binance API: {e}")
        return None


def load_klines_from_file(file_path):
    try:
        data = pd.read_csv(file_path)
        if "Date" not in data.columns:
            raise ValueError("文件中缺少 'Date' 列")
        data["Date"] = pd.to_datetime(data["Date"])
        data.set_index("Date", inplace=True)
        return data
    except Exception as e:
        print(f"Error loading data from file: {e}")
        return None


def create_gui():
    root = tk.Tk()
    root.title("K 线数据加载器")

    data = None
    treeview = None

    # 加载用户配置
    user_config = {"last_file_path": None, "default_source": "file"}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            user_config = json.load(f)
    else:
        with open(CONFIG_FILE, "w") as f:
            json.dump(user_config, f)

    def load_data():
        nonlocal data
        if user_config["default_source"] == "file" and user_config["last_file_path"]:
            data = load_klines_from_file(user_config["last_file_path"])
        elif user_config["default_source"] == "api":
            data = load_klines_from_binance()
        update_data_display(data)

    def update_data_display(data):
        nonlocal treeview
        if data is not None:
            if treeview:
                treeview.destroy()

            columns = ("Timestamp", "Open", "High", "Low", "Close", "Volume")
            treeview = ttk.Treeview(root, columns=columns, show="headings")
            for col in columns:
                treeview.heading(col, text=col)
                treeview.column(col, width=100)

            for index, row in data.iterrows():
                treeview.insert("", "end", values=(
                index.strftime("%Y-%m-%d %H:%M"), row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]))

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
            search_column_menu = ttk.OptionMenu(search_frame, search_column_var, "所有列", "Timestamp", "Open", "High",
                                                "Low", "Close", "Volume")
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
                        if search_text.lower() in str(values[treeview.columns.index(search_column)]).lower():
                            treeview.selection_set(item)
                            treeview.see(item)
                            break

            search_btn = tk.Button(search_frame, text="搜索", command=search_data)
            search_btn.pack(side="left", padx=5)

            treeview.pack(pady=10, padx=10, fill="both", expand=True)

    file_button = tk.Button(root, text="从本地文件加载", command=lambda: load_klines_from_file(
        filedialog.askopenfilename(filetypes=[("CSV 文件", "*.csv")])))
    api_button = tk.Button(root, text="从 Binance API 加载", command=load_klines_from_binance)

    file_button.pack(pady=10)
    api_button.pack(pady=10)

    load_data()

    root.mainloop()


if __name__ == "__main__":
    create_gui()