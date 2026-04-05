"""Backtesting engine using backtrader"""
import backtrader as bt
import pandas as pd
from signal_engine import generate_signals, load_config


class SignalStrategy(bt.Strategy):
    """Strategy that follows external signals."""
    
    params = (
        ("printlog", True),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
            
            self.bar_executed = len(self)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        gross = trade.pnl
        net = trade.pnlcomm
        self.log(f"OPERATION PROFIT, GROSS {gross:.2f}, NET {net:.2f}")
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # No position - check for buy signal
            signal = self.datas[0].signal[0]
            if signal > 0:
                self.log(f"BUY CREATE, {self.dataclose[0]:.2f}")
                self.order = self.buy()
        else:
            # Have position - check for sell signal
            signal = self.datas[0].signal[0]
            if signal < 0:
                self.log(f"SELL CREATE, {self.dataclose[0]:.2f}")
                self.order = self.sell()


class PandasDataWithSignal(bt.feeds.PandasData):
    """Custom data feed that includes signal column."""
    lines = ("signal",)
    params = (
        ("signal", -1),
    )


def run_backtest(df: pd.DataFrame, initial_capital: float = 100000, commission: float = 2.5):
    """
    Run backtest on DataFrame with signals.
    
    Args:
        df: DataFrame with OHLCV and 'signal' column
        initial_capital: Starting capital
        commission: Commission per contract per side
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SignalStrategy)
    
    # Prepare data
    data = PandasDataWithSignal(
        dataname=df[["open", "high", "low", "close", "volume", "signal"]],
        datetime=None,
        open=0,
        high=1,
        low=2,
        close=3,
        volume=4,
        signal=5,
    )
    
    cerebro.adddata(data)
    cerebro.broker.setcash(initial_capital)
    # NQ futures: $20 per point, commission per contract per side
    cerebro.broker.setcommission(
        commission=commission,
        mult=20,  # $20 per point for NQ
        margin=12000  # Margin per contract
    )
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)  # 1 contract
    
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    
    results = cerebro.run()
    
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")
    print(f"Total Return: {((cerebro.broker.getvalue() - initial_capital) / initial_capital * 100):.2f}%")
    
    return cerebro, results


if __name__ == "__main__":
    from data_fetcher import get_data
    from signal_engine import generate_signals
    
    config = load_config()
    df = get_data()
    df_signals = generate_signals(df, config)
    
    cerebro, results = run_backtest(
        df_signals,
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"]
    )
