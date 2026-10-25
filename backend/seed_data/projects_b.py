"""Catalog part B: Biomedical Engineering, Biology, Chemistry."""

from .projects_a import ADAFRUIT_LEARN, ARDUINO_ANALOG, ARDUINO_START, MICROPYTHON_ESP32, TINKERCAD
from .vocab import project

BME = "Biomedical Engineering"
BIO = "Biology"
CHEM = "Chemistry"
ECE = "Electrical and Computer Engineering"
PHYS = "Physics"
ENV = "Environmental Science"

SCIPY_SIGNAL = ("scipy-signal", "SciPy signal processing", "https://docs.scipy.org/doc/scipy/reference/signal.html", "SciPy", ("signal processing", "python"))  # fmt: skip
SCIPY_STATS = ("scipy-stats", "SciPy statistical functions", "https://docs.scipy.org/doc/scipy/reference/stats.html", "SciPy", ("statistics", "python"))  # fmt: skip
OPENCV_PY = ("opencv-python-tutorials", "OpenCV-Python tutorials", "https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html", "OpenCV", ("computer vision", "python"))  # fmt: skip
MATPLOTLIB = ("matplotlib", "Matplotlib documentation", "https://matplotlib.org/stable/", "Matplotlib", ("data visualization", "python"))  # fmt: skip
PUBCHEM = ("pubchem", "PubChem", "https://pubchem.ncbi.nlm.nih.gov/", "NIH", ("chemistry lab",))  # fmt: skip

