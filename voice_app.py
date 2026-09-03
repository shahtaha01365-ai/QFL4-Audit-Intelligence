pareto_cat = None
if category_col and qty_col:
    pareto_cat = filtered[[category_col, qty_col]].copy()
    pareto_cat[category_col] = pareto_cat[category_col].astype(str).str.strip()
    pareto_cat[qty_col] = pd.to_numeric(pareto_cat[qty_col], errors="coerce").fillna(0)
    pareto_cat = pareto_cat[~pareto_cat[category_col].isin(["", "nan", "None", "NaN"])]
    pareto_cat = pareto_cat.groupby(category_col, as_index=False)[qty_col].sum().sort_values(qty_col, ascending=False).reset_index(drop=True)
    
    # --- Yahan zero quantity walay categories remove kiye gaye hain ---
    pareto_cat = pareto_cat[pareto_cat[qty_col] > 0]
