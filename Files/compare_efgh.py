import openpyxl, re

revit_raw = [
    ('3.E.Niv 0.01','3/4',92.40,'102'),('3.E.Niv 0.02','2/3',75.00,'102'),
    ('3.E.Niv 0.03','1/2',54.68,'102'),('3.E.Niv 0.04','1/2',54.68,'102'),
    ('3.E.Niv 0.05','1/2',64.31,'102'),('3.E.Niv 0.06','2/3',73.40,'102'),
    ('3.E.Niv 0.07','1/2',68.55,'102'),('3.E.Niv 0.08','1/2',54.68,'102'),
    ('3.E.Niv 0.09','2/3',69.85,'102'),('3.E.Niv 0.10','3/4',90.81,'102'),
    ('3.E.Niv 1.01','3/5',100.33,'110'),('3.E.Niv 1.02','2/3',75.00,'110'),
    ('3.E.Niv 1.03','1/2',54.68,'110'),('3.E.Niv 1.04','1/2',54.56,'110'),
    ('3.E.Niv 1.05','1/2',60.34,'110'),('3.E.Niv 1.06','2/3',72.15,'110'),
    ('3.E.Niv 2.01','3/5',105.14,'120'),('3.E.Niv 2.02','2/3',75.00,'120'),
    ('3.E.Niv 2.03','1/2',54.68,'120'),('3.E.Niv 2.04','1/2',54.56,'120'),
    ('3.E.Niv 2.05','1/2',60.34,'120'),('3.E.Niv 2.06','2/3',72.15,'120'),
    ('3.E.Niv 3.01','3/5',105.14,'130'),('3.E.Niv 3.02','2/3',75.00,'130'),
    ('3.E.Niv 3.03','1/2',54.68,'130'),('3.E.Niv 3.04','1/2',54.56,'130'),
    ('3.E.Niv 3.05','1/2',60.34,'130'),('3.E.Niv 3.06','2/3',72.15,'130'),
    ('3.F.Niv 1.07','2/3',81.05,'110'),('3.F.Niv 1.08','1/2',54.68,'110'),
    ('3.F.Niv 1.09','1/2',54.68,'110'),('3.F.Niv 1.10','2/4',88.65,'110'),
    ('3.F.Niv 1.11','3/5',98.74,'110'),
    ('3.F.Niv 2.07','2/3',81.05,'120'),('3.F.Niv 2.08','1/2',54.68,'120'),
    ('3.F.Niv 2.09','1/2',54.68,'120'),('3.F.Niv 2.10','2/4',88.65,'120'),
    ('3.F.Niv 2.11','3/5',103.56,'120'),
    ('3.F.Niv 3.07','2/3',81.05,'130'),('3.F.Niv 3.08','1/2',54.68,'130'),
    ('3.F.Niv 3.09','1/2',54.68,'130'),('3.F.Niv 3.10','2/4',88.65,'130'),
    ('3.F.Niv 3.11','3/5',103.56,'130'),
    ('3.F.Niv 4.01','2/3',72.15,'140'),('3.F.Niv 4.02','5/7',129.50,'140'),
    ('3.F.Niv 4.03','3/4',92.29,'140'),('3.F.Niv 4.04','2/4',88.65,'140'),
    ('3.F.Niv 4.05','3/5',103.56,'140'),
    ('3.F.Niv 5.01','2/3',72.15,'150'),('3.F.Niv 5.02','5/7',129.50,'150'),
    ('3.F.Niv 5.03','3/4',92.29,'150'),('3.F.Niv 5.04','2/4',88.65,'150'),
    ('3.F.Niv 5.05','3/5',103.56,'150'),
    ('4.G.Niv 0.1','4/6',123.39,'102'),('4.G.Niv 0.2','5/6',125.13,'102'),
    ('4.G.Niv 0.3','2/3',73.49,'102'),('4.G.Niv 0.4','2/3',73.49,'102'),
    ('4.G.Niv 0.5','',275.28,'102'),
    ('4.G.Niv 1.01','5/6',131.32,'110'),('4.G.Niv 1.02','3/5',104.51,'110'),
    ('4.G.Niv 1.03','1/2',54.68,'110'),('4.G.Niv 1.04','3/5',111.05,'110'),
    ('4.G.Niv 2.01','5/6',136.13,'120'),('4.G.Niv 2.02','3/5',104.51,'120'),
    ('4.G.Niv 2.03','1/2',54.68,'120'),('4.G.Niv 2.04','3/5',111.05,'120'),
    ('4.G.Niv 3.01','5/6',136.13,'130'),('4.G.Niv 3.02','3/5',104.51,'130'),
    ('4.G.Niv 3.03','1/2',54.68,'130'),('4.G.Niv 3.04','3/5',111.05,'130'),
    ('4.H.Niv 1.05','3/5',111.05,'110'),('4.H.Niv 1.06','2/3',73.49,'110'),
    ('4.H.Niv 1.07','2/3',84.07,'110'),('4.H.Niv 1.08','5/6',138.77,'110'),
    ('4.H.Niv 2.05','3/5',111.05,'120'),('4.H.Niv 2.06','2/3',73.49,'120'),
    ('4.H.Niv 2.07','2/3',84.07,'120'),('4.H.Niv 2.08','5/6',143.46,'120'),
    ('4.H.Niv 3.05','3/5',111.05,'130'),('4.H.Niv 3.06','2/3',73.49,'130'),
    ('4.H.Niv 3.07','2/3',84.07,'130'),('4.H.Niv 3.08','5/6',143.46,'130'),
]

