# BEEL Excel stijlgids — xlsx exports

Gebruik deze referentie bij elke xlsx-export via openpyxl.
Importeer altijd: `from openpyxl.styles import Font, PatternFill, Alignment, Border, Side`

---

## Kleurenpalet (hex zonder #)

| Naam             | Hex      | Gebruik                                      |
|------------------|----------|----------------------------------------------|
| Blauw primair    | `156082` | Hoofdheader achtergrond, titelbalk           |
| Blauw licht      | `DDEAF3` | Subheader, sectietitels, positie-headers     |
| Blauw mid        | `B5D4F4` | Afwisselende rijen (even), lichte accenten   |
| Oranje primair   | `E97132` | Waarschuwing, gewijzigde waarden             |
| Oranje licht     | `FDF0E8` | Achtergrond waarschuwingsrijen               |
| Groen ok         | `1A7F4E` | Conforme waarden, ok-tekst                   |
| Groen licht      | `E6F4ED` | Achtergrond conforme cellen                  |
| Rood nok         | `C0392B` | Niet-conforme waarden                        |
| Rood licht       | `FDF0EF` | Achtergrond niet-conforme cellen             |
| Grijs achter     | `F5F5F5` | Afwisselende rijen (oneven), metadata        |
| Grijs rand       | `D0D0D0` | Celranden                                    |
| Wit              | `FFFFFF` | Standaard celachtergrond                     |
| Tekst donker     | `1A1A1A` | Standaard tekstkleur (via Font color)        |
| Tekst grijs      | `666666` | Secundaire tekst, labels                     |
| Tekst wit        | `FFFFFF` | Tekst op donkere headers                     |

---

## Lettertypen

| Element              | Font     | Grootte | Vet   | Kleur    |
|----------------------|----------|---------|-------|----------|
| Hoofdtitel (rij 1)   | Calibri  | 14      | Ja    | `156082` |
| Kolomheader          | Calibri  | 10      | Ja    | `FFFFFF` |
| Subheader / sectie   | Calibri  | 10      | Ja    | `156082` |
| Datarijen            | Calibri  | 10      | Nee   | `1A1A1A` |
| Niet-conform cel     | Calibri  | 10      | Ja    | `C0392B` |
| Conform cel          | Calibri  | 10      | Nee   | `1A7F4E` |
| n.v.t. cel           | Calibri  | 10      | Nee   | `999999` |
| Footer / metadata    | Calibri  | 9       | Nee   | `666666` |

---

## Rijen & kolommen

```python
# Hoofdtitel — rij 1, merged over alle kolommen
ws.merge_cells(f'A1:{last_col}1')
ws['A1'] = "Titel van het rapport"
ws['A1'].font = Font(name='Arial', size=14, bold=True, color='156082')
ws['A1'].alignment = Alignment(horizontal='left', vertical='center')
ws.row_dimensions[1].height = 24

# Kolomheaders — rij 2
for col, header in enumerate(headers, start=1):
    cell = ws.cell(row=2, column=col, value=header)
    cell.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    cell.fill = PatternFill('solid', fgColor='156082')
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.border = thin_border
ws.row_dimensions[2].height = 18

# Datarijen — afwisselend wit / lichtblauw
fill_odd  = PatternFill('solid', fgColor='FFFFFF')
fill_even = PatternFill('solid', fgColor='DDEAF3')
for i, row in enumerate(data_rows):
    fill = fill_even if i % 2 == 0 else fill_odd
    ...

# Sectieheader (per gebouw / per positie)
cell.font = Font(name='Arial', size=10, bold=True, color='156082')
cell.fill = PatternFill('solid', fgColor='DDEAF3')
```

---

## Celstijlen — snelreferentie

```python
thin_border = Border(
    left=Side(style='thin', color='D0D0D0'),
    right=Side(style='thin', color='D0D0D0'),
    top=Side(style='thin', color='D0D0D0'),
    bottom=Side(style='thin', color='D0D0D0')
)

# Niet-conform
cell.font = Font(name='Calibri', size=10, bold=True, color='C0392B')
cell.fill = PatternFill('solid', fgColor='FDF0EF')

# Conform (optioneel subtiel groen)
cell.font = Font(name='Calibri', size=10, color='1A7F4E')

# Gewijzigd / waarschuwing
cell.font = Font(name='Calibri', size=10, bold=True, color='E97132')
cell.fill = PatternFill('solid', fgColor='FDF0E8')

# n.v.t.
cell.font = Font(name='Calibri', size=10, italic=True, color='999999')
```

---

## Kolombreedtes (richtlijnen)

| Kolomtype              | Breedte (karakters) |
|------------------------|---------------------|
| Ruimtenaam / label     | 22–28               |
| Oppervlakte (m²)       | 10–12               |
| Min. norm              | 10                  |
| Verschil (Δ)           | 10                  |
| Status / identiek      | 14                  |
| Appartementnummer      | 22                  |
| Type (bv. 2/3)         | 8                   |

```python
ws.column_dimensions['A'].width = 26
ws.column_dimensions['B'].width = 11
# etc.
```

---

## Bestandsnaamconventie

```
BEEL_{ProjectNr}_{Onderwerp}_{JJJJMMDD}.xlsx
```
Voorbeeld: `BEEL_KSS_Conformiteitscheck_2C_20260603.xlsx`

---

## Footer (laatste rij)

Voeg altijd een lege rij toe, dan een footercel:
```python
footer_row = ws.max_row + 2
ws.cell(row=footer_row, column=1, value=f"Gegenereerd door BEEL Architecten — {datum}")
ws.cell(row=footer_row, column=1).font = Font(name='Arial', size=9, color='666666', italic=True)
```
