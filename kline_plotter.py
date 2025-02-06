import mplfinance as mpf
import pandas as pd

def plot_kline(data):
    """
    绘制 K 线图
    :param data: pandas DataFrame，包含时间序列数据，列名包括 ['Open', 'High', 'Low', 'Close', 'Volume']
    """
    try:
        if data is None or data.empty:
            print("No data to plot.")
            return

        # 确保数据包含必要的列
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Missing required columns: {required_columns}")

        # 添加均线（可选）
        data["MA10"] = data["Close"].rolling(window=10).mean()
        data["MA20"] = data["Close"].rolling(window=20).mean()

        # 绘制 K 线图
        mpf.plot(data, type='candle',
                title='K-line Chart',
                mav=(10, 20),  # 添加均线
                volume=True,  # 显示成交量
                style='charles')  # 设置样式
    except Exception as e:
        print(f"Error plotting K-line chart: {e}")