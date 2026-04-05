"""CLI for NQ Trader - adjust parameters and run backtests"""
import typer
import yaml
from datetime import datetime

from data_fetcher import get_data
from signal_engine import generate_signals, load_config
from backtester import run_backtest

app = typer.Typer(help="NQ Futures Trading Signal System")


@app.command()
def backtest(
    signal_type: str = typer.Option("sma_crossover", "--signal", "-s", help="Signal type: sma_crossover, rsi, macd"),
    short_window: int = typer.Option(None, "--short", help="Short window (SMA)"),
    long_window: int = typer.Option(None, "--long", help="Long window (SMA)"),
    rsi_period: int = typer.Option(None, "--rsi-period", help="RSI period"),
    rsi_oversold: int = typer.Option(None, "--rsi-oversold", help="RSI oversold level"),
    rsi_overbought: int = typer.Option(None, "--rsi-overbought", help="RSI overbought level"),
    start_date: str = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
):
    """Run backtest with specified parameters."""
    config = load_config()
    
    # Override signal config
    config["signal"]["type"] = signal_type
    if short_window:
        config["signal"]["short_window"] = short_window
    if long_window:
        config["signal"]["long_window"] = long_window
    if rsi_period:
        config["signal"]["rsi_period"] = rsi_period
    if rsi_oversold:
        config["signal"]["rsi_oversold"] = rsi_oversold
    if rsi_overbought:
        config["signal"]["rsi_overbought"] = rsi_overbought
    
    # Override backtest dates
    if start_date:
        config["backtest"]["start_date"] = start_date
    if end_date:
        config["backtest"]["end_date"] = end_date
    
    print(f"Signal: {config['signal']['type']}")
    print(f"Period: {config['backtest']['start_date']} to {config['backtest']['end_date']}")
    print("-" * 50)
    
    df = get_data(config["backtest"]["start_date"], config["backtest"]["end_date"])
    df_signals = generate_signals(df, config)
    
    signal_count = df_signals["signal"].value_counts()
    print(f"\nSignal summary:")
    for sig, count in signal_count.items():
        label = {1: "BUY", -1: "SELL", 0: "HOLD"}.get(sig, "UNKNOWN")
        print(f"  {label}: {count}")
    
    print("\nRunning backtest...")
    print("-" * 50)
    
    cerebro, results = run_backtest(
        df_signals,
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"]
    )


@app.command()
def show_config():
    """Display current configuration."""
    config = load_config()
    print(yaml.dump(config, default_flow_style=False))


@app.command()
def save_config(
    signal_type: str = typer.Option(None, "--signal", "-s"),
    short_window: int = typer.Option(None, "--short"),
    long_window: int = typer.Option(None, "--long"),
    rsi_period: int = typer.Option(None, "--rsi-period"),
    rsi_oversold: int = typer.Option(None, "--rsi-oversold"),
    rsi_overbought: int = typer.Option(None, "--rsi-overbought"),
):
    """Save configuration changes to config.yaml."""
    config = load_config()
    
    if signal_type:
        config["signal"]["type"] = signal_type
    if short_window:
        config["signal"]["short_window"] = short_window
    if long_window:
        config["signal"]["long_window"] = long_window
    if rsi_period:
        config["signal"]["rsi_period"] = rsi_period
    if rsi_oversold:
        config["signal"]["rsi_oversold"] = rsi_oversold
    if rsi_overbought:
        config["signal"]["rsi_overbought"] = rsi_overbought
    
    with open("config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("Config saved.")


if __name__ == "__main__":
    app()
