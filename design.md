## Requirements

1. Be able to backtest and switch to live trading very easily
2. Allow pair-trading strategies
3. Efficient backtesting
4. Adaptable to different data sources
5. During backtest, support visualization
6. Taker strategy only

## Design

### **High-level architecture**

- Single codebase exposes the same Strategy API in both modes.
- Two pluggable runtime engines:
    - BacktestEngine: reads historical data, advances simulated time, routes events to Strategy, simulates orders via BrokerSim.
    - LiveEngine: subscribes to real data feed(s), routes real-time events to the same Strategy instance, sends orders to ExecutionClient (real broker).
- Key invariants:
    - Strategy code must be mode-agnostic (no if live/backtest inside strategy).
    - All I/O (data, execution) behind interfaces so you can swap implementations by config.
- Minimal component graph:
    - Config -> Engine (Backtest or Live)
    - Engine uses DataClient + ExecutionClient + Portfolio + RiskManager + EventBus
    - Strategy subscribes to events and issues Orders via a simple API

### **Core components and interfaces (python sketches)**

- DataClient (interface)
    - backtest: yields historical events (bar/tick) via generator or async stream
    - live: subscribes to real streaming API and invokes callbacks
- ExecutionClient (interface)
    - backtest: BrokerSim that receives MarketOrder, executes at simulated price (next tick/last tick/mid + slippage model), returns Fill events
    - live: sends market orders to broker API
- Strategy (base class)
    - on_event(event) callback (or on_bar, on_tick)
    - on_fill(fill)
    - create_order(Order) -> returns OrderId or raises
- Portfolio / Position manager
    - track positions, PnL, realized/unrealized
    - apply fills to update cash/position
- RiskManager (optional for simple rules)
    - validate sizing & checks (max position, margin)
- Engine
    - event loop: pulls events from DataClient, passes to Strategy, collects emitted Orders, routes to ExecutionClient, applies fills to Portfolio
    - metric collector: equity curve, trades, turnover, drawdown
- Persistence / Recorder
    - write trades, ticks, metrics (CSV/Parquet) for later visualization

Example minimal class signatures (not full code):

`class DataClient(ABC):
    def subscribe(self, symbols: List[str], callback: Callable[[Event], None]) -> None: ...
    def stream(self) -> Iterator[Event]: ...  # backtest mode

class ExecutionClient(ABC):
    def send_order(self, order: Order) -> OrderId: ...
    def cancel_order(self, order_id: OrderId) -> None: ...

class Strategy(ABC):
    def initialize(self, context: StrategyContext): ...
    def on_event(self, event: Event): ...
    def on_fill(self, fill: Fill): ...`

### Efficiency for backtesting options

A. Vectorized backtesting (fastest for indicators & simple signals)

- Load aligned time-series into numpy/pandas arrays
- Compute rolling statistics (beta, mean, std) using vectorized rolling (pandas .rolling or numba)
- Generate signals as boolean arrays, compute positions and PnL in bulk
- Best when strategy logic can be expressed in array ops (many pair strategies can)

B. Event-driven backtest (more flexible)

- Process events one at a time in a loop (closer to live)
- Easier to simulate order book, slippage, partial fills
- Slower but more accurate for complex order interactions

C. Hybrid

- Compute indicators vectorized, but simulate orders in event loop (gives speed while keeping realistic order simulation)

### Data source adaptability

- Abstract DataClient with flavors:
    - CSV/ParquetReader: historical file
    - DataProviderClient: wrapper around API (Polygon, Binance, broker)
    - ReplayClient: pre-recorded trade/tick replay
- Provide adapters that normalize raw feed into common Event schema (timestamp, symbol, bid, ask, trade_price, volume).
- Provide resampling & alignment utilities for pair trading:
    - join on timestamp inner/outer
    - forward/backfill missing values with caution (affects cointegration)
- Suggest storage format: Parquet with partitioning by symbol/date for efficient reads.

### Visualization during backtest

- Real-time / per-run visualization:
    - Equity curve, drawdowns, trade markers on price chart
    - Spread, z-score, rolling mean/std
    - Position size over time
- Tools:
    - Matplotlib for static plots
    - Plotly for interactive time-series; useful for hover/zoom
    - Streamlit or Dash for interactive dashboards that show charts and tables while backtest runs or after completion
- Minimal plots to implement:
    - Price chart with entry/exit markers for both legs
    - Spread and z-score with threshold lines
    - Equity curve vs benchmark
    - Trade list table (time, symbol, side, size, price, pnl)

### Metrics and reporting

- Per-trade metrics: entry/exit time, price, size, PnL, slippage
- Portfolio metrics: cumulative PnL, annualized return, Sharpe, max drawdown, win_rate, avg_hold_time, turnover
- Per-symbol metrics: fills, slippage, volume usage
- Logging: structured logs to CSV/Parquet for later analysis

### Testing and validation

- Unit tests for:
    - beta estimation (rolling regression)
    - signal generation
    - execution simulation (fills/pricing/slippage)
- Backtest validation:
    - replay small known scenarios to verify deterministic behavior
    - compare vectorized vs event-driven results for sanity check
- Paper trading:
    - run LiveEngine connected to a paper account or broker sandbox; same strategy code used as in backtest