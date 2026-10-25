"""Community project starters seeded into Wonderland: fictional students' developed ideas in
the same ProjectPlan shape the Caterpillar produces. Written by the team (labeled 'authored');
links are the documentation home pages already used in the catalog."""

from .projects_a import ARDUINO_START, FREECAD, GITHUB, MDN_JS, PY_VENV, TINKERCAD
from .projects_b import MATPLOTLIB, OPENCV_PY, PUBCHEM, SCIPY_STATS
from .projects_c import NUMPY_RANDOM, PANDAS


def _res(doc, kind="documentation"):
    slug, title, url, provider, tags = doc
    return {
        "id": f"starter/{slug}",
        "title": title,
        "url": url,
        "kind": kind,
        "provider": provider,
        "topic_tags": list(tags),
        "verification_status": "provided_unverified",
        "content_excerpt": None,
        "metadata": {},
        "source": "authored",
        "thumbnail_url": None,
    }


def _material(name, purpose, cost, quantity=None):
    return {"name": name, "purpose": purpose, "quantity": quantity, "estimated_cost_usd": cost}


VSCODE = _material("VS Code (free)", "Editing and running code", 0.0)
PYTHON = _material("Python 3 with a virtual environment", "Scripts and analysis", 0.0)


def starter(
    *,
    author: str,
    created_at: str,
    name: str,
    summary: str,
    deliverable: str,
    majors: list[str],
    interests: list[str],
    difficulty: str,
    hours: float,
    milestones: list[tuple[str, str, float]],
    materials: list[dict],
    software: list[dict],
    resources: list[dict],
    customization: list[str],
    first_action: str,
    pitch: str,
    assumptions: list[str] | None = None,
) -> dict:
    """A seeded starter post. milestones: (title, objective, hours); hours must sum to hours."""
    assert abs(sum(h for _, _, h in milestones) - hours) < 0.01, name
    weeks = max(1, round(hours / 6))
    per_week = round(hours / weeks, 1)
    plan = {
        "name": name,
        "summary": summary,
        "associated_majors": majors,
        "interests": interests,
        "difficulty": difficulty,
        "difficulty_assumptions": [],
        "deliverable": deliverable,
        "learning_objectives": [f"Apply {i} in a finished build" for i in interests[:3]],
        "prerequisites": ["Read the first milestone before buying anything."],
        "estimated_total_hours": hours,
        "suggested_schedule": [
            {"week": w, "focus": milestones[min(w - 1, len(milestones) - 1)][0], "hours": per_week}
            for w in range(1, weeks + 1)
        ],
        "estimated_cost_usd": sum(m["estimated_cost_usd"] or 0 for m in materials),
        "materials": materials,
        "software": software,
        "milestones": [
            {
                "title": title,
                "objective": objective,
                "steps": [objective],
                "expected_output": f"{title} is done and shown to a friend.",
                "definition_of_done": "You can demo this step in under two minutes.",
                "pitfalls": [],
                "estimated_hours": h,
                "resource_ids": [],
            }
            for title, objective, h in milestones
        ],
        "customization_ideas": customization,
        "success_criteria": [
            "Every milestone's definition of done is met.",
            "A two-minute demo works.",
        ],
        "first_action": first_action,
        "scope_adjustments": [],
        "constraint_warnings": [],
        "assumptions": assumptions
        or ["Written by the student with the Caterpillar; hours are estimates."],
        "suggested_search_queries": [],
        "resources": resources,
        "research_connections": [],
        "similar_examples": [],
        "guidance_note": "A community starter: a developed idea, not a sourced tutorial.",
    }
    return {
        "author": author,
        "created_at": created_at,
        "payload": {
            "plan": plan,
            "original_idea": pitch,
            "generation_mode": "authored",
            "web_results": [],
        },
    }


