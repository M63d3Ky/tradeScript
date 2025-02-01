import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
import os
import json
import requests

# 保存用户配置文件的路径
CONFIG_FILE = "config.json"


def load_klines_from_file(file_path):
    try:
        data = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
        return data
    except Exception as e:
        print(f"Error loading data from file: {e}")
        return None


def load_klines_from_api():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30")
        data = response.json()

        prices = data["prices"]
        df = pd.DataFrame(prices, columns=["Date", "Close"])
        df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        df.set_index("Date", inplace=True)

        df["Open"] = df["Close"]
        df["High"] = df["Close"]
        df["Low"] = df["Close"]
        return df
    except Exception as e:
        print(f"Error loading data from API: {e}")
        return None


def create_gui():
    root = tk.Tk()
    root.title("K 线数据加载器")

    data = None
    treeview = None

    # 加载用户配置（记录用户最后的选择）
    user_config = {"last_file_path": None, "default_source": "file"}  # 默认配置
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            user_config = json.load(f)
    else:
        with open(CONFIG_FILE, "w") as f:
            json.dump(user_config, f)

    def load_from_file():
        nonlocal data
        if user_config["last_file_path"]:
            initial_dir = os.path.dirname(user_config["last_file_path"])
        else:
            initial_dir = os.getcwd()

        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("CSV 文件", "*.csv")])
        if file_path:
            data = load_klines_from_file(file_path)
            user_config["last_file_path"] = file_path
            user_config["default_source"] = "file"
            with open(CONFIG_FILE, "w") as f:
                json.dump(user_config, f)
            update_data_display(data)

    def load_from_api():
        nonlocal data
        data = load_klines_from_api()
        user_config["default_source"] = "api"
        with open(CONFIG_FILE, "w") as f:
            json.dump(user_config, f)
        update_data_display(data)

    def update_data_display(data):
        nonlocal treeview
        if data is not None:
            # 清空表格
            if treeview:
                treeview.destroy()

            # 创建新的表格
            columns = ("Date", "Open", "Close", "High", "Low")
            treeview = ttk.Treeview(root, columns=columns, show="headings")
            for col in columns:
                treeview.heading(col, text=col)
                treeview.column(col, width=100)

            # 插入数据
            for index, row in data.iterrows():
                treeview.insert("", "end", values=(index.date(), row["Open"], row["Close"], row["High"], row["Low"]))

            # 添加滚动条
            scrollbar = ttk.Scrollbar(root, orient="vertical", command=treeview.yview)
            treeview.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            # 绑定中键拖动事件
            treeview.bind("<Button-2>", lambda e: treeview.yview_scroll(1, "units"))
            treeview.bind("<B2-Motion>", lambda e: treeview.yview_scroll(1, "units"))

            # 给表格添加搜索功能
            search_frame = tk.Frame(root)
            search_frame.pack(pady=10)

            # 添加搜索框
            search_var = tk.StringVar()
            search_entry = tk.Entry(search_frame, textvariable=search_var)
            search_entry.pack(side="left")

            def search_data():
                search_text = search_var.get().strip()
                if not search_text:
                    return
                for item in treeview.get_children():
                    values = treeview.item(item, "values")
                    if any(search_text.lower() in str(value).lower() for value in values):
                        treeview.selection_set(item)
                        treeview.see(item)
                        break

            search_btn = tk.Button(search_frame, text="搜索", command=search_data)
            search_btn.pack(side="left", padx=5)

            treeview.pack(pady=10, padx=10, fill="both", expand=True)

    def auto_load_data():
        if user_config["default_source"] == "file" and user_config["last_file_path"]:
            data = load_klines_from_file(user_config["last_file_path"])
            update_data_display(data)
        elif user_config["default_source"] == "api":
            load_from_api()

    file_button = tk.Button(root, text="从本地文件加载", command=load_from_file)
    api_button = tk.Button(root, text="从 API 加载", command=load_from_api)

    file_button.pack(pady=10)
    api_button.pack(pady=10)

    # 自动加载上次用户选择的数据
    auto_load_data()

    root.mainloop()


# 启动程序
create_gui()