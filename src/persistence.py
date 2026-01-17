"""Persistence layer for recording trades, ticks, and metrics."""

from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from src.portfolio import Portfolio


class Recorder:
    """Records trades, metrics, and equity curve to persistent storage."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize recorder.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def save_trades(self, portfolio: Portfolio, filename: Optional[str] = None) -> str:
        """Save trades to CSV/Parquet.
        
        Args:
            portfolio: Portfolio containing trades
            filename: Optional filename (default: trades.parquet)
            
        Returns:
            Path to saved file
        """
        if not portfolio.trades:
            return None
            
        df = pd.DataFrame(portfolio.trades)
        filepath = self.output_dir / (filename or "trades.parquet")
        
        if filepath.suffix == ".parquet":
            df.to_parquet(filepath, index=False)
        else:
            df.to_csv(filepath, index=False)
            
        return str(filepath)
    
    def save_equity_curve(self, portfolio: Portfolio, filename: Optional[str] = None) -> str:
        """Save equity curve to CSV/Parquet.
        
        Args:
            portfolio: Portfolio containing equity curve
            filename: Optional filename (default: equity_curve.parquet)
            
        Returns:
            Path to saved file
        """
        if not portfolio.equity_curve:
            return None
            
        df = pd.DataFrame({
            'timestamp': range(len(portfolio.equity_curve)),  # TODO: use actual timestamps
            'equity': portfolio.equity_curve
        })
        filepath = self.output_dir / (filename or "equity_curve.parquet")
        
        if filepath.suffix == ".parquet":
            df.to_parquet(filepath, index=False)
        else:
            df.to_csv(filepath, index=False)
            
        return str(filepath)
    
    def save_metrics(self, metrics: Dict, filename: Optional[str] = None) -> str:
        """Save metrics to CSV/Parquet.
        
        Args:
            metrics: Dictionary of metrics to save
            filename: Optional filename (default: metrics.parquet)
            
        Returns:
            Path to saved file
        """
        if not metrics:
            return None
            
        # Convert metrics to DataFrame (single row)
        df = pd.DataFrame([metrics])
        filepath = self.output_dir / (filename or "metrics.parquet")
        
        if filepath.suffix == ".parquet":
            df.to_parquet(filepath, index=False)
        else:
            df.to_csv(filepath, index=False)
            
        return str(filepath)
    
    def compute_metrics(self, portfolio: Portfolio) -> Dict:
        """Compute portfolio metrics from trades and equity curve.
        
        Args:
            portfolio: Portfolio to compute metrics for
            
        Returns:
            Dictionary of computed metrics
        """
        if not portfolio.trades or not portfolio.equity_curve:
            return {}
        
        df_trades = pd.DataFrame(portfolio.trades)
        equity_series = pd.Series(portfolio.equity_curve)
        
        # Basic metrics
        total_return = (equity_series.iloc[-1] - equity_series.iloc[0]) / equity_series.iloc[0]
        
        # Compute returns for Sharpe ratio
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
        
        # Maximum drawdown
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate (from trades, if we can compute PnL per trade)
        # This is simplified - real implementation would track PnL per trade
        num_trades = len(df_trades)
        win_rate = 0.5  # Placeholder - would need to compute from fills
        
        # Average hold time (placeholder)
        avg_hold_time = 0.0  # Would need to track entry/exit times
        
        # Turnover
        total_volume = df_trades['quantity'].abs().sum() if 'quantity' in df_trades.columns else 0
        initial_equity = portfolio.initial_cash
        turnover = total_volume / initial_equity if initial_equity > 0 else 0
        
        return {
            'initial_cash': portfolio.initial_cash,
            'final_equity': equity_series.iloc[-1],
            'total_return': total_return,
            'annualized_return': total_return,  # Would need time period for proper annualization
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': num_trades,
            'avg_hold_time': avg_hold_time,
            'turnover': turnover,
            'total_volume': total_volume
        }
