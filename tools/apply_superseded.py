#!/usr/bin/env python3
"""Apply superseded.json after merging recordings from several places.

Each participant folder (from the recorder's folder mode or unzipped ZIP files) has
logs/superseded.json: every recording that a newer recording of the same sentence (in the
same round) replaced. On one device the recorder already keeps replaced recordings out of
<participant>/, but when files from several places are merged (two folders, or ZIP files
saved at different times) a replaced recording can sit next to its replacement. This
moves every listed file (and its .json sidecar) from <participant>/ to
<participant>/not_used/. It never deletes anything.

    python3 tools/apply_superseded.py MERGED/P017            # show what would move
    python3 tools/apply_superseded.py MERGED/P017 --apply    # move
"""
import json
import os
import shutil
import sys


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply = '--apply' in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    folder = args[0]
    log = os.path.join(folder, 'logs', 'superseded.json')
    if not os.path.exists(log):
        sys.exit(f'No {log}: nothing was replaced.')
    with open(log, encoding='utf-8') as handle:
        replaced = json.load(handle).get('replaced', [])
    target = os.path.join(folder, 'not_used')
    moved = 0
    for item in replaced:
        name = item['fileName']
        source = os.path.join(folder, name)
        if not os.path.exists(source):
            continue
        sidecar = os.path.splitext(name)[0] + '.json'
        print(f'{"moving" if apply else "would move"}: {name}  (replaced by {item.get("supersededBy")})')
        if apply:
            os.makedirs(target, exist_ok=True)
            shutil.move(source, os.path.join(target, name))
            if os.path.exists(os.path.join(folder, sidecar)):
                shutil.move(os.path.join(folder, sidecar), os.path.join(target, sidecar))
        moved += 1
    print(f'{moved} file(s) {"moved" if apply else "to move (run with --apply)"}.')


if __name__ == '__main__':
    main()
