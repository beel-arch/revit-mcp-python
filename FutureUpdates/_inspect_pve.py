import openpyxl

base = r"C:\Users\frederik.van.nespen\OneDrive - SBA\Documenten\GitHub\revit-mcp-python\Programma voorbeeld\C.1. Outputspecificaties"

p = base + r"\DEEL_1_Systeemfiche\BIJLAGE VI_Programma van Eisen_StLod_StNor_20240502.xlsx"
wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
ws = wb["PvE"]
print("--- PvE rows 12-60, cols A-N")
for i, row in enumerate(ws.iter_rows(min_row=12, max_row=60, max_col=14, values_only=True), start=12):
    cells = [str(c)[:24] if c is not None else "" for c in row]
    if any(cells):
        print(i, cells)