def parse_key(s):
    m = re.match(r'^(\d+)\.\w+\.Niv (\d+)\.(\d+)', s.strip())
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

SCOPE = ('3.E', '3.F', '4.G', '4.H')
wb = openpyxl.load_workbook(r'C:/Users/frederik.van.nespen/OneDrive - SBA/Documenten/GitHub/revit-mcp-python/Files/simulatietabel.xlsx', read_only=True)
ws = wb['Table002 (Page 1-4)']
rows = list(ws.iter_rows(values_only=True))

excel = {}
for row in rows[1:]:
    raw = str(row[2]).strip() if row[2] else ''
    if not raw or not any(raw.startswith(p) for p in SCOPE):
        continue
    k = parse_key(raw)
    if k:
        excel[k] = {'number': raw, 'type': str(row[5]).strip() if row[5] else '', 'wo': float(row[7]) if row[7] else 0.0}

flagged = []
revit = {}
for (num, name, area, level) in revit_raw:
    if name == '':
        flagged.append(('UNNAMED', num, area, level))
        continue
    k = parse_key(num)
    if k:
        revit[k] = {'number': num, 'name': name, 'area': area, 'level': level}

ok = type_mismatch = area_diff = no_excel = 0
results = []
for k in sorted(revit.keys()):
    r = revit[k]
    e = excel.get(k)
    if e:
        diff = round(r['area'] - e['wo'], 2)
        type_ok = r['name'] == e['type']
        if not type_ok:
            status = 'TYPE MISMATCH'; type_mismatch += 1
        elif abs(diff) > 0.5:
            status = 'AREA DIFF'; area_diff += 1
        else:
            status = 'OK'; ok += 1
        results.append((r['number'], e['number'], r['name'], e['type'], r['area'], e['wo'], diff, status))
    else:
        status = 'NO EXCEL MATCH'; no_excel += 1
        results.append((r['number'], '-', r['name'], '-', r['area'], '-', None, status))

no_revit = [(k, e) for k, e in sorted(excel.items()) if k not in revit]

print('FASE2 (E+F+G+H): Revit={} | Excel={} | OK={} | TypeMismatch={} | AreaDiff={} | NoExcel={} | NoRevit={}'.format(
    len(revit), len(excel), ok, type_mismatch, area_diff, no_excel, len(no_revit)))

if flagged:
    for f in flagged:
        print('  [UNNAMED] {} | {} m2 | Level {}'.format(f[1], f[2], f[3]))

fmt = '  {:<22} {:<22} {:<6} {:<6} {:<8} {:<8} {:<7} {}'
issues = [r for r in results if r[7] != 'OK']
if issues:
    print(fmt.format('Revit Nr','Excel Nr','R.Type','E.Type','Revit','Excel','Diff','Status'))
    for r in issues:
        diff_str = '{:+.2f}'.format(r[6]) if r[6] is not None else '-'
        print(fmt.format(r[0],r[1],r[2],r[3],r[4],str(r[5]),diff_str,r[7]))
if no_revit:
    print('  No Revit match:', [e['number'] for _,e in no_revit])
