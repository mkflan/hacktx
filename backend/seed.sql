-- Demo data: two fictional students and ten sample projects, copied from
-- json_api/dev/fixtures.py. Safe to run more than once (INSERT OR IGNORE, fixed IDs).
-- URLs are real public documentation pages; they stay provided_unverified.

INSERT OR IGNORE INTO users (id, username, major, interests, time_amount, time_unit, time_raw)
VALUES (1, 'alex_demo', 'Electrical and Computer Engineering', 'sensors, plants, sustainability', 12.0, 'total_hours', '12 total hours');
INSERT OR IGNORE INTO users (id, username, major, interests, time_amount, time_unit, time_raw)
VALUES (2, 'maya_demo', 'Computer Science', 'language learning, web apps, data visualization', 20.0, 'total_hours', '20 total hours');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (1, 'Smart Soil Moisture Monitor', 'Read a soil moisture sensor with a microcontroller and alert when a plant needs water.', 'Electrical and Computer Engineering',
    'sensors, plants, IoT', 10.0, 'total_hours', '10 total hours', NULL, 'beginner');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (1, 'arduino-getting-started', 'Getting Started with Arduino', 'https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/', 'documentation', 'Arduino',
    'arduino, microcontroller, sensors', NULL);
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (1, 'wiring-notes', 'Wiring notes for an analog moisture sensor', NULL, 'guide', NULL,
    'sensors, wiring', 'Power the sensor from 3.3 V, read the analog pin, and record dry and wet readings to calibrate thresholds.');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (2, 'Solar Panel Output Logger', 'Measure a small solar panel''s voltage and current over a day and chart it.', 'Electrical and Computer Engineering, Mechanical Engineering',
    'sustainability, energy, sensors', 12.0, 'total_hours', '12 total hours', NULL, 'intermediate');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (2, 'measurement-guide', 'Measuring panel voltage and current safely', NULL, 'guide', NULL,
    'energy, measurement', 'Use a voltage divider for the ADC and a shunt or current sensor module; log a reading every minute.');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (3, 'Mini Greenhouse Climate Controller', 'Keep a small enclosure within a temperature and humidity range.', 'Electrical and Computer Engineering, Mechanical Engineering',
    'plants, sensors, automation', 6.0, 'weeks', '6 weeks', NULL, NULL);

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (4, 'Water Quality Sensor Buoy', 'A floating sensor package that logs temperature and turbidity.', 'Electrical and Computer Engineering, Environmental Engineering',
    'sustainability, sensors, water', 30.0, 'total_hours', '30 total hours', NULL, 'advanced');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (5, 'Spaced-Repetition Vocabulary Web App', 'A browser flashcard app that schedules reviews and saves progress locally.', 'Computer Science',
    'language learning, web apps', 16.0, 'total_hours', '16 total hours', NULL, 'beginner');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (5, 'mdn-web-storage', 'Web Storage API', 'https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API', 'documentation', 'MDN',
    'web apps, javascript, storage', NULL);
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (5, 'scheduling-notes', 'Simple review scheduling', NULL, 'guide', NULL,
    'language learning, algorithms', 'Start with fixed intervals (1, 3, 7, 14 days) and move a card back to day 1 when it is missed.');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (6, 'Language Learning Progress Dashboard', 'Chart study streaks and accuracy from an exported study log.', 'Computer Science',
    'data visualization, language learning', 18.0, 'total_hours', '18 total hours', NULL, 'intermediate');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (6, 'd3-getting-started', 'Getting started with D3', 'https://d3js.org/getting-started', 'documentation', 'D3',
    'data visualization, javascript', NULL);

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (7, 'Campus Air Quality Map', 'Collect air quality readings around campus and show them on a web map.', 'Computer Science, Electrical and Computer Engineering',
    'data visualization, sensors, sustainability', 24.0, 'total_hours', '24 total hours', NULL, 'advanced');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (7, 'leaflet-reference', 'Leaflet API reference', 'https://leafletjs.com/reference.html', 'documentation', 'Leaflet',
    'maps, data visualization, web apps', NULL);

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (8, 'Phrasebook Chat Helper', 'A rule-based chat helper that practices travel phrases.', 'Computer Science, Linguistics',
    'language learning, chatbots', NULL, 'unknown', 'a few weekends', NULL, 'intermediate');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (9, '3D-Printed Bike Accessory Mount', 'Design and print a handlebar mount and test how much load it holds.', 'Mechanical Engineering',
    '3d printing, cycling', 8.0, 'total_hours', '8 total hours', NULL, 'beginner');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (9, 'print-checklist', 'Print settings checklist', NULL, 'guide', NULL,
    '3d printing', 'Print a small test section first; orient layers across the load direction.');

INSERT OR IGNORE INTO projects (id, name, scope, majors, interests, timeline_amount,
    timeline_unit, timeline_raw, timeline_estimated_hours, difficulty)
VALUES (10, 'Recipe Scaling Command-Line Tool', NULL, 'Mathematics',
    'cooking, command line tools', 5.0, 'total_hours', '5 total hours', NULL, 'beginner');
INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider,
    topic_tags, content_excerpt)
VALUES (10, 'python-argparse', 'argparse: command-line parsing', 'https://docs.python.org/3/library/argparse.html', 'documentation', 'Python',
    'python, command line tools', NULL);

-- Forum demo posts and comments (fictional, from the two demo users). Fixed IDs and
-- timestamps keep this idempotent.
INSERT OR IGNORE INTO posts (id, user_id, project_id, title, body, created_at)
VALUES (1, 1, 1, 'Soil sensor readings are noisy, any tips?',
    'I wired the analog moisture sensor to 3.3 V and the readings jump around by about 10%. Averaging helped a little. Has anyone calibrated theirs against a dry and a wet sample?',
    '2026-10-20 14:05:00');
INSERT OR IGNORE INTO posts (id, user_id, project_id, title, body, created_at)
VALUES (2, 2, 5, 'Looking for feedback on my flashcard scheduler',
    'My spaced-repetition app uses fixed intervals of 1, 3, 7 and 14 days and resets a card to day 1 when it is missed. Does that seem reasonable, or should I try something adaptive?',
    '2026-10-21 09:30:00');
INSERT OR IGNORE INTO posts (id, user_id, project_id, title, body, created_at)
VALUES (3, 2, NULL, 'Anyone want to team up on a data visualization project?',
    'I am a CS major interested in data visualization and sensors. If you have sensor data and want to chart it, let us talk.',
    '2026-10-22 18:45:00');

INSERT OR IGNORE INTO comments (id, post_id, user_id, body, created_at)
VALUES (1, 1, 2, 'Try taking the median of ten samples instead of the mean. It ignores the spikes.',
    '2026-10-20 16:20:00');
INSERT OR IGNORE INTO comments (id, post_id, user_id, body, created_at)
VALUES (2, 3, 1, 'I have a week of soil sensor logs. Would love a chart of them.',
    '2026-10-23 08:10:00');
