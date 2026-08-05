import zipfile
import os

zip_path = 'hospital_management.zip'
if not os.path.exists(zip_path):
    print('ERROR: ZIP not found at', zip_path)
    raise SystemExit(2)

with zipfile.ZipFile(zip_path) as z:
    names = z.namelist()
    print('TOTAL_FILES:', len(names))
    # print a short listing
    for n in names[:200]:
        print(n)

    def find_by_suffix(suffix):
        return [n for n in names if n.replace('\\', '/').endswith(suffix)]

    docs_files = find_by_suffix('docs/business_rules.md')
    design_files = find_by_suffix('docs/001-initial-design.md')
    access_files = find_by_suffix('security/ir.model.access.csv')

    if docs_files:
        for p in docs_files:
            print('\nFOUND:', p)
            with z.open(p) as f:
                data = f.read().decode('utf-8', errors='replace')
                print('\n--- business_rules.md (first 400 chars) ---')
                print(data[:400])
    else:
        print('\nMISSING: docs/business_rules.md')

    if design_files:
        for p in design_files:
            print('\nFOUND:', p)
            with z.open(p) as f:
                data = f.read().decode('utf-8', errors='replace')
                print('\n--- 001-initial-design.md (first 400 chars) ---')
                print(data[:400])
    else:
        print('\nMISSING: docs/001-initial-design.md')

    if access_files:
        for p in access_files:
            print('\nFOUND:', p)
            with z.open(p) as f:
                data = f.read().decode('utf-8', errors='replace')
                print('\n--- ir.model.access.csv (first 400 chars) ---')
                print(data[:400])
    else:
        print('\nMISSING: security/ir.model.access.csv')

    print('\nINSPECTION_COMPLETE')
