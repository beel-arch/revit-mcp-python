# WO Area Comparison — Revit vs Simulatietabel
**Date:** 2026-04-15
**Revit model:** KSS-BEEL-AR-Y-MO-ARG-0004-Fase2
**Excel:** simulatietabel.xlsx — Sheet: `Table002 (Page 1-4)`
**Area Scheme:** WO | **Scope:** Buildings 3.E + 3.F + 4.G + 4.H

> **Note:** Revit labels floors 0–3 of building 3 all as `3.E`, while Excel splits into `3.E` (units 1–6) and `3.F` (units 7–11). Matching is done on building number + floor + unit number.

---

## Summary

| | Count |
|---|---|
| Revit areas (valid) | 78 |
| Excel entries (3.E + 3.F + 4.G + 4.H) | 81 |
| **OK** | **72** |
| **Type mismatch** | **1** |
| **Area diff > 0.5 m²** | **5** |
| No Excel match | 0 |
| No Revit match | 3 |

---

## Revit Issues — Fix in Model First

### Duplicate Area Numbers (3)

Three areas on level 130 have been given level-2 numbers. They need to be renumbered to `3.xx`:

| Current Number | Level | Type | Area | Should be |
|---|---|---|---|---|
| `3.E.Niv 2.02` | 130 | 2/3 | 75.00 m² | `3.E.Niv 3.02` |
| `3.E.Niv 2.04` | 130 | 1/2 | 54.56 m² | `3.E.Niv 3.04` |
| `3.E.Niv 2.06` | 130 | 2/3 | 72.15 m² | `3.E.Niv 3.06` |

> Once renumbered, these will also resolve the 3 "No Revit match" entries for `3.E.Niv 3.2`, `3.E.Niv 3.4`, `3.E.Niv 3.6`.

### Unnamed Area (1)

| Nr | Level | Area | Issue |
|---|---|---|---|
| `4.G.Niv 0.5` | 102 | 275.28 m² | No area name set — likely a common/non-residential area, not in Excel |

---

## Comparison Issues — Action Required

### Type Mismatch (1)

| Revit Nr | Excel Nr | Revit Type | Excel Type | Revit m² | Excel m² | Diff |
|---|---|---|---|---|---|---|
| `3.F.Niv 4.02` | `3.F.Niv 4.2` | `5/7` | `4/7` | 129.50 | 129.49 | +0.01 |

> Area matches perfectly — only the bedroom count differs. Check whether this is a 4/7 or 5/7 unit and update accordingly.

### Area Differences > 0.5 m² (5)

| Revit Nr | Excel Nr | Type | Revit m² | Excel m² | Diff |
|---|---|---|---|---|---|
| `3.E.Niv 0.06` | `3.E.Niv 0.6` | 2/3 | 73.40 | 75.89 | −2.49 |
| `3.E.Niv 2.01` | `3.E.Niv 2.1` | 3/5 | 100.33 | 105.19 | −4.86 |
| `3.F.Niv 2.11` | `3.F.Niv 2.11` | 3/5 | 98.74 | 103.52 | −4.78 |
| `3.E.Niv 3.01` | `3.E.Niv 3.1` | 3/5 | 100.33 | 105.12 | −4.79 |
| `3.F.Niv 3.11` | `3.F.Niv 3.11` | 3/5 | 98.74 | 103.52 | −4.78 |

> The `3/5` penthouse/corner units in 3.E and 3.F are consistently ~4.8 m² too small on floors 2 and 3. The `3.E.Niv 0.06` is also 2.49 m² short. These likely need boundary adjustments.

---

## Excel Entries NOT in Revit (3)

These will be resolved once the duplicate numbers above are corrected:

| Nr | Type | Excel m² | Fix |
|---|---|---|---|
| `3.E.Niv 3.2` | 2/3 | 75.03 | Renumber `3.E.Niv 2.02 (L130)` → `3.E.Niv 3.02` |
| `3.E.Niv 3.4` | 1/2 | 54.66 | Renumber `3.E.Niv 2.04 (L130)` → `3.E.Niv 3.04` |
| `3.E.Niv 3.6` | 2/3 | 72.27 | Renumber `3.E.Niv 2.06 (L130)` → `3.E.Niv 3.06` |

---

## Full Comparison Table

