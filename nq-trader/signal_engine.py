"""Trading signal generation with configurable parameters"""
import pandas as pd
import numpy as np
import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def sma_crossover(df: pd.DataFrame, short_window: int, long_window: int) -> pd.Series:
    """
    Generate signals based on SMA crossover.
    Returns: 1 = buy, -1 = sell, 0 = hold
    """
    df = df.copy()
    df["sma_short"] = df["close"].rolling(window=short_window).mean()
    df["sma_long"] = df["close"].rolling(window=long_window).mean()
    
    signals = pd.Series(0, index=df.index)
    
    # Buy when short crosses above long
    buy_mask = (df["sma_short"] > df["sma_long"]) & (df["sma_short"].shift(1) <= df["sma_long"].shift(1))
    signals[buy_mask] = 1
    
    # Sell when short crosses below long
    sell_mask = (df["sma_short"] < df["sma_long"]) & (df["sma_short"].shift(1) >= df["sma_long"].shift(1))
    signals[sell_mask] = -1
    
    return signals


def rsi_strategy(df: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.Series:
    """
    RSI-based strategy.
    Buy when RSI < oversold, sell when RSI > overbought.
    """
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    
    signals = pd.Series(0, index=df.index)
    signals[df["rsi"] < oversold] = 1
    signals[df["rsi"] > overbought] = -1
    
    return signals


def macd_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal_line: int = 9) -> pd.Series:
    """
    MACD crossover strategy.
    """
    df = df.copy()
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal_line, adjust=False).mean()
    
    signals = pd.Series(0, index=df.index)
    
    # Buy: MACD crosses above signal line
    buy_mask = (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
    signals[buy_mask] = 1
    
    # Sell: MACD crosses below signal line
    sell_mask = (df["macd"] < df["macd_signal"]) & (df["macd"].shift(1) >= df["macd_signal"].shift(1))
    signals[sell_mask] = -1
    
    return signals


def generate_signals(df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
    """
    Generate trading signals based on config.
    Returns DataFrame with 'signal' column (1=buy, -1=sell, 0=hold).
    """
    if config is None:
        config = load_config()
    
    signal_type = config["signal"]["type"]
    
    if signal_type == "sma_crossover":
        signals = sma_crossover(
            df,
            short_window=config["signal"]["short_window"],
            long_window=config["signal"]["long_window"]
        )
    elif signal_type == "rsi":
        signals = rsi_strategy(
            df,
            period=config["signal"]["rsi_period"],
            oversold=config["signal"]["rsi_oversold"],
            overbought=config["signal"]["rsi_overbought"]
        )
    elif signal_type == "macd":
        signals = macd_strategy(df)
    else:
        raise ValueError(f"Unknown signal type: {signal_type}")
    
    result = df.copy()
    result["signal"] = signals
    return result


if __name__ == "__main__":
    from data_fetcher import get_data
    df = get_data()
    result = generate_signals(df)
    print(result[["close", "signal"]].tail(20))
