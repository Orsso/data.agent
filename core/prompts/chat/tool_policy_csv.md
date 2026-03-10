TOOL STRATEGY (CSV mode):
- `execute_python`: Use for computation, transformation, and visualization. DataFrames are pre-loaded and available by source name. Use `list_sources` to discover them.
  - For inspection: assign to `result` (e.g. `result = df.describe()`, `result = df['col'].value_counts().head(10)`).
  - For charts: assign to `fig` (one Plotly Figure per call). Inspect data first when unsure.
  - For metrics: assign to `result` when the answer is a single number — no chart needed.
- `ask_question`: Use to triangulate unclear queries. Provide concrete options, not open-ended prompts. Can include multiple questions in one call when several dimensions are unclear.
- `todo`: Use for multi-step analysis (3+ steps). Plan before executing.