STARTERS: tuple[dict, ...] = (
    starter(
        author="priya_bme",
        created_at="2026-10-18 19:40:00",
        name="Grip Strength Tracker with a Load Cell",
        summary="A hand-held grip meter built from a 20 kg load cell and an HX711 amplifier that logs "
        "every squeeze to a phone-friendly chart, for tracking rehab progress week to week.",
        deliverable="A 3D-printed handle with a load cell inside, an Arduino reading it, and a chart of "
        "daily max grip force over two weeks.",
        majors=["Biomedical Engineering"],
        interests=["sensors", "health", "3d printing", "data visualization"],
        difficulty="intermediate",
        hours=25,
        milestones=[
            (
                "Read the load cell",
                "Wire the HX711, calibrate with known weights, print newtons.",
                6,
            ),
            (
                "Print the handle",
                "Design a two-part handle that squeezes the cell in Tinkercad.",
                7,
            ),
            ("Log sessions", "Save each squeeze with a timestamp to a CSV on a microSD card.", 6),
            ("Chart progress", "Plot daily max and average force; test with three people.", 6),
        ],
        materials=[
            _material("20 kg load cell with HX711 amplifier", "Force sensing", 9.0, "1"),
            _material("Arduino Nano", "Reads the amplifier", 8.0, "1"),
            _material("PLA filament", "Handle", 4.0, "about 120 g"),
            _material("MicroSD module and card", "Logging", 8.0, "1"),
        ],
        software=[VSCODE, PYTHON],
        resources=[_res(ARDUINO_START), _res(TINKERCAD), _res(MATPLOTLIB)],
        customization=[
            "Add a Bluetooth module and chart on a phone instead of a card.",
            "Compare dominant and non-dominant hands.",
            "Add a target line and a buzzer when the student beats last week.",
        ],
        first_action="Order the load cell kit and print a test handle at 70% scale tonight.",
        pitch="A cheap grip strength meter so I can track my wrist rehab at home.",
    ),
    starter(
        author="diego_builds",
        created_at="2026-10-19 10:15:00",
        name="Printed Phone Tripod with Tool-Free Hinges",
        summary="A folding phone tripod printed in two pieces with snap-fit, tool-free hinges, tested "
        "for how much it can hold before the hinges slip.",
        deliverable="A tripod that folds flat, holds a phone in landscape and portrait, and a table of "
        "hinge designs against slip load.",
        majors=["Mechanical Engineering"],
        interests=["3d printing", "mechanics"],
        difficulty="beginner",
        hours=10,
        milestones=[
            ("Model the hinge", "Design a snap-fit hinge with 0.3 mm clearance in FreeCAD.", 3),
            ("Print and test", "Print three hinge variants; load each until it slips.", 3),
            ("Assemble", "Print the legs and clamp; fold and unfold it 50 times.", 2),
            ("Document", "Photograph the build and write the hinge comparison.", 2),
        ],
        materials=[_material("PETG filament", "All parts", 6.0, "about 200 g")],
        software=[
            {
                "name": "FreeCAD (free)",
                "purpose": "CAD",
                "quantity": None,
                "estimated_cost_usd": 0.0,
            }
        ],
        resources=[_res(FREECAD), _res(TINKERCAD)],
        customization=[
            "Add a cold-shoe mount for a small light.",
            "Scale the clamp for a tablet.",
            "Try TPU for the hinge pins.",
        ],
        first_action="Measure your phone and print one hinge pair before designing anything else.",
        pitch="A phone tripod I can print in one evening that actually folds.",
    ),
    starter(
        author="hana_bio",
        created_at="2026-10-19 16:05:00",
        name="Pollinator Visit Counts on Campus Flower Beds",
        summary="Ten-minute counts of bees, butterflies and flies on three flower beds, repeated over "
        "two weeks, to see which plantings pull the most pollinators.",
        deliverable="A dataset of 30 counts and a chart of visits per bed and per time of day, with "
        "photos of the top five visitors identified on iNaturalist.",
        majors=["Biology"],
        interests=["ecology", "plants", "data visualization"],
        difficulty="beginner",
        hours=12,
        milestones=[
            ("Pick the beds", "Choose three beds with different plantings; map them.", 2),
            ("Count", "Ten-minute counts at 10 am and 3 pm on five days each.", 5),
            ("Identify", "Photograph and identify the common visitors.", 2),
            ("Chart", "Visits per bed and per hour; write what differed.", 3),
        ],
        materials=[_material("Notebook, timer and a phone camera", "Field work", 0.0)],
        software=[PYTHON],
        resources=[_res(MATPLOTLIB), _res(SCIPY_STATS)],
        customization=[
            "Add weather and temperature to each count.",
            "Compare native and ornamental beds.",
            "Repeat in spring for a seasonal comparison.",
        ],
        first_action="Walk campus tomorrow and photograph three beds that are in bloom.",
        pitch="Which flower beds on campus do the bees actually like?",
    ),
    starter(
        author="sam_chem",
        created_at="2026-10-20 11:20:00",
        name="Homemade Colorimeter for Water Hardness",
        summary="An LED-and-photodiode colorimeter in a small box that measures calcium hardness with "
        "an EDTA indicator, calibrated against a commercial test kit.",
        deliverable="A working colorimeter, a calibration curve from five standards, and hardness "
        "readings for tap water from three buildings.",
        majors=["Chemistry"],
        interests=["chemistry lab", "optics", "water", "sensors"],
        difficulty="intermediate",
        hours=30,
        milestones=[
            (
                "Build the optics",
                "LED, cuvette holder and photodiode in a dark box; read it on an Arduino.",
                8,
            ),
            ("Standards", "Make five calcium standards and run the indicator reaction.", 8),
            ("Calibrate", "Plot absorbance against concentration; fit the line.", 6),
            ("Measure", "Test tap water from three buildings against a commercial kit.", 8),
        ],
        materials=[
            _material("Green LED and photodiode", "Light source and detector", 4.0, "1 each"),
            _material("Plastic cuvettes", "Samples", 8.0, "10"),
            _material("Water hardness test kit (reference)", "Comparison", 15.0, "1"),
            _material("Arduino Uno", "Reads the photodiode", 20.0, "1"),
        ],
        software=[PYTHON],
        resources=[_res(PUBCHEM), _res(ARDUINO_START), _res(MATPLOTLIB)],
        customization=[
            "Swap the indicator to measure nitrate instead.",
            "Add a second LED color and compare sensitivity.",
            "Replace the Arduino with a phone camera and app.",
        ],
        first_action="Ask the stockroom for EDTA indicator and five cuvettes; wire the LED tonight.",
        pitch="Can I build a colorimeter good enough to measure water hardness in the dorms?",
    ),
    starter(
        author="lin_math",
        created_at="2026-10-20 21:00:00",
        name="Simulating Queue Times at the Dining Hall",
        summary="Record arrival and service times at one dining hall line for a week, fit the "
        "distributions, and simulate how an extra register or a faster scanner changes the wait.",
        deliverable="A simulation notebook with the fitted model, validated against the real waits, and "
        "a chart of wait time against number of registers.",
        majors=["Mathematics"],
        interests=["simulation", "statistics", "probability", "python"],
        difficulty="intermediate",
        hours=35,
        milestones=[
            ("Collect", "Time arrivals and service at the busiest hour for five days.", 8),
            ("Fit", "Fit arrival and service distributions; check them visually.", 7),
            ("Simulate", "Build a discrete-event simulation; validate against observed waits.", 12),
            ("Experiment", "Add a register, speed the scanner; chart the effect.", 8),
        ],
        materials=[_material("Stopwatch app and a notebook", "Timing", 0.0)],
        software=[PYTHON, VSCODE],
        resources=[_res(NUMPY_RANDOM), _res(PANDAS), _res(SCIPY_STATS)],
        customization=[
            "Model two lines with jockeying between them.",
            "Add a lunch-rush arrival curve instead of a flat rate.",
            "Estimate the cost of an extra register against minutes saved.",
        ],
        first_action="Stand in the dining hall at noon tomorrow with a stopwatch for 30 minutes.",
        pitch="How many registers would the dining hall need so nobody waits more than five minutes?",
        assumptions=["Arrivals are roughly Poisson at a fixed hour; checked in milestone 2."],
    ),
    starter(
        author="omar_phys",
        created_at="2026-10-21 08:30:00",
        name="Measuring the Moon's Distance with Two Phones",
        summary="Two friends hundreds of kilometres apart photograph the Moon against the stars at the "
        "same second; the parallax between the two photos gives the Moon's distance.",
        deliverable="Two synchronized photos, the measured parallax angle, and a distance estimate with "
        "an uncertainty compared to the true value that night.",
        majors=["Physics"],
        interests=["astronomy", "optics"],
        difficulty="advanced",
        hours=60,
        milestones=[
            (
                "Plan the night",
                "Pick a date with the Moon near a bright star; find a partner far away.",
                8,
            ),
            ("Rehearse", "Practice synchronized photos with a tripod and a timer app.", 12),
            ("Shoot", "Take the paired photos; record GPS positions and exact times.", 10),
            (
                "Measure",
                "Measure the Moon's shift against the stars in pixels, convert to angle.",
                18,
            ),
            ("Compute", "Distance from baseline and angle; compare to the ephemeris value.", 12),
        ],
        materials=[
            _material("Two phones or cameras with tripods", "Imaging", 0.0, "2"),
            _material("A partner at least 500 km away", "Baseline", 0.0, "1"),
        ],
        software=[
            PYTHON,
            {
                "name": "Stellarium (free)",
                "purpose": "Planning and star positions",
                "quantity": None,
                "estimated_cost_usd": 0.0,
            },
        ],
        resources=[_res(OPENCV_PY), _res(MATPLOTLIB)],
        customization=[
            "Repeat at perigee and apogee to see the distance change.",
            "Use a planet instead of the Moon for a harder measurement.",
            "Automate the star matching with OpenCV.",
        ],
        first_action="Find a date in the next month when the Moon passes close to a bright star.",
        pitch="Can two phones measure how far away the Moon is?",
        assumptions=["Both cameras can record exposure time to the second."],
    ),
    starter(
        author="rosa_env",
        created_at="2026-10-21 17:45:00",
        name="Storm Drain Litter Audit and Map",
        summary="Walk every storm drain on campus, photograph and categorize the litter at each, and "
        "publish a map that shows where cigarette butts, wrappers and plastics collect.",
        deliverable="A map of 40+ drains colored by litter count, a category breakdown, and a one-page "
        "note for facilities on the three worst spots.",
        majors=["Environmental Science"],
        interests=["water", "sustainability", "maps", "data visualization"],
        difficulty="beginner",
        hours=12,
        milestones=[
            ("Map the drains", "Walk campus with a GPS app; drop a pin at every drain.", 3),
            ("Audit", "Count and categorize litter at each drain; photograph it.", 5),
            ("Map it", "Color the pins by count on a web map.", 2),
            ("Report", "Write the one-page note with the three worst spots.", 2),
        ],
        materials=[_material("Gloves, a litter picker and a phone", "Field work", 12.0)],
        software=[PYTHON],
        resources=[_res(MDN_JS), _res(GITHUB)],
        customization=[
            "Repeat after a football game to see the spike.",
            "Add rainfall to see what washes in.",
            "Pair with a creek microplastics survey downstream.",
        ],
        first_action="Install a GPS pin app and walk one block of campus this afternoon.",
        pitch="Where does campus litter actually end up before it reaches the creek?",
    ),
    starter(
        author="kai_cs",
        created_at="2026-10-22 13:10:00",
        name="Pixel Art Game with a Learning Opponent",
        summary="A small browser game (a two-player grid duel) where the opponent is a Q-learning agent "
        "trained in the browser, so players can watch it get better as they play.",
        deliverable="A playable web game with a trained opponent, a difficulty slider that changes the "
        "training budget, and a chart of the agent's win rate over episodes.",
        majors=["Computer Science"],
        interests=["games", "machine learning", "web apps"],
        difficulty="advanced",
        hours=60,
        milestones=[
            ("Build the game", "A grid duel playable by two humans in the browser.", 15),
            ("Random opponent", "Replace player two with a random agent; log outcomes.", 8),
            ("Q-learning", "Implement tabular Q-learning; train for 10,000 episodes.", 20),
            ("Watch it learn", "Chart win rate during training; add a difficulty slider.", 10),
            ("Polish", "Pixel art, sounds, and a short write-up of what the agent learned.", 7),
        ],
        materials=[_material("Laptop with a modern browser", "Everything runs client-side", 0.0)],
        software=[VSCODE],
        resources=[_res(MDN_JS), _res(GITHUB), _res(PY_VENV)],
        customization=[
            "Swap tabular Q-learning for a tiny neural network.",
            "Let two agents train against each other.",
            "Add a replay viewer for the agent's best games.",
        ],
        first_action="Sketch the grid rules on paper and build the two-human version first.",
        pitch="A game where the AI opponent visibly learns while you play.",
    ),
)

STARTER_COMMENTS: tuple[tuple[int, str, str, str], ...] = (
    # (starter index, author, body, created_at)
    (0, "alex_demo", "The HX711 drifts with temperature; let it warm up for a minute before calibrating.", "2026-10-19 09:10:00"),
    (2, "maya_demo", "If you export the counts as CSV I can help chart them by hour.", "2026-10-20 12:30:00"),
    (4, "maya_demo", "This is basically my bus-stop statistics project but for food. Want to compare notes?", "2026-10-21 19:05:00"),
    (7, "alex_demo", "Could the agent run on an ESP32 with a tiny display? Would love a handheld version.", "2026-10-23 15:40:00"),
)  # fmt: skip
