import openpyxl, re

revit_raw = [
    ('1.A.Niv 0.01','3/4',89.85,'102'),('1.A.Niv 0.02','2/3',85.30,'102'),
    ('1.A.Niv 0.03','1/2',54.68,'102'),('1.A.Niv 0.04','1/2',54.68,'102'),
    ('1.A.Niv 0.05','1/2',57.59,'102'),('1.A.Niv 0.06','1/2',67.07,'102'),
    ('1.A.Niv 0.07','1/2',57.77,'102'),('1.A.Niv 0.08','1/2',57.59,'102'),
    ('1.A.Niv 0.09','1/2',54.68,'102'),('1.A.Niv 0.10','1/2',54.68,'102'),
    ('1.A.Niv 0.11','2/3',77.04,'102'),('1.A.Niv 0.12','2/3',103.08,'102'),
    ('1.A.Niv 1.01','3/5',97.65,'110'),('1.A.Niv 1.02','2/3',85.30,'110'),
    ('1.A.Niv 1.03','2/3',73.49,'110'),('1.A.Niv 1.04','1/2',54.68,'110'),
    ('1.A.Niv 1.05','1/2',57.59,'110'),('1.A.Niv 1.06','1/2',57.93,'110'),
    ('1.A.Niv 1.07','1/2',54.96,'110'),('1.A.Niv 1.08','1/2',54.96,'110'),
    ('1.A.Niv 1.09','1/2',57.77,'110'),('1.A.Niv 1.10','1/2',57.59,'110'),
    ('1.A.Niv 1.11','1/2',54.68,'110'),('1.A.Niv 1.12','1/2',54.68,'110'),
    ('1.A.Niv 1.13','2/3',77.04,'110'),('1.A.Niv 1.14','3/5',111.01,'110'),
    ('1.A.Niv 2.01','3/5',102.47,'120'),('1.A.Niv 2.02','2/3',85.30,'120'),
    ('1.A.Niv 2.03','1/2',54.68,'120'),('1.A.Niv 2.04','1/2',54.68,'120'),
    ('1.A.Niv 2.05','3/5',103.26,'120'),('1.A.Niv 2.06','2/3',72.30,'120'),
    ('1.A.Niv 2.07','1/2',54.96,'120'),('1.A.Niv 2.08','2/3',78.55,'120'),
    ('1.A.Niv 2.09','1/2',54.68,'120'),('1.A.Niv 2.10','2/3',77.04,'120'),
    ('1.A.Niv 2.11','3/5',115.83,'120'),
    ('1.A.Niv 3.01','3/5',102.47,'130'),('1.A.Niv 3.02','2/3',85.30,'130'),
    ('1.A.Niv 3.03','1/2',54.68,'130'),('1.A.Niv 3.04','1/2',54.68,'130'),
    ('1.A.Niv 3.05','3/5',103.26,'130'),('1.A.Niv 3.06','2/3',72.30,'130'),
    ('1.A.Niv 3.07','1/2',54.96,'130'),('1.A.Niv 3.08','2/3',78.55,'130'),
    ('1.A.Niv 3.09','1/2',54.68,'130'),('1.A.Niv 3.10','2/3',77.04,'130'),
    ('1.A.Niv 3.11','3/5',115.83,'130'),
    ('1.B.Niv 4.01','2/3',78.55,'140'),('1.B.Niv 4.02','1/2',54.68,'140'),
    ('1.B.Niv 4.03','2/3',77.04,'140'),('1.B.Niv 4.04','3/5',115.83,'140'),
    ('1.B.Niv 5.01','2/3',78.55,'150'),('1.B.Niv 5.02','1/2',54.68,'150'),
    ('1.B.Niv 5.03','2/3',77.04,'150'),('1.B.Niv 5.04','3/5',115.83,'150'),
    ('2.C.Niv 1.01','2/3',77.52,'110'),('2.C.Niv 1.02','1/2',55.19,'110'),
    ('2.C.Niv 1.03','3/4',92.48,'110'),('2.C.Niv 1.04','4/5',114.46,'110'),
    ('2.C.Niv 1.05','3/4',90.17,'110'),('2.C.Niv 1.06','3/5',105.07,'110'),
    ('2.C.Niv 1.07','2/3',72.17,'110'),('2.C.Niv 1.08','2/3',77.52,'110'),
    ('2.C.Niv 2.01','2/3',77.52,'120'),('2.C.Niv 2.02','1/2',55.19,'120'),
    ('2.C.Niv 2.03','3/4',92.48,'120'),('2.C.Niv 2.04','4/5',114.46,'120'),
    ('2.C.Niv 2.05','3/4',90.17,'120'),('2.C.Niv 2.06','3/5',105.07,'120'),
    ('2.C.Niv 2.07','2/3',72.17,'120'),('2.C.Niv 2.08','2/3',77.52,'120'),
    ('2.C.Niv 3.01','2/3',77.52,'130'),('2.C.Niv 3.02','1/2',55.19,'130'),
    ('2.C.Niv 3.03','3/4',92.48,'130'),('2.C.Niv 3.04','4/5',114.46,'130'),
    ('2.C.Niv 3.05','3/4',90.17,'130'),('2.C.Niv 3.06','3/5',105.07,'130'),
    ('2.C.Niv 3.07','2/3',72.17,'130'),('2.C.Niv 3.08','2/3',77.52,'130'),
]

def parse_key(s):
    # Returns (building_int, floor, unit) e.g. '1.A.Niv 2.07' -> (1, 2, 7)
    m = re.match(r'^(\d+)\.\w+\.Niv (\d+)\.(\d+)', s.strip())
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

# Build revit lookup
revit = {}
for (num, name, area, level) in revit_raw:
    k = parse_key(num)
    if k:
        revit[k] = {'number': num, 'name': name, 'area': area, 'level': level}

# Load Excel
SCOPE = ('1.A', '1.B', '2.C', '2.D')
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
        results.append((r['number'], e['number'], r['name'], e['type'], r['area'], e['wo'], diff, r['level'], status))
    else:
        status = 'NO EXCEL MATCH'; no_excel += 1
        results.append((r['number'], '-', r['name'], '-', r['area'], '-', None, r['level'], status))

no_revit = [(k, e) for k, e in sorted(excel.items()) if k not in revit]

print('Revit: {} | Excel: {} | OK: {} | Type mismatch: {} | Area diff (>0.5m2): {} | No Excel: {} | No Revit: {}'.format(
    len(revit), len(excel), ok, type_mismatch, area_diff, no_excel, len(no_revit)))
print()
fmt = '{:<22} {:<22} {:<6} {:<6} {:<10} {:<10} {:<7} {}'
print(fmt.format('Revit Nr','Excel Nr','R.Type','E.Type','Revit m2','Excel m2','Diff','Status'))
print('-'*100)
for row in results:
    diff_str = '{:+.2f}'.format(row[6]) if row[6] is not None else '-'
    flag = ' <--' if row[8] != 'OK' else ''
    print(fmt.format(row[0],row[1],row[2],row[3],row[4],str(row[5]),diff_str, row[8]+flag))

if no_revit:
    print('\nExcel entries NOT in Revit:')
    for k, e in no_revit:
        print('  {} | {} | {} m2'.format(e['number'], e['type'], e['wo']))
