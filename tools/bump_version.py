#!/usr/bin/env python3
"""Set the new recorder's version everywhere it appears, in one step.

    python3 tools/bump_version.py 201

Updates js/config.js, the recorder page (app_next.html while it is being tested,
app.html after the switch), every ?v= cache-buster in that page and in css/app.css,
and the matching key in version.json. The legacy pages are never touched.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def read(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def replace(path, pattern, replacement, expect_at_least=1):
    text = read(path)
    updated, count = re.subn(pattern, replacement, text)
    if count < expect_at_least:
        sys.exit(f'{path}: expected to update {pattern!r} at least {expect_at_least} time(s), found {count}')
    write(path, updated)
    print(f'  {path}: {count} change(s)')


def recorder_page():
    if os.path.exists(os.path.join(ROOT, 'app_next.html')):
        return 'app_next.html', 'nextAppVersion'
    if 'js/config.js' in read('app.html'):
        return 'app.html', 'appVersion'
    sys.exit('Could not find the new recorder page (app_next.html or app.html loading js/config.js).')


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r'\d+', sys.argv[1]):
        sys.exit(__doc__)
    version = sys.argv[1]
    page, key = recorder_page()
    print(f'Setting the recorder version to {version} ({page}, version.json "{key}")')
    replace('js/config.js', r"APP_VERSION: '\d+'", f"APP_VERSION: '{version}'")
    replace('js/config.js', r"MATERIAL_VERSION: 'materials_v\d+'", f"MATERIAL_VERSION: 'materials_v{version}'")
    replace(page, r'\?v=\d+', f'?v={version}', expect_at_least=10)
    replace(page, r"var APP_VERSION = '\d+'", f"var APP_VERSION = '{version}'")
    replace('css/app.css', r'\?v=\d+', f'?v={version}')
    if page == 'app.html':
        replace('index.html', r"const APP_VERSION = '\d+'", f"const APP_VERSION = '{version}'")
    data = json.loads(read('version.json'))
    data[key] = version
    write('version.json', json.dumps(data, indent=2) + '\n')
    print(f'  version.json: {key} = {version}')


if __name__ == '__main__':
    main()
