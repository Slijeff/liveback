from src.data.data_client import YFinanceDataClient
import pandas as pd
def main():
    dc = YFinanceDataClient(["AAPL", "NVDA"], pd.to_datetime("2025-12-01"), pd.to_datetime("2026-01-01"))
    for event in dc.stream():
        print(event)


if __name__ == "__main__":
    main()
