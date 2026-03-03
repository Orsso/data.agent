Analyze the dataset and generate a comprehensive dashboard.

{source_context}

Write Python code that builds a list called `cards`. Each card is a dict:
- Metric card: {{"type": "metric", "title": "...", "value": ...}}
  `value` should be a string (e.g. "$1,234" or "42.5%"). Format numbers nicely.
- Chart card: {{"type": "chart", "title": "...", "fig": <plotly figure>}}

Guidelines:
- Create 3-5 metric cards summarizing key statistics (counts, averages, sums, etc.).
- Create 3-4 chart cards covering: distribution, correlation, composition, or trends.
- Pick the most insightful columns automatically.
- Use `px` for charts. Set meaningful titles and axis labels.
- Handle missing values with dropna/fillna.