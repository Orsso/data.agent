ERROR RECOVERY - when a tool call fails:

Read the LAST line of the traceback — it tells you the error type and message.
Then check WHERE the error originated: your code (pandas, python) vs. a library (plotly internals).

- TypeError / ValueError in YOUR code or pandas: the column likely needs cleaning. Check the profile for its format. Strip non-numeric characters before conversion.
- TypeError / ValueError in plotly internals: you passed a wrong parameter to the chart function. Read the error message, fix the function call. Do NOT attempt to clean data as a workaround.
- If the error says figures were "captured" despite the error: do NOT regenerate those figures. They are already saved. Fix only the part that failed and continue.
- If the error mentions "DisplayFormatter" or "IPython display": ignore it — this is a non-actionable internal error. Your figures were captured. Proceed normally.
- KeyError on a column name: use the exact column names from the profile.
- Aggregation fails on object dtype: convert to numeric first with pd.to_numeric(col, errors='coerce').
- "No module named X": that library is not available. Rewrite using only pd, px, go, np, re.
- Chart looks wrong or empty: check for NaN in the data used for x/y/color/size parameters. Use dropna() on the plotting DataFrame.
- NEVER retry with the exact same code. Always fix the root cause first.
