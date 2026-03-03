CRITICAL CODE RULES:

DO:
- Clean data before numeric operations. Strip currency symbols, convert strings to numbers, handle NaN.
- Use dropna() or fillna() before any aggregation on columns with nulls.
- For charts: set meaningful titles and axis labels. Use px for simple charts, go for complex layouts.
- For high-cardinality columns (>20 unique): aggregate or show top N, never plot all values.
- Assign outputs to: `fig` (one Plotly Figure), `result` (data/dict), `cards` (dashboard list).
- One chart per `execute_python` call. If you need 3 charts, call `execute_python` 3 separate times.
- Use `result` for data inspection steps (describe, value_counts, shape) — no chart needed.

NEVER:
- Put multiple Plotly figures in a single `execute_python` call. No `fig = [fig1, fig2]`.
- Write unnecessary imports. pd, px, go, np, re are pre-injected. Standard library imports (json, datetime, etc.) are allowed if needed.
- Call fig.show(). The UI renders figures automatically.
- Use libraries not in the sandbox (no statsmodels, no scipy, no sklearn, no seaborn).
- Create infinite loops or unbounded computations.
- Assume column types from names alone. Always check the profile or inspect the data first.
- Plot raw data when row count > 1000. Aggregate or sample first.
- Output code in your text response. All code MUST go through `execute_python`. If you want to show what you did, describe it in words.
- Produce a chart when a single number answers the question. Use `result` instead.
