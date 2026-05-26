#!/usr/bin/env python3
"""Generate Just the Docs pages from the cleaned README.md + site_structure.py.

README.md is the single source of truth. This splits its `##` sections and
composes them into the page tree defined in tools/site_structure.py, writing
one Markdown file per page into pages/ with Just the Docs nav front matter.
Images referenced by the README (GitHub URLs) are vendored/rewritten to local
/images/ paths so the site is self-contained. Re-runnable: pages/ is wiped each
run; README image URLs are left untouched (so the README still renders on GitHub).
"""

import html
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_structure import PAGES

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
PAGES_DIR = ROOT / "pages"
SRC_IMAGES = ROOT / "images"

# Featured links for the home-page list (labels as provided by the user).
FEATURED_LINKS = [
    ("RogueMon Rules", "/rules/"),
    ("Play RogueMon", "https://crozwords.itch.io/roguemon"),
    ("RogueMon Leaderboard", "https://www.roguemon.gg/"),
]


def slugify(text):
    text = html.unescape(re.sub(r'<[^>]+>', '', text)).split('(')[0]
    text = text.replace('/', ' ').lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_]+', '-', text).strip('-')


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------

_image_cache = {}


def resolve_image(src):
    if src in _image_cache:
        return _image_cache[src]
    result = src
    m = re.search(r'/images/([^"?]+)$', src)
    if "user-attachments/assets/" in src:
        asset_id = src.rstrip("/").split("/")[-1]
        name = "att-%s.png" % asset_id[:8]
        dest = SRC_IMAGES / name
        if not dest.exists():
            try:
                req = urllib.request.Request(src, headers={"User-Agent": "roguemon-site"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    dest.write_bytes(r.read())
            except Exception as exc:
                print("WARNING: could not vendor %s (%s)" % (src, exc), file=sys.stderr)
                _image_cache[src] = src
                return src
        result = "/images/" + urllib.parse.quote(name)
    elif m:
        name = urllib.parse.unquote(m.group(1))
        if not (SRC_IMAGES / name).exists():
            print("WARNING: missing image images/%s" % name, file=sys.stderr)
        result = "/images/" + urllib.parse.quote(name)
    elif "github.com" in src and "/blob/" in src:
        tail = urllib.parse.unquote(src.split("/blob/", 1)[1].split("/", 1)[1])
        root_file = ROOT / tail
        if root_file.exists():
            norm = re.sub(r'\s+', '-', tail.lower())
            shutil.copy2(root_file, SRC_IMAGES / norm)
            result = "/images/" + urllib.parse.quote(norm)
        else:
            print("WARNING: blob image not at root: %s" % tail, file=sys.stderr)
    _image_cache[src] = result
    return result


def rewrite_images(text):
    return re.sub(r'src="([^"]*)"',
                  lambda m: 'src="%s"' % resolve_image(m.group(1)), text)


def vendor_attachments(text):
    for url in set(re.findall(r'src="([^"]*user-attachments[^"]*)"', text)):
        resolve_image(url)


# --------------------------------------------------------------------------
# Parse README into ## sections (body excludes the heading line)
# --------------------------------------------------------------------------

def parse_sections(text):
    sections = {}  # slug -> {"title": str, "lines": [..]}
    current = None
    for line in text.split("\n"):
        m = re.match(r'^##\s+(.*?)\s*$', line)
        if m and not line.startswith("###"):
            title = m.group(1).strip()
            current = {"title": title, "lines": []}
            sections[slugify(title)] = current
        elif current is not None:
            current["lines"].append(line)
    return sections


def trim(lines):
    out = list(lines)
    while out and (not out[0].strip() or out[0].strip() == "---"):
        out.pop(0)
    while out and (not out[-1].strip() or out[-1].strip() == "---"):
        out.pop()
    return out


def promote_headings(lines):
    return [re.sub(r'^(#{3,6})(\s)', lambda m: m.group(1)[1:] + m.group(2), ln)
            for ln in lines]


# --------------------------------------------------------------------------
# Emit
# --------------------------------------------------------------------------

def front_matter(page):
    fm = ['---', 'title: "%s"' % page["title"], 'layout: default']
    if page.get("parent"):
        fm.append('parent: "%s"' % page["parent"])
    if page.get("grand_parent"):
        fm.append('grand_parent: "%s"' % page["grand_parent"])
    fm.append('nav_order: %d' % page.get("nav_order", 1))
    if page.get("has_children"):
        fm.append('has_children: true')
    fm.append('permalink: /%s/' % page["slug"])
    fm.append('---')
    return "\n".join(fm)


def build_anchor_map():
    anchors = {}
    for page in PAGES:
        anchors[page["slug"]] = "/%s/" % page["slug"]
        for sec in page["sections"]:
            anchors[slugify(sec)] = "/%s/" % page["slug"]
    return anchors


def rewrite_anchors(text, anchors):
    def repl(m):
        key = slugify(m.group(1))
        return "](%s)" % anchors[key] if key in anchors else m.group(0)
    return re.sub(r'\]\(#([^)]+)\)', repl, text)


def build_home(sections, anchors):
    """Home page: 'What is RogueMon?' intro, then the featured-link list, then
    the README's 'Creator and Useful Links' content. All sourced; no added copy."""
    parts = ["# RogueMon"]
    wir = sections.get("what-is-roguemon")
    if wir:
        parts.append("## What is RogueMon?\n\n" + "\n".join(trim(wir["lines"])))
    parts.append("\n".join("- [%s](%s)" % (label, url)
                           for label, url in FEATURED_LINKS))
    creator = sections.get("creator-and-useful-links")
    if creator:
        parts.append("## Creator and Useful Links\n\n"
                     + "\n".join(trim(creator["lines"])))
    body = rewrite_anchors(rewrite_images("\n\n".join(parts)), anchors)
    fm = "\n".join(["---", "title: Home", "layout: default",
                    "nav_order: 0", "permalink: /", "---"])
    (ROOT / "index.md").write_text(fm + "\n\n" + body.strip() + "\n",
                                   encoding="utf-8")


def main():
    text = README.read_text(encoding="utf-8")
    vendor_attachments(text)
    sections = parse_sections(text)
    anchors = build_anchor_map()

    if PAGES_DIR.exists():
        shutil.rmtree(PAGES_DIR)
    PAGES_DIR.mkdir()

    missing = []
    for page in PAGES:
        single = len(page["sections"]) == 1
        page_slug = page["slug"]
        body_parts = []
        for sec_name in page["sections"]:
            sec = sections.get(slugify(sec_name))
            if sec is None:
                missing.append((page["title"], sec_name))
                continue
            lines = trim(sec["lines"])
            if single:
                body_parts.append("\n".join(promote_headings(lines)))
            elif slugify(sec["title"]) == slugify(page["title"]):
                body_parts.append("\n".join(lines))           # drop redundant heading
            else:
                body_parts.append("## %s\n\n%s" % (sec["title"], "\n".join(lines)))

        body = "\n\n".join(p for p in body_parts if p.strip())
        body = rewrite_anchors(rewrite_images(body), anchors)
        body = "# %s\n\n%s" % (page["title"], body.strip())
        (PAGES_DIR / (page_slug + ".md")).write_text(
            front_matter(page) + "\n\n" + body.strip() + "\n", encoding="utf-8")

    build_home(sections, anchors)

    if missing:
        print("WARNING: unmatched sections:", file=sys.stderr)
        for pg, sec in missing:
            print("  %s <- %s" % (pg, sec), file=sys.stderr)
    print("Generated %d pages into %s/" % (len(PAGES), PAGES_DIR.name))


if __name__ == "__main__":
    main()