PROJECTS: tuple[dict, ...] = (
    # ------------------------------------------------------------- Biomedical Engineering
    project(
        "pulse-oximeter-explorer",
        "Pulse Oximeter Signal Explorer",
        majors=(BME,),
        interests=("sensors", "health", "signal processing", "embedded systems", "python"),
        difficulty="intermediate",
        hours=25,
        description="Read the raw red and infrared signals from a MAX30102 sensor, filter them, "
        "estimate heart rate, and compare with a commercial fingertip oximeter.",
        start=(
            "Wire the MAX30102 over I2C and stream raw red and IR samples to the serial port.",
            "Save 60 seconds of data to CSV; plot it in Python and find the pulse waveform.",
            "Band-pass filter 0.5-4 Hz; detect peaks with a minimum spacing of 0.3 s.",
            "Compute heart rate from the median beat interval; compare with the commercial device.",
            "Try finger pressure, movement and cold hands; document what breaks the signal.",
            "Write up the ratio-of-ratios idea behind SpO2 and why you are not reporting it.",
        ),
        materials=(
            ("MAX30102 pulse oximeter and heart-rate module", "1", "Raw PPG signals", 6),
            ("Arduino Uno or ESP32", "1", "Reads the sensor", 12),
            ("Commercial fingertip pulse oximeter", "1", "Reference for comparison", 20),
        ),
        guides=(
            (
                "ppg-notes",
                "Clean the PPG before counting peaks",
                "Band-pass 0.5-4 Hz, then detect peaks with a minimum spacing of 0.3 s. Report "
                "heart rate as the median of the last 8 beat intervals; it survives one bad beat.",
                ("signal processing", "health"),
            ),
        ),
        docs=(SCIPY_SIGNAL, ARDUINO_START),
    ),
    project(
        "prosthetic-finger-prototype",
        "3D-Printed Prosthetic Finger Prototype",
        majors=(BME,),
        interests=("3d printing", "health", "mechanics"),
        difficulty="beginner",
        hours=12,
        description="Print a tendon-driven finger with elastic return, fit it to a measured "
        "hand, and test grip on everyday objects.",
        start=(
            "Measure a finger's three segment lengths and joint widths with calipers.",
            "Model the segments and pin joints in Tinkercad with 0.3 mm clearance.",
            "Print at 80% scale first to check the joints move; then print full size.",
            "Thread fishing line as the tendon and elastic cord as the return spring.",
            "Mount on a Velcro strap; test picking up a pen, a cup and a ball; note what fails.",
        ),
        materials=(
            ("PLA filament", "about 80 g", "Finger segments", 3),
            ("Elastic cord and braided fishing line", "1 m each", "Return spring and tendon", 5),
            ("Velcro strap", "1", "Mounting to the hand", 3),
            ("Digital calipers", "1", "Measuring", 15),
        ),
        guides=(
            (
                "fit-notes",
                "Measure, print small, iterate",
                "Print the first joint at 80% scale to check tolerances (0.3 mm clearance works "
                "on most printers), then scale to the measured finger. Smooth the pin holes with "
                "a drill bit by hand.",
                ("3d printing", "health"),
            ),
        ),
        docs=(TINKERCAD,),
    ),
    project(
        "posture-wearable",
        "Posture Monitoring Wearable",
        majors=(BME,),
        interests=("sensors", "health", "embedded systems", "data visualization"),
        difficulty="intermediate",
        hours=40,
        description="A clip-on wearable that measures trunk angle with an IMU and vibrates after "
        "a minute of slouching, with a phone or laptop view of the day's posture.",
        start=(
            "Read the MPU6050 on an ESP32; print pitch from the accelerometer.",
            "Fuse accelerometer and gyro with a complementary filter for a stable angle.",
            "Add a 10-second calibration of 'upright' at power-on.",
            "Vibrate after 60 seconds past a 20 degree lean; stop when upright returns.",
            "Send the angle over Bluetooth or Wi-Fi every 5 seconds; chart a day of data.",
            "Wear it for a day; write down false alarms and what you would change.",
        ),
        materials=(
            ("MPU6050 IMU module", "1", "Trunk angle", 5),
            ("ESP32 development board", "1", "Controller with Bluetooth", 10),
            ("Coin vibration motor", "1", "Haptic alert", 3),
            ("500 mAh LiPo battery and charger board", "1", "Power", 12),
            ("Clip or elastic strap and a small case", "1", "Wearing it", 5),
        ),
        guides=(
            (
                "angle-notes",
                "Compute the trunk angle, then alert gently",
                "Fuse accelerometer and gyro with a complementary filter, define upright during a "
                "10 second calibration, and vibrate only after 60 seconds past a 20 degree lean.",
                ("sensors", "health"),
            ),
        ),
        docs=(MICROPYTHON_ESP32, ADAFRUIT_LEARN),
    ),
    project(
        "emg-led-bar",
        "EMG-Controlled LED Bar",
        majors=(BME,),
        interests=("sensors", "health", "neuroscience", "electronics"),
        difficulty="beginner",
        hours=10,
        description="Read a muscle sensor on your forearm and light more LEDs as you squeeze "
        "harder; a first look at electromyography.",
        start=(
            "Place three electrodes on the forearm as the sensor's guide shows.",
            "Read the sensor's envelope output on A0 and print it; squeeze and watch it rise.",
            "Map the value to 0-8 LEDs; add a smoothing average so the bar does not flicker.",
            "Add a calibration button that records relaxed and max-squeeze levels.",
            "Try different electrode positions and record which gives the cleanest signal.",
        ),
        materials=(
            ("MyoWare 2.0 muscle sensor or similar EMG module", "1", "Muscle signal", 40),
            ("Disposable electrode pads", "1 pack", "Skin contact", 8),
            ("Arduino Uno", "1", "Reads the sensor", 20),
            ("8 LEDs and 220 ohm resistors, or an LED bar", "1 set", "Display", 4),
            ("9 V battery and clip", "1", "Battery power only", 4),
        ),
        guides=(
            (
                "emg-safety",
                "Battery power only",
                "Run the EMG board and Arduino from a battery, never from a laptop plugged into "
                "the wall while electrodes are on skin. Clean the skin and place electrodes "
                "along the muscle, not across it.",
                ("health", "neuroscience"),
            ),
        ),
        docs=(ARDUINO_ANALOG, ARDUINO_START),
    ),
    project(
        "cell-counter-microscope",
        "Low-Cost Microscope Image Cell Counter",
        majors=(BME,),
        interests=("computer vision", "health", "microbiology", "machine learning", "python"),
        difficulty="advanced",
        hours=80,
        description="Count cells in microscope images with a classical OpenCV pipeline, measure it "
        "against hand counts, and only then decide whether a learned model is worth it.",
        start=(
            "Collect 30 images of prepared slides with a USB microscope at one magnification.",
            "Hand-count cells in 20 of them; this is your ground truth.",
            "Build the pipeline: grayscale, blur, threshold, watershed, contour count.",
            "Compare automatic against hand counts; plot agreement and look at the misses.",
            "Tune or add a size filter; if agreement stays below 90%, train a small U-Net.",
            "Package it as a script that takes a folder and writes a CSV of counts.",
        ),
        materials=(
            ("USB digital microscope or a phone-to-eyepiece adapter", "1", "Imaging", 40),
            ("Prepared slide set (blood smear, yeast, onion)", "1 set", "Samples", 20),
            ("Laptop", "1", "Processing", 0),
        ),
        guides=(
            (
                "counting-notes",
                "Classical first, learned second",
                "Start with thresholding and watershed in OpenCV and compare against 20 "
                "hand-counted images. Only train a model if the classical pipeline is below 90% "
                "agreement, and keep the 20 images as a test set.",
                ("computer vision", "microbiology"),
            ),
        ),
        docs=(
            OPENCV_PY,
            (
                "imagej",
                "ImageJ",
                "https://imagej.net/",
                "ImageJ",
                ("microbiology", "computer vision"),
            ),  # fmt: skip
        ),
    ),
    # ----------------------------------------------------------------------------- Biology
    project(
        "biodiversity-survey",
        "Backyard Biodiversity Survey with iNaturalist",
        majors=(BIO,),
        interests=("ecology", "plants", "data visualization", "education"),
        difficulty="beginner",
        hours=10,
        description="Walk the same transect for a week, photograph every organism you can, let "
        "iNaturalist help identify them, and chart what you found.",
        start=(
            "Pick a 50 m transect near you and mark its ends.",
            "Install iNaturalist; walk the line at the same hour on five days and photograph "
            "every plant, insect and bird you can.",
            "Accept or correct the suggested identifications; note the ones you are unsure of.",
            "Export your observations as CSV; count species per day and per group.",
            "Chart species accumulation over the five days and write what it tells you.",
        ),
        materials=(
            ("Smartphone with the iNaturalist app", "1", "Photos and identification", 0),
            ("Notebook and tape measure", "1 each", "Marking the transect", 5),
        ),
        guides=(
            (
                "transect-notes",
                "Use a fixed transect",
                "Walk the same 50 m line at the same time of day on five days and record every "
                "organism you can photograph. The species accumulation curve flattening is the "
                "result to show.",
                ("ecology",),
            ),
        ),
        docs=(
            (
                "inaturalist",
                "iNaturalist",
                "https://www.inaturalist.org/",
                "iNaturalist",
                ("ecology",),
            ),  # fmt: skip
            (
                "gbif",
                "GBIF: Global Biodiversity Information Facility",
                "https://www.gbif.org/",
                "GBIF",
                ("ecology",),
            ),  # fmt: skip
        ),
    ),
    project(
        "led-spectrum-plant-growth",
        "Plant Growth under Different LED Spectra",
        majors=(BIO, ECE),
        interests=("plants", "agriculture", "statistics", "sensors"),
        difficulty="intermediate",
        hours=30,
        description="Grow radish seedlings under red, blue and white LED strips on a timer and "
        "test whether the spectrum changes height and leaf count.",
        start=(
            "Set up three trays with 8 seeds each under red, blue and white LED strips, same "
            "distance, 14 hours a day on a timer.",
            "Water equally; measure height and leaf count every two days for three weeks.",
            "Enter the data in a spreadsheet with one row per plant per day.",
            "Plot mean height per treatment with error bars.",
            "Run a one-way ANOVA on final height; report the p-value and what it means.",
            "Write up confounders you could not control (temperature, light intensity).",
        ),
        materials=(
            ("Radish or Wisconsin Fast Plants seeds", "1 pack", "Fast-growing test plants", 8),
            ("Red, blue and white 12 V LED strips", "1 m each", "Light treatments", 20),
            ("12 V power supply and outlet timer", "1 each", "Powering the lights", 15),
            ("Seed trays and potting mix", "3", "Growing", 12),
            ("Ruler and kitchen scale", "1 each", "Measurements", 10),
        ),
        guides=(
            (
                "design-notes",
                "Replicates beat extra treatments",
                "Three light treatments with 8 plants each gives a real comparison; measure every "
                "two days and run a one-way ANOVA at the end. Keep the lamps at the same distance "
                "so intensity is not the hidden variable.",
                ("statistics", "plants"),
            ),
        ),
        docs=(SCIPY_STATS, MATPLOTLIB),
    ),
    project(
        "sourdough-microbiome-log",
        "Sourdough Starter Microbiome Log",
        majors=(BIO,),
        interests=("microbiology", "food", "cooking", "data visualization"),
        difficulty="beginner",
        hours=12,
        description="Start a sourdough culture from flour and water and track pH, rise and smell "
        "daily as the yeast and lactic acid bacteria take over.",
        start=(
            "Mix equal weights of flour and water in a jar; feed once a day at the same hour.",
            "Measure pH with strips and the rise height 6 hours after feeding; note the smell.",
            "Log everything in a spreadsheet for 14 days.",
            "Plot pH and rise against day; mark when pH falls below 4.",
            "Optional: streak a drop on an agar plate in a supervised lab and count colonies.",
            "Bake with it on day 14 and write what the log predicted about the bread.",
        ),
        materials=(
            ("Flour, water and two glass jars", "1 set", "The culture", 10),
            ("pH test strips (range 3-7)", "1 pack", "Acidity", 6),
            ("Ruler and masking tape", "1", "Rise height", 2),
            ("Optional: nutrient agar plates (lab)", "10", "Colony counts", 20),
        ),
        guides=(
            (
                "log-notes",
                "Measure the same three things daily",
                "pH, rise height after 6 hours and smell notes. Plot pH against day; the drop "
                "below 4 marks a stable culture dominated by lactic acid bacteria.",
                ("microbiology", "food"),
            ),
        ),
        docs=(),
    ),
    project(
        "dna-barcoding-blast",
        "DNA Barcoding Analysis with BLAST",
        majors=(BIO,),
        interests=("genetics", "bioinformatics", "ecology", "python"),
        difficulty="intermediate",
        hours=25,
        description="Identify species from public or class-generated barcode sequences with "
        "NCBI BLAST and build a small phylogenetic tree of what you found.",
        start=(
            "Collect 10-20 COI or ITS sequences (from a course, BOLD or GenBank) as FASTA.",
            "BLAST each one at NCBI; record top hit, identity, query cover and E-value.",
            "Decide a rule for 'identified' (for example 98% identity over 500 bp).",
            "Align the sequences with Clustal Omega or MUSCLE; build a neighbor-joining tree.",
            "Script the record keeping with Biopython so it is repeatable.",
            "Write up which samples were ambiguous and why.",
        ),
        materials=(
            ("Laptop", "1", "Everything runs online or in Python", 0),
            (
                "Optional: a barcoding kit through a course or the BOLD student program",
                None,
                "Your own sequences",
                0,
            ),  # fmt: skip
        ),
        guides=(
            (
                "blast-notes",
                "Read the alignment, not just the top hit",
                "99% identity over 600 bp is strong; 92% over 200 bp is not. Record query cover, "
                "identity and E-value for every sample before you call a species.",
                ("genetics", "bioinformatics"),
            ),
        ),
        docs=(
            (
                "ncbi-blast",
                "NCBI BLAST",
                "https://blast.ncbi.nlm.nih.gov/Blast.cgi",
                "NCBI",
                ("bioinformatics", "genetics"),
            ),  # fmt: skip
            (
                "biopython",
                "Biopython",
                "https://biopython.org/",
                "Biopython",
                ("bioinformatics", "python"),
            ),  # fmt: skip
        ),
    ),
    project(
        "soil-antibiotic-screen",
        "Soil Microbe Antibiotic Discovery Screen",
        majors=(BIO, CHEM),
        interests=("microbiology", "health", "chemistry lab"),
        difficulty="advanced",
        hours=90,
        description="Isolate bacteria from local soil and screen them for antibiotic activity "
        "against safe tester strains, in the style of the Tiny Earth program, in a supervised lab.",
        start=(
            "Arrange supervised access to a BSL-1 teaching lab and agree on the safety rules.",
            "Dilute a soil sample and plate it; pick 50 distinct colonies into a master plate.",
            "Spot each isolate against safe tester strains; look for zones of inhibition.",
            "Re-test the hits; photograph plates with a ruler for scale and measure zones.",
            "Characterize the best isolates (Gram stain, colony morphology, 16S if available).",
            "Present a table of hits with zone sizes and what a next step would be.",
        ),
        materials=(
            ("Supervised BSL-1 lab access (required)", "1", "Safety and equipment", 0),
            ("Nutrient agar plates", "40", "Growing isolates", 40),
            ("Sterile loops, swabs, tubes and a spreader", "1 set", "Handling", 25),
            ("Safe tester strains supplied by the course", "2", "Screening targets", 0),
        ),
        guides=(
            (
                "safety-first",
                "Do this only in a supervised lab",
                "Soil isolates are unknown organisms. Work at BSL-1 or higher with an instructor, "
                "autoclave everything, and never take plates home.",
                ("microbiology",),
            ),
        ),
        docs=(),
    ),
    # --------------------------------------------------------------------------- Chemistry
    project(
        "cabbage-ph-indicator",
        "Red Cabbage pH Indicator Strips",
        majors=(CHEM,),
        interests=("chemistry lab", "education", "plants"),
        difficulty="beginner",
        hours=8,
        description="Make pH indicator strips from red cabbage, calibrate them against a meter, "
        "and test household liquids; a complete small experiment with a real calibration.",
        start=(
            "Boil chopped red cabbage; soak coffee-filter strips in the liquid and dry them.",
            "Make six solutions of known pH (measured with a meter or reference strips).",
            "Dip a strip in each; photograph them side by side under the same light.",
            "Build your color chart from the photos.",
            "Test vinegar, baking soda, lemon juice, soap and tap water; estimate each pH.",
            "Compare with the meter and report how close the strips got.",
        ),
        materials=(
            ("Red cabbage", "1", "Anthocyanin indicator", 3),
            ("Coffee filters", "1 pack", "Strips", 4),
            ("Vinegar, baking soda, lemon juice, soap", "1 set", "Test liquids", 6),
            ("pH meter or reference strips", "1", "Calibration", 12),
        ),
        guides=(
            (
                "calibration-notes",
                "Make a color chart you can trust",
                "Dip strips in six solutions of known pH, photograph them under the same light "
                "and build your reference chart from those photos, not from a chart online.",
                ("chemistry lab",),
            ),
        ),
        docs=(PUBCHEM,),
    ),
    project(
        "webcam-spectrophotometer",
        "Webcam Spectrophotometer",
        majors=(CHEM, PHYS),
        interests=("optics", "chemistry lab", "sensors", "data visualization", "python"),
        difficulty="intermediate",
        hours=30,
        description="Build a spectrophotometer from a webcam, a diffraction grating and a box, "
        "calibrate it with a fluorescent lamp, and measure dye concentration with Beer's law.",
        start=(
            "Build a light-tight box with a 0.5 mm slit, the grating in front of the webcam.",
            "Capture a frame of a compact fluorescent lamp; find the bright lines.",
            "Map pixel column to wavelength using the 436 nm and 546 nm mercury lines.",
            "Take dark and blank frames; compute absorbance of a food dye solution.",
            "Measure five dilutions; plot absorbance against concentration (Beer's law).",
            "Measure an unknown dilution and report its concentration with an error estimate.",
        ),
        materials=(
            ("USB webcam", "1", "Detector", 15),
            ("Diffraction grating slide, 1000 lines/mm", "1", "Splits the light", 8),
            ("Cardboard box, black tape, razor blades for the slit", "1 set", "Housing", 10),
            ("Food dye and small clear vials or cuvettes", "1 set", "Samples", 10),
            ("Compact fluorescent lamp", "1", "Wavelength calibration", 6),
        ),
        guides=(
            (
                "wavelength-calibration",
                "Calibrate wavelength with known lines",
                "A compact fluorescent lamp has mercury lines at 436 and 546 nm; map pixel column "
                "to wavelength with those, then take dark and blank frames before every sample.",
                ("optics", "chemistry lab"),
            ),
        ),
        docs=(OPENCV_PY, MATPLOTLIB),
    ),
    project(
        "zinc-copper-battery",
        "Zinc-Copper Battery Optimization",
        majors=(CHEM,),
        interests=("energy", "chemistry lab", "electronics"),
        difficulty="beginner",
        hours=12,
        description="Build simple zinc-copper cells and find which electrolyte, electrode area "
        "and spacing give the most voltage and current, then stack cells to light an LED.",
        start=(
            "Build one cell: zinc and copper strips in a cup of salt water; measure the voltage.",
            "Measure the current through a 100 ohm resistor; record both.",
            "Change one variable at a time: electrolyte, electrode area, spacing.",
            "Chart voltage and current against each variable.",
            "Connect three cells in series; light an LED and time how long it lasts.",
        ),
        materials=(
            ("Zinc and copper strips", "4 each", "Electrodes", 10),
            ("Salt, vinegar and copper sulfate (from a kit)", "1 set", "Electrolytes", 12),
            ("Multimeter", "1", "Voltage and current", 15),
            ("Small cups, filter paper and alligator leads", "1 set", "Cells and wiring", 8),
        ),
        guides=(
            (
                "variables-notes",
                "Vary one thing: electrolyte, area, distance",
                "Record open-circuit voltage and the current through a 100 ohm resistor for each "
                "change. Expect about 1.1 V per cell; stack cells in series to light an LED.",
                ("energy", "chemistry lab"),
            ),
        ),
        docs=(PUBCHEM,),
    ),
    project(
        "biodiesel-from-cooking-oil",
        "Biodiesel from Used Cooking Oil",
        majors=(CHEM, ENV),
        interests=("sustainability", "energy", "chemistry lab"),
        difficulty="intermediate",
        hours=40,
        description="Convert filtered waste cooking oil into biodiesel by base-catalyzed "
        "transesterification in a supervised lab, then test it against the raw oil.",
        start=(
            "Arrange supervised lab time with a fume hood; review the safety data sheets.",
            "Filter and dry 1 L of used cooking oil; titrate its free fatty acid content.",
            "Run the reaction with methanol and KOH at 55 C; separate the glycerol layer.",
            "Wash and dry the biodiesel; measure yield.",
            "Compare viscosity and a small burn test against the raw oil.",
            "Report yield, cost per liter and what you would change.",
        ),
        materials=(
            ("Supervised chemistry lab with a fume hood (required)", "1", "Safety", 0),
            ("Used cooking oil, filtered", "1 L", "Feedstock", 0),
            ("Methanol and potassium hydroxide (lab-issued)", None, "Reagents", 0),
            ("Glassware, hot plate and magnetic stirrer", "1 set", "Reaction", 0),
        ),
        guides=(
            (
                "safety-notes",
                "Methanol and KOH need a fume hood",
                "Wear goggles and gloves. Measure the oil's free fatty acid content with a "
                "titration first; high FFA oil makes soap instead of biodiesel.",
                ("chemistry lab", "sustainability"),
            ),
        ),
        docs=(PUBCHEM,),
    ),
    project(
        "caffeine-docking",
        "Molecular Docking of Caffeine Analogs",
        majors=(CHEM,),
        interests=("simulation", "health", "chemistry lab", "bioinformatics", "python"),
        difficulty="advanced",
        hours=80,
        description="Dock caffeine and analogs you design into the adenosine A2A receptor with "
        "open-source tools and rank them by predicted binding.",
        start=(
            "Install AutoDock Vina, Open Babel and RDKit in a Python environment.",
            "Download the A2A receptor structure with caffeine from the PDB; strip waters.",
            "Redock caffeine; confirm the pose is within 2 angstroms RMSD of the crystal pose.",
            "Design 10 analogs in RDKit; generate 3D conformers.",
            "Dock all of them; rank by score and inspect the top poses.",
            "Write up the ranking and its limits (docking scores are not affinities).",
        ),
        materials=(("Laptop, any OS", "1", "All tools are free", 0),),
        guides=(
            (
                "docking-notes",
                "Validate by redocking the known ligand",
                "Before docking anything new, redock the ligand from the crystal structure; if "
                "its pose is not within 2 angstroms RMSD, fix your setup first.",
                ("simulation", "health"),
            ),
        ),
        docs=(
            (
                "rcsb-pdb",
                "RCSB Protein Data Bank",
                "https://www.rcsb.org/",
                "RCSB PDB",
                ("bioinformatics",),
            ),  # fmt: skip
            (
                "rdkit-docs",
                "RDKit documentation",
                "https://www.rdkit.org/docs/",
                "RDKit",
                ("simulation", "python"),
            ),  # fmt: skip
            PUBCHEM,
        ),
    ),
)
