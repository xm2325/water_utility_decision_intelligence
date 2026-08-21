# Yorkshire Water ODI / Regulatory Decision Product — v0.4 results

## Data actually used

The analysis ran on Yorkshire Water official APR Open Data CSV files for 2023/24, 2024/25 and 2025/26. The latest file contains **121,937 rows**.

## 2025/26 common performance-commitment portfolio

The parser found **36** common 3A rows, including **18** with a numeric outperformance/underperformance payment. Across all common 3A rows, **12** were explicitly reported as not meeting their PCL; **11** of those PCL misses also had a numeric payment in this extract.

Gross observed negative-payment exposure across the parsed common 3A measures is **£76.75m**. Positive payments across those measures total **£15.86m**, giving a net parsed payment of **£-60.89m**. This is a deliberately narrow extract of common 3A measures and must not be presented as Yorkshire Water's total company ODI position.

The three largest observed negative-payment workstreams are:

1. **Serious pollution incidents** — £18.68m
2. **Total pollution incidents** — £18.34m
3. **Internal sewer flooding** — £14.28m

Together these account for **66.8%** of observed negative-payment exposure in the extracted portfolio. This is useful for triage under limited team capacity, but it is **not** an estimate that these payments are avoidable.

## Storm-overflow reporting signal

The same APR line, `Number of spills from storm overflows (from 1 January to 31 December)`, is present in all three files. Reported values are:

| year    |   spills |
|:--------|---------:|
| 2023-24 |    77761 |
| 2024-25 |    68164 |
| 2025-26 |    51560 |

The first-to-latest change is **-33.7%**. This is a descriptive reporting trend only; the project does not infer causality from it.

## Next real-data layer

The repository includes an ArcGIS FeatureServer downloader and a temporal night-flow ML backtest. Yorkshire Water's 2026 night-flow layer exposes `DATE`, `DMA_ID`, `ACTUAL_MIN_NIGHT_FLOW`, `MIN_NIGHT_FLOW` and coordinates. The model forecasts each dated minimum-night-flow observation from strictly prior DMA history and ranks upper-band exceedances for investigation. Such residuals are an operational signal, **not a confirmed leak label**.
