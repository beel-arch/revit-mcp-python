# WO Area Comparison — Revit vs Simulatietabel
**Date:** 2026-04-15  
**Revit model:** KSS-BEEL-AR-Y-MO-ARG-0003-Fase1  
**Excel:** simulatietabel.xlsx — Sheet: `Table002 (Page 1-4)`  
**Area Scheme:** WO | **Scope:** Buildings 1.A + 1.B + 2.C

> **Note:** Revit labels floors 0–3 of building 1 as `1.A`, while Excel splits them into `1.A` (units 1–7) and `1.B` (units 7–14). Similarly, Revit labels building 2 as `2.C`, while Excel splits into `2.C` (units 1–4) and `2.D` (units 5–8). Matching is done on building number + floor + unit number.

---

## Summary

| | Count |
|---|---|
| Revit areas (1.A + 1.B + 2.C) | 80 |
| Excel entries (1.A + 1.B + 2.C + 2.D) | 80 |
| **OK** | **75** |
| **Type mismatch** | **1** |
| **Area diff > 0.5 m²** | **4** |
| No Excel match | 0 |
| No Revit match | 0 |

---

## Issues — Action Required

### Type Mismatch (1)

| Revit Nr | Excel Nr | Revit Type | Excel Type | Revit m² | Excel m² | Diff |
|---|---|---|---|---|---|---|
| `1.A.Niv 0.12` | `1.B.Niv 0.12` | `2/3` | `3/5` | 103.08 | 104.29 | −1.21 |

> Both type AND area differ. Check whether this unit is 2/3 or 3/5 and update Revit area name accordingly. Area also needs to grow by ~1.2 m².

### Area Differences > 0.5 m² (4)

| Revit Nr | Excel Nr | Type | Revit m² | Excel m² | Diff |
|---|---|---|---|---|---|
| `2.C.Niv 1.04` | `2.C.Niv 1.4` | 4/5 | 114.46 | 115.01 | −0.55 |
| `2.C.Niv 2.04` | `2.C.Niv 2.4` | 4/5 | 114.46 | 115.02 | −0.56 |
| `2.C.Niv 3.01` | `2.C.Niv 3.1` | 2/3 | 77.52 | 76.89 | +0.63 |
| `2.C.Niv 3.04` | `2.C.Niv 3.4` | 4/5 | 114.46 | 115.06 | −0.60 |

> The `4/5` units in 2.C are consistently ~0.55 m² too small across all floors — likely a wall or boundary adjustment needed. Unit 3.01 is 0.63 m² too large.

---

## Full Comparison Table

