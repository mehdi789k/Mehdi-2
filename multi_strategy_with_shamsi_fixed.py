import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice
from khayyam import JalaliDate
from matplotlib import rc

# پشتیبانی از زبان فارسی در نمودارها
rc('font', family='DejaVu Sans')
plt.rcParams["axes.unicode_minus"] = False

# مسیر پیش‌فرض برای فایل CSV
DEFAULT_CSV_PATH = "dot.v_15.csv"

# تابع خواندن داده‌ها از فایل CSV
def load_data(file_path):
    if not os.path.exists(file_path):
        print(f"فایل {file_path} یافت نشد. لطفاً اطمینان حاصل کنید که فایل در مسیر مشخص موجود است.")
        exit()
    data = pd.read_csv(file_path)
    # ترکیب ستون‌های تاریخ و زمان
    data['DateTime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'])
    data.drop(['Date', 'Time'], axis=1, inplace=True)
    data.set_index('DateTime', inplace=True)
    # تبدیل تاریخ به شمسی
    data['تاریخ شمسی'] = data.index.map(lambda x: JalaliDate(x).strftime('%Y-%m-%d'))
    return data

# محاسبه اندیکاتورهای مورد نیاز
def calculate_indicators(data):
    data['EMA_50'] = EMAIndicator(data['Close'], window=50).ema_indicator()
    data['EMA_200'] = EMAIndicator(data['Close'], window=200).ema_indicator()
    data['RSI'] = RSIIndicator(data['Close'], window=14).rsi()
    data['VWAP'] = VolumeWeightedAveragePrice(
        high=data['High'], low=data['Low'], close=data['Close'], volume=data['Volume']
    ).volume_weighted_average_price()
    return data

# استراتژی ترکیبی: روند + الگوهای قیمتی + حجم و RSI
def combined_strategy(data):
    signals = []
    for i in range(len(data)):
        row = data.iloc[i]
        if row['Close'] > row['EMA_50'] > row['EMA_200'] and 40 < row['RSI'] < 70:
            signals.append('خرید')
        elif row['Close'] < row['EMA_50'] < row['EMA_200'] and row['RSI'] < 60:
            signals.append('فروش')
        else:
            signals.append('بدون سیگنال')
    data['سیگنال ترکیبی'] = signals
    return data

# استراتژی Pinbar + EMA
def pinbar_ema_strategy(data):
    signals = ['بدون سیگنال']  # مقدار پیش‌فرض برای ردیف اول
    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]
        if row['Close'] > row['EMA_50'] and prev_row['Low'] > row['Low']:
            signals.append('خرید')
        elif row['Close'] < row['EMA_50'] and prev_row['High'] < row['High']:
            signals.append('فروش')
        else:
            signals.append('بدون سیگنال')
    data['سیگنال Pinbar + EMA'] = signals
    return data

# استراتژی Bollinger Bands + RSI
def bb_rsi_strategy(data):
    signals = []
    for i in range(len(data)):
        row = data.iloc[i]
        if row['Close'] < row['VWAP'] and row['RSI'] < 30:
            signals.append('خرید')
        elif row['Close'] > row['VWAP'] and row['RSI'] > 70:
            signals.append('فروش')
        else:
            signals.append('بدون سیگنال')
    data['سیگنال BB + RSI'] = signals
    return data

# استراتژی Pullback در روند
def pullback_strategy(data):
    signals = ['بدون سیگنال']  # مقدار پیش‌فرض برای ردیف اول
    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]
        if row['Close'] > row['EMA_50'] and prev_row['Close'] < row['Close']:
            signals.append('خرید')
        elif row['Close'] < row['EMA_50'] and prev_row['Close'] > row['Close']:
            signals.append('فروش')
        else:
            signals.append('بدون سیگنال')
    data['سیگنال Pullback'] = signals
    return data

# ترکیب تمامی استراتژی‌ها
def combine_strategies(data):
    data = combined_strategy(data)
    data = pinbar_ema_strategy(data)
    data = bb_rsi_strategy(data)
    data = pullback_strategy(data)
    return data

# نمایش سیگنال‌های نهایی
def plot_signals(data, strategy_column):
    plt.figure(figsize=(16, 8))
    plt.plot(data.index, data['Close'], label='قیمت پایانی', color='blue', alpha=0.7)
    plt.plot(data.index, data['EMA_50'], label='EMA 50', color='orange', alpha=0.7)
    plt.plot(data.index, data['EMA_200'], label='EMA 200', color='red', alpha=0.7)

    buy_signals = data[data[strategy_column] == 'خرید']
    sell_signals = data[data[strategy_column] == 'فروش']

    plt.scatter(buy_signals.index, buy_signals['Close'], label='سیگنال خرید', marker='^', color='green', alpha=1)
    plt.scatter(sell_signals.index, sell_signals['Close'], label='سیگنال فروش', marker='v', color='red', alpha=1)

    plt.title('سیگنال‌های نهایی', fontsize=14)
    plt.xlabel('تاریخ', fontsize=12)
    plt.ylabel('قیمت', fontsize=12)
    plt.legend()
    plt.grid()
    plt.show()

# اجرای برنامه اصلی
if __name__ == "__main__":
    # استفاده از مسیر پیش‌فرض
    print(f"در حال بارگذاری فایل از مسیر پیش‌فرض: {DEFAULT_CSV_PATH}")
    data = load_data(DEFAULT_CSV_PATH)
    data = calculate_indicators(data)
    data = combine_strategies(data)

    # نمایش نتایج
    print(data[['تاریخ شمسی', 'سیگنال ترکیبی', 'سیگنال Pinbar + EMA', 'سیگنال BB + RSI', 'سیگنال Pullback']].tail())
    plot_signals(data, 'سیگنال ترکیبی')