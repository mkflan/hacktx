"""Fictional in-memory development fixtures. NOT database seeds; responses say data_source=fake.

Resource policy: URLs are real public documentation pages that returned HTTP 200 when these
fixtures were written (2026-10-24). That checks the link, not the content, so every resource is
still provided_unverified. Text guides have url=None. No research papers are included because
none were supplied; plans built from fixtures report that honestly.
"""

from ..contracts import NormalizedProject, NormalizedUser, Resource, TimeValue

ALEX = NormalizedUser(
    id="fixture-ece",
    username="alex_demo",
    major="Electrical and Computer Engineering",
    interests=("sensors", "plants", "sustainability"),
    time_commitment=TimeValue(amount=12, unit="total_hours", raw="12 total hours"),
)

MAYA = NormalizedUser(
    id="fixture-cs",
    username="maya_demo",
    major="Computer Science",
    interests=("language learning", "web apps", "data visualization"),
    time_commitment=TimeValue(amount=20, unit="total_hours", raw="20 total hours"),
)

FIXTURE_USERS = (ALEX, MAYA)

_ARDUINO = Resource(
    id="proj-soil-moisture/arduino-getting-started",
    title="Getting Started with Arduino",
    url="https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/",
    kind="documentation",
    provider="Arduino",
    topic_tags=("arduino", "microcontroller", "sensors"),
)

