"""Visualization utilities for backtesting results."""

from typing import List, Optional, Dict
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def plot_equity_curve(equity_curve: List[float], benchmark: Optional[List[float]] = None) -> None:
    """Plot equity curve with optional benchmark.
    
    Args:
        equity_curve: List of equity values over time
        benchmark: Optional benchmark equity curve for comparison
    """
    plt.figure(figsize=(12, 6))
    plt.plot(equity_curve, label='Equity Curve', linewidth=2)
    if benchmark:
        plt.plot(benchmark, label='Benchmark', linewidth=2, alpha=0.7)
    plt.xlabel('Time')
    plt.ylabel('Equity')
    plt.title('Equity Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def plot_interactive_equity_curve(equity_curve: List[float], benchmark: Optional[List[float]] = None) -> None:
    """Plot interactive equity curve with optional benchmark.
    
    Args:
        equity_curve: List of equity values over time
        benchmark: Optional benchmark equity curve for comparison
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=equity_curve, mode='lines', name='Equity Curve', line=dict(width=2)))
    if benchmark:
        fig.add_trace(go.Scatter(y=benchmark, mode='lines', name='Benchmark', line=dict(width=2, dash='dash')))
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Time',
        yaxis_title='Equity',
        hovermode='x unified'
    )
    fig.show()


def plot_price_chart_with_trades(
    prices: Dict[str, List[float]],
    trades: pd.DataFrame,
    timestamps: Optional[List] = None
) -> None:
    """Plot price chart with entry/exit markers for both legs (pair trading).
    
    Args:
        prices: Dictionary mapping symbol to price series
        trades: DataFrame with columns: timestamp, symbol, side, quantity, price
        timestamps: Optional timestamps for x-axis
    """
    num_symbols = len(prices)
    fig, axes = plt.subplots(num_symbols, 1, figsize=(12, 6 * num_symbols), sharex=True)
    
    if num_symbols == 1:
        axes = [axes]
    
    for idx, (symbol, price_series) in enumerate(prices.items()):
        ax = axes[idx]
        x_axis = timestamps if timestamps else range(len(price_series))
        
        ax.plot(x_axis, price_series, label=f'{symbol} Price', linewidth=1.5)
        
        # Plot entry/exit markers
        symbol_trades = trades[trades['symbol'] == symbol]
        for _, trade in symbol_trades.iterrows():
            # Find closest timestamp index
            if timestamps:
                # Would need to match timestamp to index
                pass
            else:
                # Use price index as approximation
                color = 'green' if trade['side'] == 'BUY' else 'red'
                marker = '^' if trade['side'] == 'BUY' else 'v'
                ax.scatter(0, trade['price'], color=color, marker=marker, s=100, alpha=0.7)
        
        ax.set_ylabel(f'{symbol} Price')
        ax.set_title(f'{symbol} Price with Trade Markers')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Time')
    plt.tight_layout()
    plt.show()


def plot_spread_and_zscore(
    spread: List[float],
    zscore: Optional[List[float]] = None,
    thresholds: Optional[Dict[str, float]] = None,
    timestamps: Optional[List] = None
) -> None:
    """Plot spread and z-score with threshold lines.
    
    Args:
        spread: Spread series (e.g., price_A - price_B)
        zscore: Optional z-score series
        thresholds: Optional dict with keys like 'entry', 'exit' for threshold lines
        timestamps: Optional timestamps for x-axis
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    x_axis = timestamps if timestamps else range(len(spread))
    
    # Plot spread
    axes[0].plot(x_axis, spread, label='Spread', linewidth=1.5)
    if thresholds and 'spread_entry' in thresholds:
        axes[0].axhline(thresholds['spread_entry'], color='green', linestyle='--', label='Entry Threshold')
        axes[0].axhline(-thresholds['spread_entry'], color='green', linestyle='--')
    if thresholds and 'spread_exit' in thresholds:
        axes[0].axhline(thresholds['spread_exit'], color='red', linestyle='--', label='Exit Threshold')
        axes[0].axhline(-thresholds['spread_exit'], color='red', linestyle='--')
    axes[0].set_ylabel('Spread')
    axes[0].set_title('Spread Over Time')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot z-score
    if zscore is not None:
        axes[1].plot(x_axis, zscore, label='Z-Score', linewidth=1.5, color='orange')
        if thresholds and 'zscore_entry' in thresholds:
            axes[1].axhline(thresholds['zscore_entry'], color='green', linestyle='--', label='Entry Threshold')
            axes[1].axhline(-thresholds['zscore_entry'], color='green', linestyle='--')
        if thresholds and 'zscore_exit' in thresholds:
            axes[1].axhline(thresholds['zscore_exit'], color='red', linestyle='--', label='Exit Threshold')
            axes[1].axhline(-thresholds['zscore_exit'], color='red', linestyle='--')
        axes[1].axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
    axes[1].set_ylabel('Z-Score')
    axes[1].set_xlabel('Time')
    axes[1].set_title('Z-Score Over Time')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def plot_position_size(positions: Dict[str, List[float]], timestamps: Optional[List] = None) -> None:
    """Plot position size over time.
    
    Args:
        positions: Dictionary mapping symbol to position size series
        timestamps: Optional timestamps for x-axis
    """
    plt.figure(figsize=(12, 6))
    
    x_axis = timestamps if timestamps else range(len(next(iter(positions.values()))))
    
    for symbol, position_series in positions.items():
        plt.plot(x_axis, position_series, label=f'{symbol} Position', linewidth=1.5)
    
    plt.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
    plt.xlabel('Time')
    plt.ylabel('Position Size')
    plt.title('Position Size Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def plot_trade_list_table(trades: pd.DataFrame) -> None:
    """Display trade list as formatted table.
    
    Args:
        trades: DataFrame with columns: timestamp, symbol, side, size, price, pnl
    """
    # Ensure required columns exist
    required_cols = ['timestamp', 'symbol', 'side', 'quantity', 'price']
    missing_cols = [col for col in required_cols if col not in trades.columns]
    
    if missing_cols:
        print(f"Warning: Missing columns in trades DataFrame: {missing_cols}")
        return
    
    # Display formatted table
    display_df = trades[required_cols].copy()
    if 'pnl' in trades.columns:
        display_df['pnl'] = trades['pnl']
    
    print(display_df.to_string(index=False))


def plot_interactive_comprehensive(
    prices: Dict[str, List[float]],
    spread: List[float],
    zscore: Optional[List[float]],
    equity_curve: List[float],
    trades: Optional[pd.DataFrame] = None
) -> None:
    """Create comprehensive interactive dashboard with multiple plots.
    
    Args:
        prices: Dictionary mapping symbol to price series
        spread: Spread series
        zscore: Optional z-score series
        equity_curve: Equity curve series
        trades: Optional trades DataFrame
    """
    num_subplots = 3 + (1 if zscore is not None else 0)
    fig = make_subplots(
        rows=num_subplots,
        cols=1,
        subplot_titles=(
            ['Price Charts'] + 
            (['Z-Score'] if zscore is not None else []) +
            ['Spread', 'Equity Curve']
        ),
        vertical_spacing=0.05
    )
    
    row = 1
    
    # Price charts
    for symbol, price_series in prices.items():
        fig.add_trace(
            go.Scatter(y=price_series, mode='lines', name=f'{symbol} Price'),
            row=row, col=1
        )
    
    # Z-score
    if zscore is not None:
        row += 1
        fig.add_trace(
            go.Scatter(y=zscore, mode='lines', name='Z-Score', line=dict(color='orange')),
            row=row, col=1
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=row, col=1)
    
    # Spread
    row += 1
    fig.add_trace(
        go.Scatter(y=spread, mode='lines', name='Spread', line=dict(color='blue')),
        row=row, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", row=row, col=1)
    
    # Equity curve
    row += 1
    fig.add_trace(
        go.Scatter(y=equity_curve, mode='lines', name='Equity Curve', line=dict(color='green', width=2)),
        row=row, col=1
    )
    
    fig.update_layout(height=800, title_text="Backtest Dashboard", hovermode='x unified')
    fig.show()