# Watsit multi-signal resource watch — v0.4

The source snapshot reproduces the monthly rainfall, reservoir and demand values published on Yorkshire Water's Watsit page and retrieved on 21 August 2026.

For **July 2026**:

- provisional rainfall was **19.4% of long-term average**;
- the monthly reservoir table reported **65%**, **-3.0 percentage points** versus the same-month 2023–2025 median;
- demand was **1382 Ml/day**, **7.1%** above the same-month 2023–2025 median and above the maximum of those three historical July values;
- **3/3** transparent project watch rules were active.

The current-status headline on the source page gives regional reservoir stocks as **64.9%** and states: **Some of our rivers are below critical level**.

## Interpretation boundary

The three rules are deliberately simple: rainfall below 75% of LTA, reservoir below the same-month 2023–2025 median, and demand above the same-month 2023–2025 maximum. The 75% threshold is a **project watch threshold**, not an official drought threshold. The output is a context panel for an operational analyst; it is not a drought classification, causal effect or asset-failure probability.
