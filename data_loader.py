import pandas as pd
import requests
import tkinter.messagebox as messagebox
from kline_plotter import plot_kline


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
            messagebox.showinfo("提示", "数据加载完成")  # 只显示成功提示框