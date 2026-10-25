"""Catalog part C: Mathematics, Physics, Environmental Science."""

from .projects_a import ARDUINO_ANALOG, ARDUINO_START, MICROPYTHON_ESP32, PY_VENV
from .projects_b import MATPLOTLIB
from .vocab import project

MATH = "Mathematics"
PHYS = "Physics"
ENV = "Environmental Science"
CS = "Computer Science"
ECE = "Electrical and Computer Engineering"

NUMPY_RANDOM = ("numpy-random", "NumPy random sampling", "https://numpy.org/doc/stable/reference/random/index.html", "NumPy", ("python", "probability"))  # fmt: skip
PANDAS = ("pandas-docs", "pandas documentation", "https://pandas.pydata.org/docs/", "pandas", ("python", "statistics"))  # fmt: skip

PROJECTS: tuple[dict, ...] = (
    # ------------------------------------------------------------------------- Mathematics
    project(
        "recipe-scaler-cli",
        "Recipe Scaling Command-Line Tool",
        majors=(MATH,),
        interests=("cooking", "command line tools", "python"),
        difficulty="beginner",
        hours=5,
        description="A command-line tool that scales a recipe to any number of servings, "
        "converting units and keeping fractions readable.",
        start=(
            "Create the repository and a virtual environment; write scale.py with argparse.",
            "Parse lines like '1 1/2 cups flour' into quantity, unit and ingredient.",
            "Store every quantity in grams or milliliters; convert back for display.",
            "Scale by a factor and print readable fractions (1/3, 2/3) with the fractions module.",
            "Add tests for the tricky lines (ranges, 'a pinch', missing units).",
        ),
        materials=(("Laptop with Python 3", "1", "Everything is local", 0),),
        guides=(
            (
                "units-notes",
                "Unit conversion is the real problem",
                "Store every ingredient in grams or milliliters internally and convert for "
                "display; fractions like 1/3 cup need a tolerant parser and a limit on the "
                "denominator when printing.",
                ("command line tools",),
            ),
        ),
        docs=(
            (
                "python-argparse",
                "argparse: command-line parsing",
                "https://docs.python.org/3/library/argparse.html",
                "Python",
                ("python", "command line tools"),
            ),  # fmt: skip
            (
                "python-fractions",
                "fractions: rational numbers",
                "https://docs.python.org/3/library/fractions.html",
                "Python",
                ("python",),
            ),  # fmt: skip
        ),
    ),
    project(
        "monte-carlo-estimators",
        "Monte Carlo Estimation of Pi and Beyond",
        majors=(MATH,),
        interests=("probability", "simulation", "statistics", "python"),
        difficulty="beginner",
        hours=8,
        description="Estimate pi, an integral and the birthday-problem probability by random "
        "sampling, and show how the error shrinks with the sample count.",
        start=(
            "Sample random points in a square; estimate pi from the fraction inside the circle.",
            "Run 10^2 to 10^6 samples; plot absolute error against N on log-log axes.",
            "Estimate the integral of e^(-x^2) on [0, 1] the same way; compare with SciPy.",
            "Simulate the birthday problem for 23 people; compare with the exact value.",
            "Write up the 1/sqrt(N) slope and what it means for simulations in general.",
        ),
        materials=(("Laptop with Python 3", "1", "NumPy and Matplotlib", 0),),
        guides=(
            (
                "convergence-notes",
                "Plot the error, not just the estimate",
                "Run 10^2 to 10^6 samples and plot absolute error on a log-log chart; the slope "
                "near -1/2 is the lesson. Use a fixed random seed so the chart is reproducible.",
                ("probability", "simulation"),
            ),
        ),
        docs=(NUMPY_RANDOM, MATPLOTLIB),
    ),
    project(
        "bus-arrival-statistics",
        "Campus Bus Arrival Time Statistics",
        majors=(MATH,),
        interests=("statistics", "data visualization", "transportation", "python"),
        difficulty="intermediate",
        hours=25,
        description="Record real bus arrivals at one stop, fit waiting-time distributions, and "
        "show when it is worth walking instead of waiting.",
        start=(
            "Pick one stop; record arrival times for 10 days (by hand or from the agency's "
            "real-time feed).",
            "Compute headways; plot their histogram and fit an exponential and a gamma.",
            "Compute the expected wait from your data and from E[W] = E[T^2] / (2 E[T]).",
            "Compare the wait with the walking time to the next stop or destination.",
            "Build a one-page chart: 'walk if the wait is above X minutes at this hour'.",
        ),
        materials=(
            ("Laptop with Python 3", "1", "Analysis", 0),
            ("Public transit schedule or real-time feed (GTFS)", None, "Data source", 0),
        ),
        guides=(
            (
                "inspection-paradox",
                "Why your wait feels longer than the schedule",
                "If buses arrive every 10 minutes on average but with variance, the average wait "
                "is longer than 5 minutes. Compute it from your data and from the formula "
                "E[W] = E[T^2] / (2 E[T]).",
                ("statistics", "transportation"),
            ),
        ),
        docs=(
            PANDAS,
            (
                "gtfs",
                "GTFS: General Transit Feed Specification",
                "https://gtfs.org/",
                "MobilityData",
                ("transportation",),
            ),  # fmt: skip
        ),
    ),
    project(
        "campus-epidemic-model",
        "Epidemic Model on a Campus Social Graph",
        majors=(MATH,),
        interests=("simulation", "health", "networks", "python"),
        difficulty="intermediate",
        hours=40,
        description="Fit a basic SIR model, then run the same outbreak on a synthetic campus "
        "contact network and compare the two curves.",
        start=(
            "Solve the SIR equations with SciPy; plot S, I and R for a few R0 values.",
            "Build a synthetic contact graph (dorms, classes, clubs) with NetworkX.",
            "Simulate the same R0 on the graph with a stochastic SIR; run 100 trials.",
            "Compare the ODE curve with the network's mean and spread.",
            "Test one intervention (vaccinate the top-degree 5%) and report the change.",
            "Write up why the two models disagree and which to trust for what.",
        ),
        materials=(("Laptop with Python 3", "1", "NetworkX, SciPy, Matplotlib", 0),),
        guides=(
            (
                "sir-notes",
                "Compare the ODE with the network",
                "Fit the basic SIR model first, then run the same R0 on a synthetic contact "
                "graph; the difference between the two curves is the result to present.",
                ("simulation", "networks"),
            ),
        ),
        docs=(
            (
                "networkx-docs",
                "NetworkX documentation",
                "https://networkx.org/documentation/stable/",
                "NetworkX",
                ("networks", "python"),
            ),  # fmt: skip
            (
                "scipy-integrate",
                "SciPy integrate (ODE solvers)",
                "https://docs.scipy.org/doc/scipy/reference/integrate.html",
                "SciPy",
                ("simulation", "python"),
            ),  # fmt: skip
        ),
    ),
    project(
        "markov-music-generator",
        "Markov Chain Music Generator",
        majors=(MATH, CS),
        interests=("music", "probability", "python", "art"),
        difficulty="intermediate",
        hours=30,
        description="Train a Markov chain on public-domain MIDI files of one composer and "
        "generate new melodies; compare orders 1 to 4 by ear and by a plagiarism statistic.",
        start=(
            "Collect 20 public-domain MIDI files of one composer; hold out 5 as a test set.",
            "Parse notes with music21 into (pitch, duration) states.",
            "Build order-1 to order-4 transition tables; generate 16-bar melodies from each.",
            "Measure how often each order reproduces 8-note runs from the training set verbatim.",
            "Export the melodies as MIDI; run a small listening survey with classmates.",
            "Write up the trade-off between order, novelty and 'sounds like music'.",
        ),
        materials=(
            ("Laptop with Python 3", "1", "music21 and a MIDI player", 0),
            ("Public-domain MIDI files", "20", "Training data", 0),
        ),
        guides=(
            (
                "order-notes",
                "Order 2 or 3 sounds like music",
                "Order 1 wanders, order 5 copies the training piece. Encode (pitch, duration) "
                "pairs as states and keep a test set out to measure how often the model "
                "reproduces 8-note runs verbatim.",
                ("music", "probability"),
            ),
        ),
        docs=(
            (
                "music21-docs",
                "music21 documentation",
                "https://www.music21.org/music21docs/",
                "music21",
                ("music", "python"),
            ),  # fmt: skip
        ),
    ),
    project(
        "toy-rsa-attacks",
        "Implement and Attack Toy RSA",
        majors=(MATH,),
        interests=("cybersecurity", "probability", "python"),
        difficulty="advanced",
        hours=60,
        description="Implement RSA from scratch with small keys, then break your own keys with "
        "factoring, common-modulus and low-exponent attacks to see why real parameters matter.",
        start=(
            "Implement key generation, encryption and decryption with Python integers.",
            "Generate 32-bit keys and break them by trial division and Pollard's rho.",
            "Implement the common-modulus attack and the low public exponent (e = 3) attack.",
            "Add Fermat factoring for primes that are too close together.",
            "For each attack, state the parameter rule that defeats it; verify with larger keys.",
            "Write a report with the math and timing charts for each attack.",
        ),
        materials=(("Laptop with Python 3", "1", "SymPy for primes and number theory", 0),),
        guides=(
            (
                "ethics-notes",
                "Attack only keys you generated",
                "Every attack runs on keys from your own code. Document each attack with the "
                "math that makes it work and the parameter choice that prevents it.",
                ("cybersecurity",),
            ),
        ),
        docs=(
            (
                "sympy-ntheory",
                "SymPy number theory",
                "https://docs.sympy.org/latest/modules/ntheory.html",
                "SymPy",
                ("python", "probability"),
            ),  # fmt: skip
            (
                "python-pow",
                "pow() with a modulus",
                "https://docs.python.org/3/library/functions.html#pow",
                "Python",
                ("python",),
            ),  # fmt: skip
        ),
    ),
    # ----------------------------------------------------------------------------- Physics
    project(
        "phone-pendulum-period",
        "Pendulum Period vs Length with a Phone Sensor",
        majors=(PHYS,),
        interests=("mechanics", "sensors", "education", "data visualization"),
        difficulty="beginner",
        hours=6,
        description="Swing a phone as a pendulum, log its accelerometer with a free app, and "
        "measure g from the period-length relation.",
        start=(
            "Install phyphox; hang the phone in a small bag on a string from a door frame.",
            "Record the accelerometer for 10 swings at five string lengths.",
            "Read the period from the peaks; average the swings.",
            "Plot T^2 against L; fit a line and compute g from the slope.",
            "Report g with an uncertainty from the fit and compare with 9.81.",
        ),
        materials=(
            ("Smartphone with the phyphox app", "1", "Sensor logging", 0),
            ("String, tape and a small bag", "1 set", "The pendulum", 5),
            ("Tape measure", "1", "Length", 5),
        ),
        guides=(
            (
                "fit-notes",
                "Fit T squared against L",
                "Plot period squared against length; the slope is 4 pi^2 / g. Five lengths with "
                "three swings each is enough to get g within 2%.",
                ("mechanics", "statistics"),
            ),
        ),
        docs=(
            (
                "phyphox",
                "phyphox: physical phone experiments",
                "https://phyphox.org/",
                "RWTH Aachen University",
                ("sensors", "education"),
            ),  # fmt: skip
        ),
    ),
    project(
        "speed-of-sound-arduino",
        "Speed of Sound Measurement with Arduino",
        majors=(PHYS, ECE),
        interests=("acoustics", "sensors", "embedded systems", "mechanics"),
        difficulty="beginner",
        hours=10,
        description="Use an ultrasonic sensor to time echoes at known distances and fit the "
        "speed of sound; then check it against the temperature formula.",
        start=(
            "Wire an HC-SR04 to the Arduino; print the echo time with pulseIn().",
            "Place a cardboard target at six measured distances; record 20 echoes at each.",
            "Fit distance against half the echo time; the slope is the speed of sound.",
            "Measure room temperature; compare with 331 + 0.6 T m/s.",
            "Repeat outdoors on a cold morning if you can; report the difference.",
        ),
        materials=(
            ("Arduino Uno", "1", "Timing", 20),
            ("HC-SR04 ultrasonic sensor", "1", "Echo timing", 3),
            ("Tape measure and a cardboard target", "1 each", "Distances", 5),
            ("Thermometer", "1", "Air temperature", 5),
        ),
        guides=(
            (
                "temperature-notes",
                "Sound speed depends on temperature",
                "Measure the echo time at six distances and fit distance against time; the slope "
                "is the speed of sound. Compare with 331 + 0.6 T m/s at your room temperature.",
                ("acoustics",),
            ),
        ),
        docs=(
            (
                "arduino-pulsein",
                "pulseIn() reference",
                "https://www.arduino.cc/reference/en/language/functions/advanced-io/pulsein/",
                "Arduino",
                ("embedded systems",),
            ),  # fmt: skip
            ARDUINO_START,
        ),
    ),
    project(
        "diy-spectroscope",
        "DIY Spectroscope for Lamp and Star Spectra",
        majors=(PHYS,),
        interests=("optics", "astronomy", "data visualization"),
        difficulty="intermediate",
        hours=25,
        description="Build a slit-and-grating spectroscope for a phone camera, calibrate it on "
        "a fluorescent lamp, and photograph the spectra of lamps and a bright star.",
        start=(
            "Build a tube with a 0.5 mm slit at one end and the grating at the other.",
            "Photograph a compact fluorescent lamp; identify the mercury lines.",
            "Calibrate pixel to wavelength with the 436 nm and 546 nm lines.",
            "Photograph an LED lamp and a sodium streetlight; plot their spectra.",
            "On a clear night, photograph Vega with a tripod and a 30 second exposure.",
            "Compare the lamp and star spectra and explain the differences.",
        ),
        materials=(
            ("Diffraction grating, 1000 lines/mm (or a blank DVD)", "1", "Splits light", 8),
            ("Cardboard tube, black tape and razor blades", "1 set", "Housing and slit", 8),
            ("Phone or DSLR camera with a tripod", "1", "Imaging", 0),
            ("Compact fluorescent lamp and an LED lamp", "1 each", "Calibration sources", 10),
        ),
        guides=(
            (
                "calibration-notes",
                "Calibrate with mercury lines",
                "Photograph a CFL first: its 436 nm and 546 nm lines set the wavelength scale. "
                "Then compare an LED, a sodium streetlight and, with a tripod, Vega.",
                ("optics", "astronomy"),
            ),
        ),
        docs=(
            (
                "nist-asd",
                "NIST Atomic Spectra Database",
                "https://www.nist.gov/pml/atomic-spectra-database",
                "NIST",
                ("optics",),
            ),  # fmt: skip
            MATPLOTLIB,
        ),
    ),
    project(
        "cosmic-ray-muon-counter",
        "Cosmic Ray Muon Counter",
        majors=(PHYS, ECE),
        interests=("astronomy", "sensors", "electronics", "embedded systems"),
        difficulty="advanced",
        hours=80,
        description="Build a two-detector coincidence counter from Geiger tubes or a "
        "scintillator kit and measure the muon rate against angle, shielding and altitude.",
        start=(
            "Assemble two Geiger counter kits (or a scintillator and SiPM kit); verify each counts.",
            "Feed both pulse outputs to a microcontroller; count coincidences within 1 us.",
            "Measure the coincidence rate for 24 hours; compare with the single-tube rates.",
            "Tilt the pair; measure the rate at 0, 30, 60 and 90 degrees.",
            "Add shielding (steel plates); measure the change.",
            "If you can, take it up a tall building or a mountain and record the altitude effect.",
        ),
        materials=(
            (
                "Two Geiger counter kits (SBM-20 tubes) or a scintillator plus SiPM kit",
                "2",
                "Detectors",
                120,
            ),  # fmt: skip
            ("Arduino or Raspberry Pi Pico", "1", "Coincidence counting", 10),
            ("Steel plates or lead bricks from the department", "several", "Shielding", 0),
            ("Enclosure and high-voltage safety gloves", "1 set", "Safety", 20),
        ),
        guides=(
            (
                "coincidence-notes",
                "Coincidence beats a single counter",
                "Two detectors 10 cm apart firing within a microsecond is almost always a muon; "
                "a single tube counts radon and background too. Expect about 1 count per cm^2 "
                "per minute at sea level.",
                ("astronomy", "sensors"),
            ),
        ),
        docs=(
            (
                "cosmicwatch",
                "CosmicWatch desktop muon detector",
                "http://www.cosmicwatch.lns.mit.edu/",
                "MIT",
                ("astronomy", "electronics"),
            ),  # fmt: skip
            ARDUINO_START,
        ),
    ),
    project(
        "maglev-controller",
        "Magnetic Levitation Controller",
        majors=(PHYS, ECE),
        interests=("control systems", "electronics", "simulation", "embedded systems"),
        difficulty="intermediate",
        hours=40,
        description="Levitate a small magnet under an electromagnet with a Hall sensor and a PID "
        "loop you tune yourself, then model the system and compare.",
        start=(
            "Mount the electromagnet pointing down with the Hall sensor under it.",
            "Drive the coil with a MOSFET from a PWM pin; read the Hall sensor at 1 kHz.",
            "Write a P controller; raise P until the magnet oscillates.",
            "Add D to damp the oscillation and a little I to remove the sag.",
            "Log the sensor at 1 kHz and plot it while tuning.",
            "Model the system (coil force vs current and gap) and compare the predicted gain.",
        ),
        materials=(
            ("12 V electromagnet or a hand-wound coil", "1", "Lifting force", 15),
            ("Linear Hall-effect sensor (SS49E)", "1", "Position", 3),
            ("Logic-level MOSFET and a 12 V supply", "1 each", "Coil driver", 12),
            ("Arduino Uno", "1", "Control loop", 20),
            ("Neodymium magnets", "5", "The levitated object", 8),
        ),
        guides=(
            (
                "pid-notes",
                "Tune P first",
                "Raise P until the magnet oscillates, then add D to damp it; a little I fixes "
                "the sag. Log the sensor at 1 kHz and plot it; you cannot tune what you cannot see.",
                ("control systems",),
            ),
        ),
        docs=(ARDUINO_ANALOG, ARDUINO_START),
    ),
    # --------------------------------------------------------------- Environmental Science
    project(
        "rain-barrel-water-quality",
        "Rain Barrel Water Quality Monitoring",
        majors=(ENV,),
        interests=("water", "sustainability", "sensors", "chemistry lab"),
        difficulty="beginner",
        hours=12,
        description="Sample a rain barrel after storms and dry spells and track pH, dissolved "
        "solids and nitrate against the rainfall record.",
        start=(
            "Find a rain barrel (or set up a bucket under a downspout); label six bottles.",
            "Sample after each rain and after three dry days for a month.",
            "Measure pH, TDS and nitrate; log them with the date and rainfall from a station.",
            "Plot each measure against days since rain.",
            "Write up whether the water is suitable for garden use and why.",
        ),
        materials=(
            ("Water test strips (pH, nitrate, hardness)", "1 pack", "Chemistry", 15),
            ("TDS meter", "1", "Dissolved solids", 12),
            ("Sample bottles", "6", "Collection", 8),
        ),
        guides=(
            (
                "sampling-notes",
                "Same time, same depth, labeled bottles",
                "Sample after each rain and after three dry days; log pH, TDS and nitrate with the "
                "date and the rainfall from the nearest weather station.",
                ("water",),
            ),
        ),
        docs=(
            (
                "usgs-water-data",
                "USGS Water Data for the Nation",
                "https://waterdata.usgs.gov/nwis",
                "USGS",
                ("water",),
            ),  # fmt: skip
        ),
    ),
    project(
        "tree-canopy-mapping",
        "Campus Tree Canopy Mapping with Satellite Imagery",
        majors=(ENV,),
        interests=("climate", "maps", "data visualization", "sustainability", "python"),
        difficulty="intermediate",
        hours=40,
        description="Compute NDVI from free Sentinel-2 imagery, map canopy cover over campus, "
        "and compare two summers.",
        start=(
            "Create a free Copernicus Data Space account; download two cloud-free Sentinel-2 "
            "scenes of campus from different years.",
            "Open bands 4 and 8 with rasterio; compute NDVI = (NIR - Red) / (NIR + Red).",
            "Threshold NDVI above 0.5 as canopy; compute canopy percentage inside the campus "
            "boundary.",
            "Validate 30 random points against Street View or a walk.",
            "Map the change between the two years; write what changed and where.",
        ),
        materials=(
            ("Laptop with Python 3", "1", "rasterio, numpy, matplotlib", 0),
            ("Copernicus Data Space account (free)", None, "Imagery", 0),
        ),
        guides=(
            (
                "ndvi-notes",
                "NDVI = (NIR - Red) / (NIR + Red)",
                "Use Sentinel-2 bands 8 and 4 at 10 m. Threshold NDVI above 0.5 as canopy and "
                "validate against 30 points you check on the ground or in Street View.",
                ("climate", "maps"),
            ),
        ),
        docs=(
            (
                "copernicus-dataspace",
                "Copernicus Data Space Ecosystem",
                "https://dataspace.copernicus.eu/",
                "ESA",
                ("climate", "maps"),
            ),  # fmt: skip
            (
                "rasterio-docs",
                "Rasterio documentation",
                "https://rasterio.readthedocs.io/en/stable/",
                "Rasterio",
                ("maps", "python"),
            ),  # fmt: skip
        ),
    ),
    project(
        "compost-temperature-logger",
        "Compost Temperature Logger",
        majors=(ENV,),
        interests=("sustainability", "sensors", "agriculture", "data visualization"),
        difficulty="beginner",
        hours=10,
        description="Log the temperature inside a compost pile every 10 minutes and chart the "
        "hot phase that tells you when to turn it.",
        start=(
            "Wire two DS18B20 probes to the Arduino; print both temperatures.",
            "Add a microSD module (or Wi-Fi logging on an ESP32); write a line every 10 minutes.",
            "Push one probe into the pile's center and one near the edge; run for two weeks.",
            "Chart both temperatures; mark when the center passes 55 C and when it drops.",
            "Turn the pile at the drop and watch the second rise; write up the timing.",
        ),
        materials=(
            ("Waterproof DS18B20 temperature probes (1 m)", "2", "Sensing", 10),
            ("Arduino Uno or ESP32", "1", "Logging", 12),
            ("MicroSD card module and card", "1", "Storage", 8),
            ("Access to a compost bin", "1", "The experiment", 0),
        ),
        guides=(
            (
                "phases-notes",
                "The thermophilic phase is the goal",
                "Log every 10 minutes; a healthy pile climbs past 55 C within days of turning. "
                "Chart the drop that tells you when to turn again.",
                ("sustainability", "agriculture"),
            ),
        ),
        docs=(ARDUINO_START, MICROPYTHON_ESP32),
    ),
    project(
        "creek-microplastics-survey",
        "Microplastics Survey of a Local Creek",
        majors=(ENV,),
        interests=("water", "sustainability", "ecology", "microbiology"),
        difficulty="intermediate",
        hours=30,
        description="Filter known volumes of creek water above and below a storm drain and "
        "count microplastic particles by type under a microscope.",
        start=(
            "Choose three sites: upstream, at and downstream of a storm drain outlet.",
            "Filter 10 L per sample through a 300 micron sieve; three replicates per site.",
            "Rinse the sieve contents into a petri dish; sort under a microscope.",
            "Count particles by type (fiber, fragment, film) per liter.",
            "Chart counts by site and type; write up sources you suspect and the method's limits.",
        ),
        materials=(
            ("300 micron sieve or plankton net", "1", "Filtering", 30),
            ("Sample jars, tweezers and petri dishes", "1 set", "Handling", 15),
            ("USB microscope or dissecting scope access", "1", "Counting", 40),
            ("Rubber boots and a measuring bucket", "1 each", "Field work", 20),
        ),
        guides=(
            (
                "protocol-notes",
                "Three sites, three replicates",
                "Sample upstream, mid and downstream of a storm drain; filter a known volume and "
                "count particles by type per liter. Wear cotton, not fleece, so you do not "
                "contaminate your own samples.",
                ("water", "ecology"),
            ),
        ),
        docs=(
            (
                "noaa-marine-debris",
                "NOAA Marine Debris Program",
                "https://marinedebris.noaa.gov/",
                "NOAA",
                ("water",),
            ),  # fmt: skip
        ),
    ),
    project(
        "urban-heat-island-network",
        "Urban Heat Island Sensor Network",
        majors=(ENV, ECE),
        interests=("climate", "sensors", "data visualization", "maps", "embedded systems"),
        difficulty="advanced",
        hours=90,
        description="Deploy six solar-powered temperature nodes across paved and green parts of "
        "campus and map the heat island through a week of days and nights.",
        start=(
            "Build one node: ESP32, BME280, solar panel, LiPo and a printed radiation shield.",
            "Send a reading every 5 minutes to a free MQTT broker; chart it live.",
            "Run one node for 48 hours; fix power and dropout problems.",
            "Build five more; mount all six at 2 m, shaded, away from walls and exhausts.",
            "Collect a week of data; map 3 pm and 3 am temperatures across campus.",
            "Write up the paved-versus-green difference and what it means for planting.",
        ),
        materials=(
            ("ESP32 development boards", "6", "Node controllers", 60),
            ("BME280 temperature, humidity and pressure sensors", "6", "Sensing", 30),
            ("Radiation shields (printed or stacked plates)", "6", "Keeps sun off the sensor", 20),
            ("2 W solar panels, LiPo batteries and charger boards", "6 sets", "Power", 90),
        ),
        guides=(
            (
                "siting-notes",
                "Siting matters more than the sensor",
                "Mount at 2 m, shaded, away from walls and exhausts; log every 5 minutes; compare "
                "paved against green sites at 3 pm and 3 am.",
                ("climate", "sensors"),
            ),
        ),
        docs=(
            (
                "adafruit-bme280",
                "Adafruit BME280 guide",
                "https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout",
                "Adafruit",
                ("sensors", "electronics"),
            ),  # fmt: skip
            MICROPYTHON_ESP32,
            PY_VENV,
        ),
    ),
)
