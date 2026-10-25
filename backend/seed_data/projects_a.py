"""Catalog part A: Computer Science, Electrical and Computer Engineering, Mechanical Engineering."""

from .vocab import project

CS = "Computer Science"
ECE = "Electrical and Computer Engineering"
ME = "Mechanical Engineering"
ENV = "Environmental Science"

# Documentation home pages reused across projects (slug, title, url, provider, tags).
GITHUB = ("github-get-started", "GitHub: Get started", "https://docs.github.com/en/get-started", "GitHub", ("web apps",))  # fmt: skip
VSCODE = ("vscode-docs", "Visual Studio Code docs", "https://code.visualstudio.com/docs", "Microsoft", ("web apps",))  # fmt: skip
PY_VENV = ("python-venv", "venv: virtual environments", "https://docs.python.org/3/library/venv.html", "Python", ("python",))  # fmt: skip
ARDUINO_START = ("arduino-getting-started", "Getting Started with Arduino", "https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/", "Arduino", ("embedded systems", "electronics"))  # fmt: skip
ARDUINO_ANALOG = ("arduino-analogread", "analogRead() reference", "https://www.arduino.cc/reference/en/language/functions/analog-io/analogread/", "Arduino", ("embedded systems",))  # fmt: skip
ARDUINO_WIRE = ("arduino-wire", "Wire library (I2C)", "https://www.arduino.cc/reference/en/language/functions/communication/wire/", "Arduino", ("embedded systems",))  # fmt: skip
MICROPYTHON_ESP32 = ("micropython-esp32", "MicroPython on the ESP32: quick reference", "https://docs.micropython.org/en/latest/esp32/quickref.html", "MicroPython", ("embedded systems", "python"))  # fmt: skip
ADAFRUIT_LEARN = ("adafruit-learn", "Adafruit Learning System", "https://learn.adafruit.com/", "Adafruit", ("electronics", "embedded systems"))  # fmt: skip
SPARKFUN = ("sparkfun-tutorials", "SparkFun tutorials", "https://learn.sparkfun.com/tutorials", "SparkFun", ("electronics",))  # fmt: skip
TINKERCAD = ("tinkercad", "Tinkercad", "https://www.tinkercad.com/", "Autodesk", ("3d printing",))  # fmt: skip
FREECAD = ("freecad-wiki", "FreeCAD documentation", "https://wiki.freecad.org/", "FreeCAD", ("3d printing", "mechanics"))  # fmt: skip
MDN_JS = ("mdn-js-guide", "JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "MDN", ("web apps",))  # fmt: skip

PROJECTS: tuple[dict, ...] = (
    # ---------------------------------------------------------------- Computer Science
    project(
        "vocab-spaced-repetition",
        "Spaced-Repetition Vocabulary Web App",
        majors=(CS,),
        interests=("language learning", "web apps", "education"),
        difficulty="beginner",
        hours=16,
        description="A browser flashcard app that schedules reviews with spaced repetition and "
        "saves progress locally, with no server to run.",
        start=(
            "Create a GitHub repository, clone it, and write a README with the one-sentence goal "
            "and the two-minute demo you will show.",
            "Make index.html, style.css and app.js; open the folder in VS Code and serve it with "
            "the Live Server extension or `python -m http.server`.",
            "Define a card as {front, back, interval_days, due} and hard-code five cards; render "
            "the one that is due.",
            "Add 'Got it' and 'Missed it' buttons: the interval steps 1, 3, 7, 14 days on success "
            "and resets to 1 on a miss.",
            "Save the deck in localStorage so a refresh keeps progress; add JSON import/export.",
            "Add a deck editor and a daily review count; use it for a week with 20 real words.",
        ),
        materials=(
            ("Laptop with a modern browser", "1", "Everything runs client-side", 0),
            ("VS Code with the Live Server extension (free)", "1", "Editing and local preview", 0),
        ),
        guides=(
            (
                "scheduling-notes",
                "Simple review scheduling",
                "Start with fixed intervals (1, 3, 7, 14 days) and move a card back to day 1 when "
                "it is missed. Store the next due date, not an interval index, so the app still "
                "works after a long break.",
                ("language learning", "web apps"),
            ),
        ),
        docs=(
            (
                "mdn-web-storage",
                "Web Storage API",
                "https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API",
                "MDN",
                ("web apps",),
            ),  # fmt: skip
            MDN_JS,
            GITHUB,
        ),
    ),
    project(
        "password-pattern-analyzer",
        "Password Strength and Pattern Analyzer",
        majors=(CS,),
        interests=("cybersecurity", "web apps", "education"),
        difficulty="beginner",
        hours=10,
        description="A single-page tool that scores a password by entropy and by common patterns "
        "(keyboard walks, years, dictionary words) and explains every deduction. The password "
        "never leaves the browser.",
        start=(
            "Create the repository and a static page with one input box and a result panel.",
            "Estimate entropy as length x log2(character set size) and show it as bits.",
            "Add pattern checks: repeated characters, sequences like 1234 and qwerty, years "
            "1900-2030, and a 1,000-word common-password list stored as a local file.",
            "Show each rule that fired and how many bits it cost; color the result.",
            "Test against 50 known-weak passwords and 10 strong passphrases; fix false alarms.",
            "Write a short page explaining why the check runs only in the browser.",
        ),
        materials=(("Laptop with a modern browser", "1", "Runs entirely client-side", 0),),
        guides=(
            (
                "entropy-notes",
                "Estimating password entropy honestly",
                "length x log2(charset) is an upper bound. Subtract for dictionary words, repeats, "
                "sequences and years, and always show the user which rule fired. Never send the "
                "password anywhere, not even to your own server.",
                ("cybersecurity",),
            ),
        ),
        docs=(MDN_JS, GITHUB),
    ),
    project(
        "language-progress-dashboard",
        "Language Learning Progress Dashboard",
        majors=(CS,),
        interests=("data visualization", "language learning", "web apps"),
        difficulty="intermediate",
        hours=18,
        description="Chart study streaks, accuracy and vocabulary growth from an exported study "
        "log (a CSV from Anki, Duolingo screenshots typed up, or a spreadsheet).",
        start=(
            "Export or build a CSV with one row per review: date, word, correct (0/1), tag.",
            "Create a static site; load the CSV with d3.csv() and aggregate to one row per day.",
            "Draw the first chart: reviews per day as bars.",
            "Add a streak counter and an accuracy-by-tag chart.",
            "Add a date range picker; make the charts redraw.",
            "Publish on GitHub Pages and put the link in the README.",
        ),
        materials=(("Laptop", "1", "Static site, no server", 0),),
        guides=(
            (
                "shape-the-data",
                "Shape the data before charting",
                "Aggregate the raw log to one row per day (reviews, correct, new words) before "
                "drawing anything; the charts stay simple and fast and the streak logic lives in "
                "one place.",
                ("data visualization",),
            ),
        ),
        docs=(
            (
                "d3-getting-started",
                "Getting started with D3",
                "https://d3js.org/getting-started",
                "D3",
                ("data visualization", "web apps"),
            ),  # fmt: skip
            (
                "github-pages",
                "GitHub Pages documentation",
                "https://docs.github.com/en/pages",
                "GitHub",
                ("web apps",),
            ),  # fmt: skip
        ),
    ),
    project(
        "phrasebook-chat-helper",
        "Phrasebook Chat Helper",
        majors=(CS,),
        interests=("language learning", "natural language processing", "web apps", "python"),
        difficulty="intermediate",
        hours=30,
        description="A rule-based chat helper that practices travel phrases: it matches what the "
        "student typed against phrase templates, shows a corrected version and asks a follow-up.",
        start=(
            "Create the repository and a Python virtual environment; install Flask.",
            "Write 50 phrases with 2-3 accepted variants each into phrases.json.",
            "Implement normalization (lowercase, strip punctuation) and fuzzy matching with "
            "difflib.SequenceMatcher; print the best match and its score.",
            "Build a one-page chat UI that posts to a /reply route and shows the correction.",
            "Add hints when the score is low and a per-session score.",
            "Test with three classmates and log which phrases confuse the matcher.",
        ),
        materials=(("Laptop", "1", "Local Flask server", 0),),
        guides=(
            (
                "matching-notes",
                "Fuzzy matching without a model",
                "Lowercase, strip punctuation, then compare with difflib ratio against each "
                "template. Above 0.8 is a match, 0.6-0.8 asks 'did you mean', below shows the "
                "hint. Keep the thresholds in one config dict so you can tune them.",
                ("natural language processing",),
            ),
        ),
        docs=(
            (
                "python-difflib",
                "difflib: helpers for computing deltas",
                "https://docs.python.org/3/library/difflib.html",
                "Python",
                ("natural language processing", "python"),
            ),  # fmt: skip
            (
                "flask-quickstart",
                "Flask Quickstart",
                "https://flask.palletsprojects.com/en/stable/quickstart/",
                "Flask",
                ("web apps", "python"),
            ),  # fmt: skip
            PY_VENV,
        ),
    ),
    project(
        "plant-disease-classifier",
        "Plant Disease Image Classifier",
        majors=(CS,),
        interests=("machine learning", "computer vision", "plants", "agriculture", "python"),
        difficulty="intermediate",
        hours=40,
        description="Fine-tune a small pretrained image model to tell healthy leaves from common "
        "diseases using a public leaf dataset, then wrap it in a simple upload page.",
        start=(
            "Create the repository and a virtual environment; install PyTorch and torchvision.",
            "Download a public leaf-disease dataset (PlantVillage on Kaggle) and split it into "
            "train, validation and test folders.",
            "Fine-tune MobileNetV3 with a frozen backbone for 3 epochs; record validation accuracy.",
            "Unfreeze the last block, lower the learning rate 10x, train 3 more epochs.",
            "Plot a confusion matrix; write down which classes confuse the model and why.",
            "Add a small Flask or Gradio upload page that shows the top-3 classes.",
            "Document the dataset's limits (lab photos, not field photos) in the README.",
        ),
        materials=(
            (
                "Laptop; a free GPU runtime such as Google Colab speeds up training",
                "1",
                "Training and inference",
                0,
            ),  # fmt: skip
        ),
        guides=(
            (
                "transfer-learning-checklist",
                "Transfer learning checklist",
                "Freeze the backbone, train the head, then unfreeze the last block with a 10x "
                "smaller learning rate. Report accuracy only on images the model never saw, and "
                "look at the wrong predictions by eye.",
                ("machine learning", "computer vision"),
            ),
        ),
        docs=(
            (
                "pytorch-tutorials",
                "PyTorch Tutorials",
                "https://pytorch.org/tutorials/",
                "PyTorch",
                ("machine learning",),
            ),  # fmt: skip
            (
                "kaggle-datasets",
                "Kaggle Datasets",
                "https://www.kaggle.com/datasets",
                "Kaggle",
                ("machine learning",),
            ),  # fmt: skip
            PY_VENV,
        ),
    ),
    project(
        "campus-air-quality-map",
        "Campus Air Quality Map",
        majors=(CS, ECE),
        interests=("data visualization", "sensors", "sustainability", "maps", "web apps"),
        difficulty="advanced",
        hours=45,
        description="Carry a particulate sensor around campus, log readings with GPS, and show "
        "them on a web map with a time slider.",
        start=(
            "Order the sensor, board and GPS module; create the repository with a hardware/ and "
            "web/ folder.",
            "Wire the PM sensor and GPS to the ESP32; print one reading per second over serial.",
            "Log to a microSD card or a phone over Bluetooth as CSV: time, lat, lon, PM2.5.",
            "Walk three routes at the same hour on three days.",
            "Clean the CSV in Python (drop warm-up readings, average per 10 m).",
            "Draw the points on a Leaflet map colored by PM2.5; add a time slider.",
            "Write a methods page: sensor limits, calibration, what the colors do not mean.",
        ),
        materials=(
            ("PMS5003 particulate matter sensor", "1", "PM2.5 readings", 20),
            ("ESP32 development board", "1", "Reads the sensor and logs", 10),
            ("NEO-6M GPS module", "1", "Position for every reading", 12),
            ("MicroSD card module and card", "1", "Logging", 8),
            ("USB power bank", "1", "Portable power", 15),
        ),
        guides=(
            (
                "calibration-notes",
                "Know what a low-cost sensor can say",
                "Low-cost particulate sensors drift with humidity. Compare side by side with a "
                "reference station if your city has one, and present values as relative "
                "differences across campus, not as regulatory numbers.",
                ("sensors", "sustainability"),
            ),
        ),
        docs=(
            (
                "leaflet-reference",
                "Leaflet API reference",
                "https://leafletjs.com/reference.html",
                "Leaflet",
                ("maps", "data visualization"),
            ),  # fmt: skip
            (
                "esp32-arduino-core",
                "Arduino core for the ESP32",
                "https://docs.espressif.com/projects/arduino-esp32/en/latest/",
                "Espressif",
                ("embedded systems",),
            ),  # fmt: skip
        ),
    ),
    # ---------------------------------------------------- Electrical and Computer Engineering
    project(
        "soil-moisture-monitor",
        "Smart Soil Moisture Monitor",
        majors=(ECE,),
        interests=("sensors", "plants", "embedded systems", "iot"),
        difficulty="beginner",
        hours=10,
        description="Read a soil moisture sensor with a microcontroller and light an LED (or send "
        "a message) when a plant needs water.",
        start=(
            "Install the Arduino IDE and run the Blink example to check the board.",
            "Wire the capacitive sensor to 3.3 V, GND and A0; print readings to the serial monitor.",
            "Record a reading in dry soil and in freshly watered soil; pick a threshold between.",
            "Light an LED (or beep) below the threshold; wait 10 minutes between checks.",
            "Log a reading every 30 minutes for 3 days and plot it in a spreadsheet.",
            "Optional: send a Wi-Fi notification from an ESP32 instead of lighting an LED.",
        ),
        materials=(
            ("Arduino Uno or compatible board", "1", "Reads the sensor", 25),
            ("Capacitive soil moisture sensor v1.2", "1", "Measures soil water content", 8),
            ("Breadboard and jumper wires", "1 set", "Connections", 8),
            ("LED and 220 ohm resistor", "1 each", "Alert when the soil is dry", 1),
        ),
        guides=(
            (
                "wiring-notes",
                "Wiring notes for an analog moisture sensor",
                "Power the sensor from 3.3 V, read the analog pin, and record dry and wet readings "
                "to calibrate your thresholds. Capacitive sensors last far longer in soil than "
                "resistive ones.",
                ("sensors", "electronics"),
            ),
        ),
        docs=(ARDUINO_START, ARDUINO_ANALOG),
    ),
    project(
        "solar-output-logger",
        "Solar Panel Output Logger",
        majors=(ECE, ME),
        interests=("sustainability", "energy", "sensors", "data visualization"),
        difficulty="intermediate",
        hours=20,
        description="Measure a small solar panel's voltage and current through a day and chart "
        "energy against the weather and the panel angle.",
        start=(
            "Wire the panel to a power resistor load through an INA219 current sensor.",
            "Read voltage and current every minute on the Arduino; print power in watts.",
            "Add a microSD module and log time, V, I and P as CSV.",
            "Run one full day at a fixed angle; chart power against time of day.",
            "Repeat at two more angles; compare total energy per day.",
            "Write up the best angle for your latitude and compare with the textbook value.",
        ),
        materials=(
            ("5 W 12 V solar panel", "1", "The energy source being measured", 20),
            ("INA219 current and voltage sensor breakout", "1", "Measures V and I over I2C", 8),
            ("Arduino Uno or ESP32", "1", "Reads the sensor and logs", 12),
            ("MicroSD card module and card", "1", "Logging", 8),
            ("10 ohm 10 W power resistor", "1", "Dummy load", 3),
        ),
        guides=(
            (
                "measurement-guide",
                "Measuring panel voltage and current safely",
                "Never short the panel directly; put the resistor load in the circuit first. "
                "Log a reading every minute and keep the sensor in the shade so its temperature "
                "does not drift.",
                ("energy", "sensors"),
            ),
        ),
        docs=(
            (
                "adafruit-ina219",
                "Adafruit INA219 current sensor guide",
                "https://learn.adafruit.com/adafruit-ina219-current-sensor-breakout",
                "Adafruit",
                ("sensors", "electronics"),
            ),  # fmt: skip
            ARDUINO_WIRE,
        ),
    ),
    project(
        "greenhouse-climate-controller",
        "Mini Greenhouse Climate Controller",
        majors=(ECE, ME),
        interests=("plants", "sensors", "automation", "embedded systems", "control systems"),
        difficulty="intermediate",
        hours=40,
        description="Keep a small enclosure inside a temperature and humidity range with a fan, "
        "a heat mat and a controller you tune yourself.",
        start=(
            "Read a DHT22 sensor on the ESP32 and print temperature and humidity every 5 seconds.",
            "Switch a fan and a seedling heat mat through a 2-channel relay module.",
            "Write on/off control with hysteresis (heat below 22 C, off above 24 C).",
            "Put everything in a clear storage bin with a few seedlings; log for 24 hours.",
            "Chart the swings; shrink them by tuning the gap or moving to a simple PID loop.",
            "Add a small web page served by the ESP32 that shows live readings.",
        ),
        materials=(
            ("DHT22 temperature and humidity sensor", "1", "Sensing", 6),
            ("ESP32 development board", "1", "Controller with Wi-Fi", 10),
            ("2-channel 5 V relay module", "1", "Switches fan and heat mat", 6),
            ("12 V fan and seedling heat mat", "1 each", "Actuators", 25),
            ("Clear plastic storage bin", "1", "Enclosure", 10),
        ),
        guides=(
            (
                "control-notes",
                "Start with on/off control, then hysteresis",
                "Heat on below 22 C and off above 24 C; the gap stops the relay from chattering. "
                "Only move to PID if the remaining swing matters for your plants.",
                ("control systems", "automation"),
            ),
        ),
        docs=(MICROPYTHON_ESP32, ADAFRUIT_LEARN),
    ),
    project(
        "water-quality-buoy",
        "Water Quality Sensor Buoy",
        majors=(ECE, ENV),
        interests=("sustainability", "sensors", "water", "embedded systems", "iot"),
        difficulty="advanced",
        hours=80,
        description="A floating sensor package that logs water temperature and turbidity and "
        "sends readings home over Wi-Fi or LoRa.",
        start=(
            "Read the DS18B20 probe and the turbidity module on an ESP32 over serial.",
            "Send a reading every 10 minutes to a free MQTT broker or a Google Sheet.",
            "Build the float: sealed IP67 box, foam collar, probes through cable glands.",
            "Run the sealed buoy in a bucket for 48 hours; check for condensation and battery draw.",
            "Add deep sleep between readings; measure the battery life you get.",
            "Get permission for a pond or creek site; deploy for a week and chart the data.",
        ),
        materials=(
            ("Waterproof DS18B20 temperature probe", "1", "Water temperature", 5),
            ("Turbidity sensor module", "1", "Cloudiness of the water", 12),
            (
                "ESP32 board (LoRa version if there is no Wi-Fi at the site)",
                "1",
                "Controller and radio",
                20,
            ),  # fmt: skip
            ("IP67 junction box and cable glands", "1", "Waterproof housing", 15),
            ("Foam collar or pool noodle, zip ties", "1 set", "Flotation", 8),
            ("Li-ion battery pack with charger board", "1", "Power", 20),
        ),
        guides=(
            (
                "deployment-notes",
                "Test on a bucket before the pond",
                "Run the sealed buoy in a bucket for 48 hours. Check for condensation, battery "
                "draw and data gaps before any outdoor deployment, and get written permission "
                "for the site.",
                ("water", "sensors"),
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
            MICROPYTHON_ESP32,
        ),
    ),
    project(
        "bike-brake-light",
        "Bike Light with Automatic Brake Flash",
        majors=(ECE,),
        interests=("embedded systems", "cycling", "sensors", "electronics"),
        difficulty="beginner",
        hours=8,
        description="A rear bike light that flashes brighter when an accelerometer detects "
        "braking, built on a tiny Arduino.",
        start=(
            "Read the MPU6050 accelerometer over I2C and print the forward axis.",
            "Average readings over 200 ms; print 'BRAKE' when deceleration passes a threshold.",
            "Drive four red LEDs: steady at low brightness, full flash on BRAKE for 1 second.",
            "Move to battery power; mount in a small box with the sensor axis pointing forward.",
            "Test on a bike in a parking lot; tune the threshold so bumps do not trigger it.",
        ),
        materials=(
            ("Arduino Nano (or compatible)", "1", "Controller", 8),
            ("MPU6050 accelerometer and gyroscope module", "1", "Detects braking", 5),
            ("High-brightness red LEDs and 100 ohm resistors", "4 each", "Light", 3),
            ("9 V battery with clip, or a small LiPo with charger", "1", "Power", 8),
            ("Small project box and zip ties", "1", "Mounting", 5),
        ),
        guides=(
            (
                "braking-detection",
                "Detecting braking from acceleration",
                "Average the forward axis over 200 ms; a sustained negative value past your "
                "threshold is braking. Add a hold time of about a second so the flash does not "
                "flicker on bumps.",
                ("sensors", "embedded systems"),
            ),
        ),
        docs=(ARDUINO_WIRE, ARDUINO_START),
    ),
    # --------------------------------------------------------------- Mechanical Engineering
    project(
        "bike-accessory-mount",
        "3D-Printed Bike Accessory Mount",
        majors=(ME,),
        interests=("3d printing", "cycling", "mechanics"),
        difficulty="beginner",
        hours=8,
        description="Design and print a handlebar mount for a light or phone, then test how "
        "much load it holds before it fails.",
        start=(
            "Measure the handlebar diameter and the accessory with calipers; sketch the clamp.",
            "Model the clamp in Tinkercad or FreeCAD with a 0.3 mm clearance.",
            "Print a small test ring first to check the fit; adjust and print the full part.",
            "Mount it and hang weights from the accessory tab until something gives; record the load.",
            "Change one thing (wall thickness, infill, orientation) and test again.",
        ),
        materials=(
            ("Access to a 3D printer (campus makerspace)", "1", "Printing", 0),
            ("PETG or PLA filament", "about 50 g", "Material for the clamp", 2),
            ("M5 bolts and nuts", "2", "Clamp closure", 2),
            ("Digital calipers", "1", "Measuring", 15),
        ),
        guides=(
            (
                "print-checklist",
                "Print settings checklist",
                "Print a small test section first. Orient layers across the load direction, use "
                "at least three walls, and let PETG cool before unclamping it from the bed.",
                ("3d printing",),
            ),
        ),
        docs=(TINKERCAD, FREECAD),
    ),
    project(
        "wind-turbine-blade-rig",
        "Desktop Wind Turbine Blade Test Rig",
        majors=(ME,),
        interests=("energy", "sustainability", "3d printing", "mechanics"),
        difficulty="intermediate",
        hours=40,
        description="Print blade sets with different pitch and count, spin them with a box fan, "
        "and measure RPM and electrical power to find the best design.",
        start=(
            "Build the rig: a small DC motor as generator on a stand, 1 m from a box fan.",
            "Model a parametric blade in OpenSCAD (pitch angle, chord, count) and print one set.",
            "Add a Hall sensor and magnet for RPM; read it and the loaded voltage on an Arduino.",
            "Run three trials per design at the same fan speed; log RPM, voltage and current.",
            "Vary only pitch, then only blade count; chart power against each.",
            "Write up the best design and compare its tip-speed ratio with textbook values.",
        ),
        materials=(
            ("Small DC motor used as a generator", "1", "Converts rotation to voltage", 8),
            ("Box fan", "1", "Wind source", 25),
            ("Hall-effect sensor and small magnet", "1 each", "RPM measurement", 4),
            ("Arduino Uno", "1", "Logging", 20),
            ("Filament for blade sets", "about 200 g", "Blades", 6),
            ("Multimeter", "1", "Checking voltage and current", 15),
        ),
        guides=(
            (
                "testing-notes",
                "Change one variable at a time",
                "Fix the fan distance and speed, then vary only pitch, then only blade count. "
                "Log RPM and loaded voltage into a shared spreadsheet with three runs per design.",
                ("energy", "mechanics"),
            ),
        ),
        docs=(
            (
                "openscad-docs",
                "OpenSCAD documentation",
                "https://openscad.org/documentation.html",
                "OpenSCAD",
                ("3d printing",),
            ),  # fmt: skip
            ARDUINO_START,
        ),
    ),
    project(
        "compliant-gripper",
        "Compliant Gripper for a Hobby Robot Arm",
        majors=(ME,),
        interests=("robotics", "3d printing", "mechanics"),
        difficulty="intermediate",
        hours=25,
        description="Design a one-piece printed gripper with living hinges, drive it with a "
        "micro servo and measure what it can pick up.",
        start=(
            "Sketch a two-finger gripper where flexures replace pins; pick flexure thickness.",
            "Model it in FreeCAD; print a single flexure and bend it 100 times by hand.",
            "Print the full gripper; add a micro servo and a horn linkage.",
            "Drive the servo from an Arduino sweep sketch; measure opening range.",
            "Test on 10 objects (egg, pen, cup); record grip success and the max weight held.",
            "Iterate once on hinge thickness or finger shape and retest.",
        ),
        materials=(
            ("TPU or PETG filament", "about 100 g", "Flexible gripper body", 8),
            ("SG90 or MG90S micro servo", "1", "Actuation", 4),
            ("Arduino or servo tester", "1", "Driving the servo", 10),
            ("Assorted M2 and M3 screws", "1 set", "Mounting", 6),
        ),
        guides=(
            (
                "compliant-notes",
                "Design living hinges you can print",
                "Keep flexure thickness at 0.8-1.2 mm for PETG and print flexures flat on the "
                "bed. Test each hinge 100 cycles by hand before adding the servo.",
                ("3d printing", "robotics"),
            ),
        ),
        docs=(
            (
                "arduino-servo",
                "Servo library",
                "https://www.arduino.cc/reference/en/libraries/servo/",
                "Arduino",
                ("robotics", "embedded systems"),
            ),  # fmt: skip
            FREECAD,
        ),
    ),
    project(
        "pedal-phone-charger",
        "Pedal-Powered Phone Charger",
        majors=(ME,),
        interests=("energy", "cycling", "sustainability", "electronics"),
        difficulty="beginner",
        hours=12,
        description="Turn a bike on a trainer stand into a USB charger with a DC motor as the "
        "generator and a buck converter, and measure the watts you can pedal.",
        start=(
            "Mount a DC motor so its shaft presses against the rear tire on a trainer stand.",
            "Pedal and measure open-circuit voltage at a slow, medium and fast cadence.",
            "Add a buck converter rated above your max voltage; set its output to 5 V.",
            "Add a fuse on the input and a USB socket on the output; charge a phone.",
            "Measure power with a USB meter at each cadence; chart watts against cadence.",
        ),
        materials=(
            ("Bike trainer stand (borrow one)", "1", "Holds the bike", 0),
            ("12-24 V DC motor or bicycle hub dynamo", "1", "Generator", 20),
            ("Buck converter to 5 V USB with display", "1", "Regulation", 8),
            ("Inline fuse holder and 3 A fuse", "1", "Safety", 4),
            ("Multimeter and USB power meter", "1 each", "Measurement", 20),
        ),
        guides=(
            (
                "safety-notes",
                "Keep the voltage in range",
                "Measure the open-circuit voltage at your fastest pedaling before connecting "
                "anything; choose a converter rated above that and add a fuse on the input.",
                ("energy", "electronics"),
            ),
        ),
        docs=(SPARKFUN,),
    ),
    project(
        "hydroponics-tower",
        "Small Vertical Hydroponics Tower",
        majors=(ME, "Biology"),
        interests=("plants", "agriculture", "water", "3d printing", "sustainability"),
        difficulty="advanced",
        hours=90,
        description="Build a 1.5 m vertical hydroponic tower from PVC with printed net-cup "
        "holders, a pump on a timer and an LED grow light, and grow lettuce from seed to harvest.",
        start=(
            "Design the tower: 4 inch PVC with 12 angled holes; print the net-cup holders.",
            "Cut and assemble the pipe over a reservoir bucket; fit the pump and return line.",
            "Mix nutrients to EC 1.2-1.8 mS/cm and pH 5.8-6.2; run the pump 15 minutes per hour.",
            "Start lettuce in rockwool; transplant at two true leaves.",
            "Log EC, pH and water temperature daily; top up and adjust.",
            "Harvest at 5-6 weeks; weigh the yield and total the water and power used.",
        ),
        materials=(
            ("4 inch PVC pipe (1.5 m) and end caps", "1", "Tower body", 25),
            ("Submersible pump, about 200 GPH", "1", "Circulates nutrients", 15),
            ("Net cups and clay pebbles", "12", "Holds the plants", 15),
            ("Two-part hydroponic nutrients", "1 set", "Feeds the plants", 20),
            ("EC/TDS meter and pH meter", "1 each", "Daily checks", 25),
            ("Full-spectrum LED grow light", "1", "Light indoors", 35),
            ("Reservoir bucket with lid (20 L)", "1", "Nutrient tank", 10),
        ),
        guides=(
            (
                "nutrient-notes",
                "Log EC and pH daily",
                "Lettuce likes pH 5.8-6.2 and EC 1.2-1.8 mS/cm. Record both every day along with "
                "the water temperature; most problems show up in that log before the leaves.",
                ("plants", "agriculture"),
            ),
        ),
        docs=(TINKERCAD,),
    ),
)
