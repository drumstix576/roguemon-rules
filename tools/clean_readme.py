#!/usr/bin/env python3
"""One-shot README.md formatting cleanup for translation into the Jekyll site.

Transforms (idempotent):
  - Drops the top table-of-contents nav line.
  - Converts centered HTML banner headers (<h1 align="center">X</h1>, including
    the malformed `# <h3 ...>X</h1>` ones) to Markdown `## X`.
  - De-shouts ALL-CAPS headings (LAB -> Lab), preserving acronyms and RogueMon.
  - Converts single-column "callout" tables to a bold lead line + bullet list.
  - Leaves real multi-column tables (evolution methods, ascension, curses,
    prizes) untouched.
  - Leaves <img> tags and their GitHub URLs alone (the site generator rewrites
    those; the README must keep rendering on GitHub).

The Forced Route section is finalized by hand afterward: its source mixes
single-cell tables and bare lines too irregularly to infer a step list. Run
from the repo root: python3 tools/clean_readme.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

SMALL_WORDS = {"a", "an", "the", "of", "to", "in", "on", "and", "or", "for",
               "vs", "with", "at", "by"}
ACRONYMS = {"HP", "PP", "BST", "TM", "PC", "NPC", "KO", "IV", "EV", "SS",
            "EXP", "QOL", "A1", "A2", "A3", "FRLG", "VR", "KARP", "SS"}

CENTER_HEADER = re.compile(r'^\s*#*\s*<h[1-6]\b[^>]*align\s*=\s*["\']?center["\']?[^>]*>(.*?)</h\d+>\s*$', re.I)
ATX = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
NAV_TOC = re.compile(r'^\s*#{1,6}\s+\[[^\]]+\]\(#')
# Empty grouping banners that exist only to nest content (the site nav supplies
# that grouping), and prize sub-rolls that should nest under "Prize Rolls".
EMPTY_BANNERS = {"roguemon rules", "items"}
PRIZE_SUBROLL = re.compile(r'^(Prize \d|Mt\. Moon Prize)\b', re.I)
ALLCAPS_HEADING = re.compile(r'^[A-Z0-9][A-Z0-9 /]{3,}$')
BAG_CAP = re.compile(r'^\s*(\d+) badges? = HP = (\d+),? Status = (\d+)\s*$')


def smart_title(text):
    text = text.strip()
    words = text.split(' ')
    out = []
    for i, word in enumerate(words):
        pieces = word.split('/')
        rebuilt = []
        for piece in pieces:
            if not piece:
                rebuilt.append(piece)
            elif piece.upper() == "ROGUEMON":
                rebuilt.append("RogueMon")
            elif piece.upper() in ACRONYMS:
                rebuilt.append(piece.upper())
            elif piece.isupper():
                low = piece.lower()
                if i > 0 and low in SMALL_WORDS:
                    rebuilt.append(low)
                else:
                    rebuilt.append(low[:1].upper() + low[1:])
            else:
                rebuilt.append(piece)
        out.append('/'.join(rebuilt))
    return ' '.join(out)


def split_cells(line):
    cells = [c.strip() for c in line.split('|')]
    if cells and cells[0] == '':
        cells = cells[1:]
    if cells and cells and cells[-1] == '':
        cells = cells[:-1]
    return cells


def is_table_row(line):
    return '|' in line and line.strip() != ''


def is_separator_row(cells):
    return bool(cells) and all(re.match(r'^:?-{2,}:?$', c) for c in cells)


def convert_callout(rows):
    """rows: list of raw table lines. Returns list of output markdown lines."""
    parsed = [split_cells(r) for r in rows]
    data = [c for c in parsed if not is_separator_row(c)]
    out = []
    if not data:
        return out
    if len(data) == 1:
        out.append(data[0][0])
    else:
        first = data[0][0]
        start = 0
        # A bold or italic first cell is the callout's lead line, not a bullet.
        if first.startswith('*'):
            out.append(first)
            out.append('')
            start = 1
        for cells in data[start:]:
            out.append('- ' + cells[0])
    return out


def clean(text):
    lines = text.split('\n')
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Drop the top ToC nav line.
        if NAV_TOC.match(line):
            i += 1
            continue

        # Bag-space-cap block: tab-indented "N badges = HP = .. Status = .." lines
        # become a real table.
        if BAG_CAP.match(line):
            rows = []
            while i < n and BAG_CAP.match(lines[i]):
                g = BAG_CAP.match(lines[i])
                rows.append((g.group(1), g.group(2), g.group(3)))
                i += 1
            out.append('| Badges | HP Cap | Status Cap |')
            out.append('|:------:|:------:|:----------:|')
            for badges, hp, status in rows:
                out.append('| %s | %s | %s |' % (badges, hp, status))
            continue

        # Table block: gather consecutive table rows.
        if is_table_row(line):
            block = []
            while i < n and is_table_row(lines[i]):
                block.append(lines[i])
                i += 1
            # Index of the first real multi-column row (callouts glued on top of a
            # data table, like the Curses intro, get peeled off as a callout).
            first_multi = None
            for idx, r in enumerate(block):
                cells = split_cells(r)
                if not is_separator_row(cells) and len(cells) > 1:
                    first_multi = idx
                    break
            # kramdown needs a blank line before/after a table or list block.
            if out and out[-1].strip() != '':
                out.append('')
            if first_multi is None:
                out.extend(convert_callout(block))
            elif first_multi == 0:
                out.extend(block)
            else:
                out.extend(convert_callout(block[:first_multi]))
                out.append('')
                out.extend(block[first_multi:])
            out.append('')
            continue

        # Centered HTML header -> Markdown ##.
        m = CENTER_HEADER.match(line)
        if m:
            title = smart_title(re.sub(r'<[^>]+>', '', m.group(1)).strip())
            if title.lower() not in EMPTY_BANNERS:
                out.append('## ' + title)
            i += 1
            continue

        # Existing Markdown header -> de-shout the text.
        m = ATX.match(line)
        if m:
            title = smart_title(m.group(2))
            if title.lower() in EMPTY_BANNERS:   # drop content-less grouping banner
                i += 1
                continue
            level = m.group(1)
            if len(level) == 2 and PRIZE_SUBROLL.match(title):
                level = '###'                    # nest prize rolls under "Prize Rolls"
            out.append(level + ' ' + title)
            i += 1
            continue

        # Standalone ALL-CAPS label (e.g. "A2 BANLIST") -> sub-heading.
        s = line.strip()
        if ALLCAPS_HEADING.match(s) and '=' not in s:
            out.append('### ' + smart_title(s))
            i += 1
            continue

        out.append(line)
        i += 1

    # Collapse 3+ blank lines to 2.
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))
    return result.rstrip() + '\n'


def main():
    if not README.exists():
        sys.exit("README.md not found")
    README.write_text(clean(README.read_text(encoding='utf-8')), encoding='utf-8')
    print("Cleaned README.md (review with: git diff README.md)")


if __name__ == "__main__":
    main()
