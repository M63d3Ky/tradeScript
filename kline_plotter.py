import mplfinance as mpf
import pandas as pd
import tkinter.messagebox as messagebox

def plot_kline(data, root):
    """
    绘制 K 线图
    :param data: pandas DataFrame，包含时间序列数据，列名包括 ['Open', 'High', 'Low', 'Close', 'Volume']
    :param root: Tkinter 根窗口对象
    """
    if data is None or data.empty:
        messagebox.showerror("错误", "没有数据可供绘制。")
        return

    # 确保数据包含必要的列
    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    if not all(col in data.columns for col in required_columns):
        messagebox.showerror("错误", f"缺少必要的列: {required_columns}")
        return

    # 确保数据类型为浮点数
    for col in required_columns:
        data[col] = data[col].astype(float)

    # 添加均线（可选）
    data["MA10"] = data["Close"].rolling(window=10).mean()
    data["MA20"] = data["Close"].rolling(window=20).mean()

    # 绘制 K 线图
    try:
        mpf.plot(data, type='candle',
                title='K-line Chart',
                mav=(10, 20),  # 添加均线
                volume=True,  # 显示成交量
                style='charles')  # 设置样式
    except Exception as e:
        messagebox.showerror("错误", f"绘制 K 线图时出错: {e}")