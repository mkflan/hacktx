"""Controlled vocabulary for the catalog and the landing form, plus the project() helper."""

MAJORS: tuple[str, ...] = (
    "Computer Science",
    "Electrical and Computer Engineering",
    "Mechanical Engineering",
    "Biomedical Engineering",
    "Biology",
    "Chemistry",
    "Mathematics",
    "Physics",
    "Environmental Science",
)

# Every interest tag used anywhere in the catalog. Lowercase; matching is case-insensitive.
INTERESTS: tuple[str, ...] = (
    "sensors", "plants", "sustainability", "energy", "robotics", "3d printing",
    "machine learning", "computer vision", "natural language processing", "data visualization",
    "web apps", "language learning", "music", "games", "health", "neuroscience", "genetics",
    "microbiology", "chemistry lab", "optics", "astronomy", "climate", "water", "agriculture",
    "ecology", "statistics", "simulation", "cybersecurity", "embedded systems", "education",
    "maps", "cycling", "cooking", "command line tools", "automation", "signal processing",
    "electronics", "transportation", "art", "food", "networks", "control systems",
    "bioinformatics", "probability", "mechanics", "acoustics", "iot", "python",
)  # fmt: skip

# Shown as checkboxes on the landing page (the rest still work as tags).
FEATURED_INTERESTS: tuple[str, ...] = (
    "sensors", "plants", "sustainability", "energy", "robotics", "3d printing",
    "machine learning", "computer vision", "data visualization", "web apps",
    "language learning", "music", "games", "health", "neuroscience", "genetics",
    "microbiology", "chemistry lab", "optics", "astronomy", "climate", "water", "agriculture",
    "ecology", "statistics", "simulation", "cybersecurity", "embedded systems", "education",
    "maps", "cycling", "electronics",
)  # fmt: skip

# Landing form choices: key, label, total hours stored on the user.
TIMEFRAME_OPTIONS: tuple[tuple[str, str, float], ...] = (
    ("weekend", "A weekend (about 12 hours)", 12),
    ("two_weeks", "Two weeks (about 25 hours)", 25),
    ("month", "A month (about 40 hours)", 40),
    ("semester", "A semester (about 100 hours)", 100),
)

DIFFICULTIES: tuple[str, ...] = ("beginner", "intermediate", "advanced")


def project(
    slug: str,
    name: str,
    *,
    majors: tuple[str, ...],
    interests: tuple[str, ...],
    difficulty: str,
    hours: float,
    description: str,
    start: tuple[str, ...],
    materials: tuple[tuple, ...] = (),
    guides: tuple[tuple, ...] = (),
    docs: tuple[tuple, ...] = (),
) -> dict:
    """One catalog project.

    start:     ordered getting-started steps (one per line in the database)
    materials: (name, quantity, purpose, estimated_cost_usd)
    guides:    (slug, title, content_excerpt, tags) authored text guides, no URL
    docs:      (slug, title, url, provider, tags) documentation or data home pages
    """
    for major in majors:
        assert major in MAJORS, (slug, major)
    for tag in interests:
        assert tag in INTERESTS, (slug, tag)
    assert difficulty in DIFFICULTIES, (slug, difficulty)
    resources = [
        {
            "slug": g_slug,
            "title": title,
            "url": None,
            "kind": "guide",
            "provider": None,
            "tags": tags,
            "excerpt": excerpt,
        }
        for g_slug, title, excerpt, tags in guides
    ] + [
        {
            "slug": d_slug,
            "title": title,
            "url": url,
            "kind": "documentation",
            "provider": provider,
            "tags": tags,
            "excerpt": None,
        }
        for d_slug, title, url, provider, tags in docs
    ]
    for resource in resources:
        for tag in resource["tags"]:
            assert tag in INTERESTS, (slug, resource["slug"], tag)
    slugs = [r["slug"] for r in resources]
    assert len(slugs) == len(set(slugs)), (slug, "duplicate resource slug")
    return {
        "slug": slug,
        "name": name,
        "majors": majors,
        "interests": interests,
        "difficulty": difficulty,
        "hours": float(hours),
        "description": description,
        "getting_started": "\n".join(start),
        "materials": [
            {"name": n, "quantity": q, "purpose": p, "estimated_cost_usd": c}
            for n, q, p, c in materials
        ],
        "resources": resources,
    }