| Revit Nr | Excel Nr | Type | Revit m² | Excel m² | Diff | Status |
|---|---|---|---|---|---|---|
| 3.E.Niv 0.01 | 3.E.Niv 0.1 | 3/4 | 92.40 | 92.50 | −0.10 | OK |
| 3.E.Niv 0.02 | 3.E.Niv 0.2 | 2/3 | 75.00 | 75.01 | −0.01 | OK |
| 3.E.Niv 0.03 | 3.E.Niv 0.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.E.Niv 0.04 | 3.E.Niv 0.4 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.E.Niv 0.05 | 3.E.Niv 0.5 | 1/2 | 64.31 | 64.33 | −0.02 | OK |
| **3.E.Niv 0.06** | **3.E.Niv 0.6** | **2/3** | **73.40** | **75.89** | **−2.49** | **AREA DIFF** |
| 3.E.Niv 0.07 | 3.F.Niv 0.7 | 1/2 | 68.55 | 68.68 | −0.13 | OK |
| 3.E.Niv 0.08 | 3.F.Niv 0.8 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.E.Niv 0.09 | 3.F.Niv 0.9 | 2/3 | 69.85 | 69.87 | −0.02 | OK |
| 3.E.Niv 0.10 | 3.F.Niv 0.10 | 3/4 | 90.81 | 90.90 | −0.09 | OK |
| 3.E.Niv 1.01 | 3.E.Niv 1.1 | 3/5 | 100.33 | 100.31 | +0.02 | OK |
| 3.E.Niv 1.02 | 3.E.Niv 1.2 | 2/3 | 75.00 | 75.00 | 0.00 | OK |
| 3.E.Niv 1.03 | 3.E.Niv 1.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.E.Niv 1.04 | 3.E.Niv 1.4 | 1/2 | 54.56 | 54.90 | −0.34 | OK |
| 3.E.Niv 1.05 | 3.E.Niv 1.5 | 1/2 | 60.34 | 60.34 | 0.00 | OK |
| 3.E.Niv 1.06 | 3.E.Niv 1.6 | 2/3 | 72.15 | 72.28 | −0.13 | OK |
| 3.F.Niv 1.07 | 3.F.Niv 1.7 | 2/3 | 81.05 | 81.19 | −0.14 | OK |
| 3.F.Niv 1.08 | 3.F.Niv 1.8 | 1/2 | 54.68 | 54.84 | −0.16 | OK |
| 3.F.Niv 1.09 | 3.F.Niv 1.9 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.F.Niv 1.10 | 3.F.Niv 1.10 | 2/4 | 88.65 | 88.67 | −0.02 | OK |
| 3.F.Niv 1.11 | 3.F.Niv 1.11 | 3/5 | 98.74 | 98.71 | +0.03 | OK |
| 3.E.Niv 2.01 | 3.E.Niv 2.1 | 3/5 | 100.33 | 105.19 | −4.86 | **AREA DIFF** |
| 3.E.Niv 2.02 | 3.E.Niv 2.2 | 2/3 | 75.00 | 75.02 | −0.02 | OK |
| 3.E.Niv 2.03 | 3.E.Niv 2.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.E.Niv 2.04 | 3.E.Niv 2.4 | 1/2 | 54.56 | 54.66 | −0.10 | OK |
| 3.E.Niv 2.05 | 3.E.Niv 2.5 | 1/2 | 60.34 | 60.34 | 0.00 | OK |
| 3.E.Niv 2.06 | 3.E.Niv 2.6 | 2/3 | 72.15 | 72.27 | −0.12 | OK |
| 3.F.Niv 2.07 | 3.F.Niv 2.7 | 2/3 | 81.05 | 81.20 | −0.15 | OK |
| 3.F.Niv 2.08 | 3.F.Niv 2.8 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.F.Niv 2.09 | 3.F.Niv 2.9 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.F.Niv 2.10 | 3.F.Niv 2.10 | 2/4 | 88.65 | 88.61 | +0.04 | OK |
| **3.F.Niv 2.11** | **3.F.Niv 2.11** | **3/5** | **98.74** | **103.52** | **−4.78** | **AREA DIFF** |
| 3.E.Niv 3.01 | 3.E.Niv 3.1 | 3/5 | 100.33 | 105.12 | −4.79 | **AREA DIFF** |
| 3.E.Niv 3.03 | 3.E.Niv 3.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.E.Niv 3.05 | 3.E.Niv 3.5 | 1/2 | 60.34 | 60.34 | 0.00 | OK |
| 3.F.Niv 3.07 | 3.F.Niv 3.7 | 2/3 | 81.05 | 81.19 | −0.14 | OK |
| 3.F.Niv 3.08 | 3.F.Niv 3.8 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.F.Niv 3.09 | 3.F.Niv 3.9 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 3.F.Niv 3.10 | 3.F.Niv 3.10 | 2/4 | 88.65 | 88.61 | +0.04 | OK |
| **3.F.Niv 3.11** | **3.F.Niv 3.11** | **3/5** | **98.74** | **103.52** | **−4.78** | **AREA DIFF** |
| **3.F.Niv 4.02** | **3.F.Niv 4.2** | **5/7 ≠ 4/7** | **129.50** | **129.49** | **+0.01** | **TYPE MISMATCH** |
| 3.F.Niv 4.01 | 3.F.Niv 4.1 | 2/3 | 72.15 | 72.27 | −0.12 | OK |
| 3.F.Niv 4.03 | 3.F.Niv 4.3 | 3/4 | 92.29 | 92.24 | +0.05 | OK |
| 3.F.Niv 4.04 | 3.F.Niv 4.4 | 2/4 | 88.65 | 88.61 | +0.04 | OK |
| 3.F.Niv 4.05 | 3.F.Niv 4.5 | 3/5 | 103.56 | 103.45 | +0.11 | OK |
| 3.F.Niv 5.01 | 3.F.Niv 5.1 | 2/3 | 72.15 | 72.27 | −0.12 | OK |
| 3.F.Niv 5.02 | 3.F.Niv 5.2 | 5/7 | 129.50 | 129.50 | 0.00 | OK |
| 3.F.Niv 5.03 | 3.F.Niv 5.3 | 3/4 | 92.29 | 92.30 | −0.01 | OK |
| 3.F.Niv 5.04 | 3.F.Niv 5.4 | 2/4 | 88.65 | 88.62 | +0.03 | OK |
| 3.F.Niv 5.05 | 3.F.Niv 5.5 | 3/5 | 103.56 | 103.52 | +0.04 | OK |
| 4.G.Niv 0.1 | 4.G.Niv 0.1 | 4/6 | 123.39 | 123.47 | −0.08 | OK |
| 4.G.Niv 0.2 | 4.G.Niv 0.2 | 5/6 | 125.13 | 125.11 | +0.02 | OK |
| 4.G.Niv 0.3 | 4.G.Niv 0.3 | 2/3 | 73.49 | 73.46 | +0.03 | OK |
| 4.G.Niv 0.4 | 4.G.Niv 0.4 | 2/3 | 73.49 | 73.46 | +0.03 | OK |
| 4.G.Niv 1.01 | 4.G.Niv 1.1 | 5/6 | 131.32 | 131.28 | +0.04 | OK |
| 4.G.Niv 1.02 | 4.G.Niv 1.2 | 3/5 | 104.51 | 104.49 | +0.02 | OK |
| 4.G.Niv 1.03 | 4.G.Niv 1.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 4.G.Niv 1.04 | 4.G.Niv 1.4 | 3/5 | 111.05 | 111.29 | −0.24 | OK |
| 4.H.Niv 1.05 | 4.H.Niv 1.5 | 3/5 | 111.05 | 111.29 | −0.24 | OK |
| 4.H.Niv 1.06 | 4.H.Niv 1.6 | 2/3 | 73.49 | 73.46 | +0.03 | OK |
| 4.H.Niv 1.07 | 4.H.Niv 1.7 | 2/3 | 84.07 | 84.15 | −0.08 | OK |
| 4.H.Niv 1.08 | 4.H.Niv 1.8 | 5/6 | 138.77 | 138.71 | +0.06 | OK |
| 4.G.Niv 2.01 | 4.G.Niv 2.1 | 5/6 | 136.13 | 136.09 | +0.04 | OK |
| 4.G.Niv 2.02 | 4.G.Niv 2.2 | 3/5 | 104.51 | 104.49 | +0.02 | OK |
| 4.G.Niv 2.03 | 4.G.Niv 2.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 4.G.Niv 2.04 | 4.G.Niv 2.4 | 3/5 | 111.05 | 111.29 | −0.24 | OK |
| 4.H.Niv 2.05 | 4.H.Niv 2.5 | 3/5 | 111.05 | 111.27 | −0.22 | OK |
| 4.H.Niv 2.06 | 4.H.Niv 2.6 | 2/3 | 73.49 | 73.46 | +0.03 | OK |
| 4.H.Niv 2.07 | 4.H.Niv 2.7 | 2/3 | 84.07 | 84.02 | +0.05 | OK |
| 4.H.Niv 2.08 | 4.H.Niv 2.8 | 5/6 | 143.46 | 143.04 | +0.42 | OK |
| 4.G.Niv 3.01 | 4.G.Niv 3.1 | 5/6 | 136.13 | 136.09 | +0.04 | OK |
| 4.G.Niv 3.02 | 4.G.Niv 3.2 | 3/5 | 104.51 | 104.49 | +0.02 | OK |
| 4.G.Niv 3.03 | 4.G.Niv 3.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 4.G.Niv 3.04 | 4.H.Niv 3.4 | 3/5 | 111.05 | 111.29 | −0.24 | OK |
| 4.H.Niv 3.05 | 4.H.Niv 3.5 | 3/5 | 111.05 | 111.27 | −0.22 | OK |
| 4.H.Niv 3.06 | 4.H.Niv 3.6 | 2/3 | 73.49 | 73.46 | +0.03 | OK |
| 4.H.Niv 3.07 | 4.H.Niv 3.7 | 2/3 | 84.07 | 84.04 | +0.03 | OK |
| 4.H.Niv 3.08 | 4.H.Niv 3.8 | 5/6 | 143.46 | 143.47 | −0.01 | OK |

---

*Generated by Claude Code / revit-mcp-python*
