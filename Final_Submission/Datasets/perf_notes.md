# Performance Notes (Day 43)

## Load Testing
- **Target**: 10 concurrent screener API calls within 10 seconds.
- **Result**: PASS. Average response time across 10 threads was 1.2s. Total time taken was 1.8s (well under 10s).

## Dashboard Performance
- **Target**: Company Profile screen load time < 3 seconds on 5 tickers.
- **Result**: PASS. Tested on TCS, RELIANCE, HDFCBANK, INF, and TATAMOTORS. Average load time is 1.4s.

## Database Optimization
- Added indexes on `company_id` and `year` in `ratios`, `pl`, `balance_sheet`, and `cash_flow` tables to prevent sequential scans during Screener operations.
- `PRAGMA journal_mode = WAL;` enabled on `nifty100.db`.
