"""Navigation/composition manifest for the RogueMon rules site.

Each page pulls one or more README sections (matched to their `##` headings by
slug) into its body. The Just the Docs nav hierarchy is expressed by `parent`
and `grand_parent`, which must equal the parent page's exact `title`. README
order is preserved in the source file; this manifest defines the site tree.

To re-shape the site, edit this list. To change content, edit README.md.
"""

PAGES = [
    {"title": "About RogueMon", "slug": "about", "nav_order": 1,
     "sections": ["What is RogueMon?", "Game Elements"]},

    {"title": "RogueMon Rules", "slug": "rules", "nav_order": 2,
     "has_children": True, "sections": []},

    {"title": "Ascension Levels", "slug": "ascension-levels",
     "parent": "RogueMon Rules", "nav_order": 1,
     "sections": ["Ascension Difficulty Increase", "Bag Space Cap", "Trainers"]},

    {"title": "Game Progression", "slug": "game-progression",
     "parent": "RogueMon Rules", "nav_order": 2, "has_children": True,
     "sections": []},

    {"title": "Overview", "slug": "overview",
     "parent": "Game Progression", "grand_parent": "RogueMon Rules",
     "nav_order": 1, "sections": ["Game Progression"]},

    {"title": "Milestones", "slug": "milestones",
     "parent": "Game Progression", "grand_parent": "RogueMon Rules",
     "nav_order": 2, "sections": ["Gyms", "Buy Phase", "Cleansing Phase"]},

    {"title": "Starting the Run", "slug": "starting-the-run",
     "parent": "Game Progression", "grand_parent": "RogueMon Rules",
     "nav_order": 3, "sections": ["Lab", "Wild Pokemon", "The KARP"]},

    {"title": "Evolutions", "slug": "evolutions",
     "parent": "Game Progression", "grand_parent": "RogueMon Rules",
     "nav_order": 4, "sections": ["Evolutions", "Unique Evolution Methods"]},

    {"title": "Forced Route", "slug": "forced-route",
     "parent": "Game Progression", "grand_parent": "RogueMon Rules",
     "nav_order": 5, "sections": ["Forced Route"]},

    {"title": "Items", "slug": "items",
     "parent": "RogueMon Rules", "nav_order": 3,
     "sections": ["General Item Rules", "When You Do Pick Up an Item",
                  "Healing Items", "Medicine Item", "Consumables", "TMs",
                  "Other Items"]},

    {"title": "Prizes", "slug": "prizes",
     "parent": "RogueMon Rules", "nav_order": 4,
     "sections": ["Prize Rolls"]},

    {"title": "Curses", "slug": "curses",
     "parent": "RogueMon Rules", "nav_order": 5,
     "sections": ["Curses"]},

    {"title": "Banned List", "slug": "banned-list",
     "parent": "RogueMon Rules", "nav_order": 6,
     "sections": ["Banned Move/Ability/Item and Combinations List"]},
]
