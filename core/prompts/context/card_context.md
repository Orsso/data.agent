CARD MODIFICATION MODE — The user has selected existing dashboard card(s) to edit:

{card_details}

MANDATORY — To update these cards, use the `card_updates` output slot:
```python
card_updates = {{"<card_id>": new_fig}}
```
Where `<card_id>` is the exact ID shown above and `new_fig` is the new Plotly figure.

WRONG (creates a new standalone chart, ignores the user's edit request):
```python
fig = px.bar(...)
```

CORRECT (proposes an edit to the existing dashboard card):
```python
new_fig = px.bar(...)
card_updates = {{"abc123": new_fig}}
```

CRITICAL: Do NOT assign to `fig` when modifying cards. `fig` is ONLY for creating new standalone charts. If you use `fig` here, the card will NOT be updated.