| Revit Nr | Excel Nr | Type | Revit m² | Excel m² | Diff | Status |
|---|---|---|---|---|---|---|
| 1.A.Niv 0.01 | 1.A.Niv 0.1 | 3/4 | 89.85 | 89.81 | +0.04 | OK |
| 1.A.Niv 0.02 | 1.A.Niv 0.2 | 2/3 | 85.30 | 85.30 | 0.00 | OK |
| 1.A.Niv 0.03 | 1.A.Niv 0.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 0.04 | 1.A.Niv 0.4 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 0.05 | 1.A.Niv 0.5 | 1/2 | 57.59 | 57.58 | +0.01 | OK |
| 1.A.Niv 0.06 | 1.A.Niv 0.6 | 1/2 | 67.07 | 67.15 | −0.08 | OK |
| 1.A.Niv 0.07 | 1.B.Niv 0.7 | 1/2 | 57.77 | 57.88 | −0.11 | OK |
| 1.A.Niv 0.08 | 1.B.Niv 0.8 | 1/2 | 57.59 | 57.58 | +0.01 | OK |
| 1.A.Niv 0.09 | 1.B.Niv 0.9 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 0.10 | 1.B.Niv 0.10 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 0.11 | 1.B.Niv 0.11 | 2/3 | 77.04 | 77.03 | +0.01 | OK |
| **1.A.Niv 0.12** | **1.B.Niv 0.12** | **2/3 ≠ 3/5** | **103.08** | **104.29** | **−1.21** | **TYPE MISMATCH** |
| 1.A.Niv 1.01 | 1.A.Niv 1.1 | 3/5 | 97.65 | 97.62 | +0.03 | OK |
| 1.A.Niv 1.02 | 1.A.Niv 1.2 | 2/3 | 85.30 | 85.28 | +0.02 | OK |
| 1.A.Niv 1.03 | 1.A.Niv 1.3 | 2/3 | 73.49 | 73.46 | +0.03 | OK |
| 1.A.Niv 1.04 | 1.A.Niv 1.4 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 1.05 | 1.A.Niv 1.5 | 1/2 | 57.59 | 57.58 | +0.01 | OK |
| 1.A.Niv 1.06 | 1.A.Niv 1.6 | 1/2 | 57.93 | 57.92 | +0.01 | OK |
| 1.A.Niv 1.07 | 1.A.Niv 1.7 | 1/2 | 54.96 | 55.13 | −0.17 | OK |
| 1.A.Niv 1.08 | 1.B.Niv 1.8 | 1/2 | 54.96 | 55.13 | −0.17 | OK |
| 1.A.Niv 1.09 | 1.B.Niv 1.9 | 1/2 | 57.77 | 57.92 | −0.15 | OK |
| 1.A.Niv 1.10 | 1.B.Niv 1.10 | 1/2 | 57.59 | 57.58 | +0.01 | OK |
| 1.A.Niv 1.11 | 1.B.Niv 1.11 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 1.12 | 1.B.Niv 1.12 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 1.13 | 1.B.Niv 1.13 | 2/3 | 77.04 | 76.97 | +0.07 | OK |
| 1.A.Niv 1.14 | 1.B.Niv 1.14 | 3/5 | 111.01 | 110.95 | +0.06 | OK |
| 1.A.Niv 2.01 | 1.A.Niv 2.1 | 3/5 | 102.47 | 102.52 | −0.05 | OK |
| 1.A.Niv 2.02 | 1.A.Niv 2.2 | 2/3 | 85.30 | 85.37 | −0.07 | OK |
| 1.A.Niv 2.03 | 1.A.Niv 2.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 2.04 | 1.A.Niv 2.4 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 2.05 | 1.A.Niv 2.5 | 3/5 | 103.26 | 103.24 | +0.02 | OK |
| 1.A.Niv 2.06 | 1.A.Niv 2.6 | 2/3 | 72.30 | 72.24 | +0.06 | OK |
| 1.A.Niv 2.07 | 1.A.Niv 2.7 | 1/2 | 54.96 | 55.15 | −0.19 | OK |
| 1.A.Niv 2.08 | 1.B.Niv 2.8 | 2/3 | 78.55 | 78.96 | −0.41 | OK |
| 1.A.Niv 2.09 | 1.B.Niv 2.9 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 2.10 | 1.B.Niv 2.10 | 2/3 | 77.04 | 77.05 | −0.01 | OK |
| 1.A.Niv 2.11 | 1.B.Niv 2.11 | 3/5 | 115.83 | 115.79 | +0.04 | OK |
| 1.A.Niv 3.01 | 1.A.Niv 3.1 | 3/5 | 102.47 | 102.45 | +0.02 | OK |
| 1.A.Niv 3.02 | 1.A.Niv 3.2 | 2/3 | 85.30 | 85.32 | −0.02 | OK |
| 1.A.Niv 3.03 | 1.A.Niv 3.3 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 3.04 | 1.A.Niv 3.4 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 3.05 | 1.A.Niv 3.5 | 3/5 | 103.26 | 103.24 | +0.02 | OK |
| 1.A.Niv 3.06 | 1.A.Niv 3.6 | 2/3 | 72.30 | 71.88 | +0.42 | OK |
| 1.A.Niv 3.07 | 1.A.Niv 3.7 | 1/2 | 54.96 | 54.96 | 0.00 | OK |
| 1.A.Niv 3.08 | 1.B.Niv 3.8 | 2/3 | 78.55 | 78.96 | −0.41 | OK |
| 1.A.Niv 3.09 | 1.B.Niv 3.9 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.A.Niv 3.10 | 1.B.Niv 3.10 | 2/3 | 77.04 | 76.97 | +0.07 | OK |
| 1.A.Niv 3.11 | 1.B.Niv 3.11 | 3/5 | 115.83 | 115.79 | +0.04 | OK |
| 1.B.Niv 4.01 | 1.B.Niv 4.1 | 2/3 | 78.55 | 78.96 | −0.41 | OK |
| 1.B.Niv 4.02 | 1.B.Niv 4.2 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.B.Niv 4.03 | 1.B.Niv 4.3 | 2/3 | 77.04 | 77.05 | −0.01 | OK |
| 1.B.Niv 4.04 | 1.B.Niv 4.4 | 3/5 | 115.83 | 115.79 | +0.04 | OK |
| 1.B.Niv 5.01 | 1.B.Niv 5.1 | 2/3 | 78.55 | 78.96 | −0.41 | OK |
| 1.B.Niv 5.02 | 1.B.Niv 5.2 | 1/2 | 54.68 | 54.66 | +0.02 | OK |
| 1.B.Niv 5.03 | 1.B.Niv 5.3 | 2/3 | 77.04 | 77.04 | 0.00 | OK |
| 1.B.Niv 5.04 | 1.B.Niv 5.4 | 3/5 | 115.83 | 115.79 | +0.04 | OK |
| 2.C.Niv 1.01 | 2.C.Niv 1.1 | 2/3 | 77.52 | 77.14 | +0.38 | OK |
| 2.C.Niv 1.02 | 2.C.Niv 1.2 | 1/2 | 55.19 | 55.50 | −0.31 | OK |
| 2.C.Niv 1.03 | 2.C.Niv 1.3 | 3/4 | 92.48 | 92.45 | +0.03 | OK |
| **2.C.Niv 1.04** | **2.C.Niv 1.4** | **4/5** | **114.46** | **115.01** | **−0.55** | **AREA DIFF** |
| 2.C.Niv 1.05 | 2.D.Niv 1.5 | 3/4 | 90.17 | 89.98 | +0.19 | OK |
| 2.C.Niv 1.06 | 2.D.Niv 1.6 | 3/5 | 105.07 | 105.42 | −0.35 | OK |
| 2.C.Niv 1.07 | 2.D.Niv 1.7 | 2/3 | 72.17 | 72.26 | −0.09 | OK |
| 2.C.Niv 1.08 | 2.D.Niv 1.8 | 2/3 | 77.52 | 77.52 | 0.00 | OK |
| 2.C.Niv 2.01 | 2.C.Niv 2.1 | 2/3 | 77.52 | 77.52 | 0.00 | OK |
| 2.C.Niv 2.02 | 2.C.Niv 2.2 | 1/2 | 55.19 | 55.11 | +0.08 | OK |
| 2.C.Niv 2.03 | 2.C.Niv 2.3 | 3/4 | 92.48 | 92.50 | −0.02 | OK |
| **2.C.Niv 2.04** | **2.C.Niv 2.4** | **4/5** | **114.46** | **115.02** | **−0.56** | **AREA DIFF** |
| 2.C.Niv 2.05 | 2.D.Niv 2.5 | 3/4 | 90.17 | 90.13 | +0.04 | OK |
| 2.C.Niv 2.06 | 2.D.Niv 2.6 | 3/5 | 105.07 | 104.62 | +0.45 | OK |
| 2.C.Niv 2.07 | 2.D.Niv 2.7 | 2/3 | 72.17 | 72.19 | −0.02 | OK |
| 2.C.Niv 2.08 | 2.D.Niv 2.8 | 2/3 | 77.52 | 77.52 | 0.00 | OK |
| **2.C.Niv 3.01** | **2.C.Niv 3.1** | **2/3** | **77.52** | **76.89** | **+0.63** | **AREA DIFF** |
| 2.C.Niv 3.02 | 2.C.Niv 3.2 | 1/2 | 55.19 | 55.31 | −0.12 | OK |
| 2.C.Niv 3.03 | 2.C.Niv 3.3 | 3/4 | 92.48 | 92.55 | −0.07 | OK |
| **2.C.Niv 3.04** | **2.C.Niv 3.4** | **4/5** | **114.46** | **115.06** | **−0.60** | **AREA DIFF** |
| 2.C.Niv 3.05 | 2.D.Niv 3.5 | 3/4 | 90.17 | 90.11 | +0.06 | OK |
| 2.C.Niv 3.06 | 2.D.Niv 3.6 | 3/5 | 105.07 | 105.20 | −0.13 | OK |
| 2.C.Niv 3.07 | 2.D.Niv 3.7 | 2/3 | 72.17 | 72.26 | −0.09 | OK |
| 2.C.Niv 3.08 | 2.D.Niv 3.8 | 2/3 | 77.52 | 77.52 | 0.00 | OK |

---

*Generated by Claude Code / revit-mcp-python*
