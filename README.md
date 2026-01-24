# LiveBack: Backtesting and Live Trading Framework

## Overview
LiveBack is a Python-based framework designed for seamless backtesting and live trading of financial strategies. It provides a unified API for strategy development, with pluggable runtime engines for both backtesting and live trading modes.

## Features
- Unified Strategy API for both backtesting and live trading
- Support for pair-trading strategies
- Efficient backtesting with vectorized and event-driven options
- Adaptable to various data sources
- Real-time and post-run visualization tools
- Comprehensive metrics and reporting

## Requirements
- Python 3.14
- `uv` package manager

## Development
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd liveback
   ```
2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```
3. Setup pre-commit:
   ```bash
   pre-commit install
   ```
4. Testing:
   ```bash
   uv run -m unittest discover -s src/tests
   ```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for discussion.