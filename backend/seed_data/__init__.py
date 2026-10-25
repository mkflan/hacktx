"""Authored demo catalog: majors, the interest vocabulary, demo users and ~47 projects.

Content rules (see CLAUDE.md): project text, outlines and materials are written by the team.
Every URL here is a well-known documentation or data home page that the team used; links
found by search engines are added later by scripts/enrich_catalog.py and labeled
"serpapi:<engine>". Nothing is marked verified: a working link is not a content check.
"""

from .projects_a import PROJECTS as _A
from .projects_b import PROJECTS as _B
from .projects_c import PROJECTS as _C
from .vocab import (
    DIFFICULTIES,
    FEATURED_INTERESTS,
    INTERESTS,
    MAJORS,
    TIMEFRAME_OPTIONS,
    project,
)

PROJECTS: tuple[dict, ...] = (*_A, *_B, *_C)

# The two scripted demo accounts. They differ on every axis the ranking uses.
DEMO_USERS: tuple[dict, ...] = (
    {
        "username": "alex_demo",
        "major": "Electrical and Computer Engineering",
        "interests": ("sensors", "plants", "sustainability"),
        "hours": 12,
        "time_raw": "12 total hours (a weekend or two)",
        "difficulty": "beginner",
    },
    {
        "username": "maya_demo",
        "major": "Computer Science",
        "interests": ("language learning", "web apps", "data visualization"),
        "hours": 40,
        "time_raw": "40 total hours (about a month)",
        "difficulty": "intermediate",
    },
)

# Fictional community members who author the seeded forum starters.
COMMUNITY_USERS: tuple[dict, ...] = (
    {
        "username": "priya_bme",
        "major": "Biomedical Engineering",
        "interests": ("sensors", "health", "signal processing"),
        "hours": 25,
        "time_raw": "25 total hours",
        "difficulty": "intermediate",
    },
    {
        "username": "diego_builds",
        "major": "Mechanical Engineering",
        "interests": ("3d printing", "robotics", "cycling"),
        "hours": 40,
        "time_raw": "40 total hours",
        "difficulty": "intermediate",
    },
    {
        "username": "hana_bio",
        "major": "Biology",
        "interests": ("ecology", "plants", "data visualization"),
        "hours": 12,
        "time_raw": "12 total hours",
        "difficulty": "beginner",
    },
    {
        "username": "sam_chem",
        "major": "Chemistry",
        "interests": ("chemistry lab", "optics", "energy"),
        "hours": 30,
        "time_raw": "30 total hours",
        "difficulty": "intermediate",
    },
    {
        "username": "lin_math",
        "major": "Mathematics",
        "interests": ("probability", "simulation", "music"),
        "hours": 100,
        "time_raw": "100 total hours (a semester)",
        "difficulty": "advanced",
    },
    {
        "username": "omar_phys",
        "major": "Physics",
        "interests": ("astronomy", "optics", "electronics"),
        "hours": 80,
        "time_raw": "80 total hours",
        "difficulty": "advanced",
    },
    {
        "username": "rosa_env",
        "major": "Environmental Science",
        "interests": ("water", "climate", "sustainability"),
        "hours": 30,
        "time_raw": "30 total hours",
        "difficulty": "intermediate",
    },
    {
        "username": "kai_cs",
        "major": "Computer Science",
        "interests": ("machine learning", "computer vision", "games"),
        "hours": 60,
        "time_raw": "60 total hours",
        "difficulty": "advanced",
    },
)

USERS: tuple[dict, ...] = (*DEMO_USERS, *COMMUNITY_USERS)

__all__ = [
    "COMMUNITY_USERS",
    "DEMO_USERS",
    "DIFFICULTIES",
    "FEATURED_INTERESTS",
    "INTERESTS",
    "MAJORS",
    "PROJECTS",
    "TIMEFRAME_OPTIONS",
    "USERS",
    "project",
]