FIXTURE_PROJECTS = (
    NormalizedProject(
        id="proj-soil-moisture",
        name="Smart Soil Moisture Monitor",
        associated_majors=("Electrical and Computer Engineering",),
        interests=("sensors", "plants", "IoT"),
        timeline=TimeValue(amount=10, unit="total_hours", raw="10 total hours"),
        difficulty="beginner",
        description="Read a soil moisture sensor with a microcontroller and alert when a "
        "plant needs water.",
        resources=(
            _ARDUINO,
            Resource(
                id="proj-soil-moisture/wiring-notes",
                title="Wiring notes for an analog moisture sensor",
                kind="guide",
                topic_tags=("sensors", "wiring"),
                content_excerpt="Power the sensor from 3.3 V, read the analog pin, and record "
                "dry and wet readings to calibrate thresholds.",
            ),
        ),
    ),
    NormalizedProject(
        id="proj-solar-logger",
        name="Solar Panel Output Logger",
        associated_majors=("Electrical and Computer Engineering", "Mechanical Engineering"),
        interests=("sustainability", "energy", "sensors"),
        timeline=TimeValue(amount=12, unit="total_hours", raw="12 total hours"),
        difficulty="intermediate",
        description="Measure a small solar panel's voltage and current over a day and chart it.",
        resources=(
            Resource(
                id="proj-solar-logger/measurement-guide",
                title="Measuring panel voltage and current safely",
                kind="guide",
                topic_tags=("energy", "measurement"),
                content_excerpt="Use a voltage divider for the ADC and a shunt or current sensor "
                "module; log a reading every minute.",
            ),
        ),
    ),
    NormalizedProject(
        id="proj-greenhouse-climate",
        name="Mini Greenhouse Climate Controller",
        associated_majors=("Electrical and Computer Engineering", "Mechanical Engineering"),
        interests=("plants", "sensors", "automation"),
        # Weeks-only timeline: a calendar span with no workload estimate.
        timeline=TimeValue(amount=6, unit="weeks", raw="6 weeks"),
        difficulty=None,
        description="Keep a small enclosure within a temperature and humidity range.",
        resources=(),
    ),
    NormalizedProject(
        id="proj-water-quality",
        name="Water Quality Sensor Buoy",
        associated_majors=("Electrical and Computer Engineering", "Environmental Engineering"),
        interests=("sustainability", "sensors", "water"),
        timeline=TimeValue(amount=30, unit="total_hours", raw="30 total hours"),
        difficulty="advanced",
        description="A floating sensor package that logs temperature and turbidity.",
        resources=(),
    ),
    NormalizedProject(
        id="proj-vocab-app",
        name="Spaced-Repetition Vocabulary Web App",
        associated_majors=("Computer Science",),
        interests=("language learning", "web apps"),
        timeline=TimeValue(amount=16, unit="total_hours", raw="16 total hours"),
        difficulty="beginner",
        description="A browser flashcard app that schedules reviews and saves progress locally.",
        resources=(
            Resource(
                id="proj-vocab-app/mdn-web-storage",
                title="Web Storage API",
                url="https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API",
                kind="documentation",
                provider="MDN",
                topic_tags=("web apps", "javascript", "storage"),
            ),
            Resource(
                id="proj-vocab-app/scheduling-notes",
                title="Simple review scheduling",
                kind="guide",
                topic_tags=("language learning", "algorithms"),
                content_excerpt="Start with fixed intervals (1, 3, 7, 14 days) and move a card "
                "back to day 1 when it is missed.",
            ),
        ),
    ),
    NormalizedProject(
        id="proj-lang-dashboard",
        name="Language Learning Progress Dashboard",
        associated_majors=("Computer Science",),
        interests=("data visualization", "language learning"),
        timeline=TimeValue(amount=18, unit="total_hours", raw="18 total hours"),
        difficulty="intermediate",
        description="Chart study streaks and accuracy from an exported study log.",
        resources=(
            Resource(
                id="proj-lang-dashboard/d3-getting-started",
                title="Getting started with D3",
                url="https://d3js.org/getting-started",
                kind="documentation",
                provider="D3",
                topic_tags=("data visualization", "javascript"),
            ),
        ),
    ),
    NormalizedProject(
        id="proj-campus-air",
        name="Campus Air Quality Map",
        associated_majors=("Computer Science", "Electrical and Computer Engineering"),
        interests=("data visualization", "sensors", "sustainability"),
        timeline=TimeValue(amount=24, unit="total_hours", raw="24 total hours"),
        difficulty="advanced",
        description="Collect air quality readings around campus and show them on a web map.",
        resources=(
            Resource(
                id="proj-campus-air/leaflet-reference",
                title="Leaflet API reference",
                url="https://leafletjs.com/reference.html",
                kind="documentation",
                provider="Leaflet",
                topic_tags=("maps", "data visualization", "web apps"),
            ),
        ),
    ),
    NormalizedProject(
        id="proj-phrasebook-chat",
        name="Phrasebook Chat Helper",
        associated_majors=("Computer Science", "Linguistics"),
        interests=("language learning", "chatbots"),
        timeline=TimeValue(raw="a few weekends", unit="unknown"),
        difficulty="intermediate",
        description="A rule-based chat helper that practices travel phrases.",
        resources=(),
    ),
    NormalizedProject(
        id="proj-bike-mount",
        name="3D-Printed Bike Accessory Mount",
        associated_majors=("Mechanical Engineering",),
        interests=("3d printing", "cycling"),
        timeline=TimeValue(amount=8, unit="total_hours", raw="8 total hours"),
        difficulty="beginner",
        description="Design and print a handlebar mount and test how much load it holds.",
        resources=(
            Resource(
                id="proj-bike-mount/print-checklist",
                title="Print settings checklist",
                kind="guide",
                topic_tags=("3d printing",),
                content_excerpt="Print a small test section first; orient layers across the "
                "load direction.",
            ),
        ),
    ),
    NormalizedProject(
        id="proj-recipe-scaler",
        name="Recipe Scaling Command-Line Tool",
        associated_majors=("Mathematics",),
        interests=("cooking", "command line tools"),
        timeline=TimeValue(amount=5, unit="total_hours", raw="5 total hours"),
        difficulty="beginner",
        description=None,
        resources=(
            Resource(
                id="proj-recipe-scaler/python-argparse",
                title="argparse: command-line parsing",
                url="https://docs.python.org/3/library/argparse.html",
                kind="documentation",
                provider="Python",
                topic_tags=("python", "command line tools"),
            ),
        ),
    ),
)
