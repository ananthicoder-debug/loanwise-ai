"""One-shot script: replace all non-ASCII in every .py file under backend/"""
import pathlib

root = pathlib.Path(__file__).parent

REPLACEMENTS = {
    '\u20b9': 'Rs.',
    '\u2014': ' - ',
    '\u2013': '-',
    '\u2192': '->',
    '\u2190': '<-',
    '\u00a0': ' ',
    '\u201c': '"',
    '\u201d': '"',
    '\u2018': "'",
    '\u2019': "'",
    '\ufeff': '',
}

fixed = 0
for py_file in root.rglob('*.py'):
    if '__pycache__' in str(py_file):
        continue
    try:
        raw = py_file.read_bytes()
        # Remove BOM if present
        if raw[:3] == b'\xef\xbb\xbf':
            raw = raw[3:]
        text = raw.decode('utf-8', errors='replace')
        original = text
        for bad, good in REPLACEMENTS.items():
            text = text.replace(bad, good)
        # Replace any remaining non-ASCII with ?
        clean = ''.join(c if ord(c) < 128 else '?' for c in text)
        if clean != original:
            py_file.write_text(clean, encoding='ascii')
            print(f'Fixed: {py_file}')
            fixed += 1
    except Exception as e:
        print(f'Error {py_file.name}: {e}')

print(f'\nTotal fixed: {fixed} files')
