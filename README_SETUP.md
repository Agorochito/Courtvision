# CourtVision — Redesign installation guide

This package updates the visual interface without intentionally changing your existing database schema. It is intended to be copied into **your existing project directory**, not run from inside the downloaded ZIP.

## Before installing

1. Quit the existing Streamlit server (`Control + C`).
2. In VS Code, **copy your original `app.py` and `main.py` somewhere safe** (for example to a folder named `backup_before_redesign/`).
3. Do **not** delete or replace `courtvision.db`, your database backup, or `.venv/`.
4. Unzip this package, and copy `app.py`, `main.py`, `styles.css`, `.gitignore`, and `requirements.txt` into your existing Courtvision folder. Keep your existing `test_consistency.py`.

## Run it

From the Courtvision project directory:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## What changed

- Off-white / charcoal / orange responsive editorial design based on the selected Kobe-style direction.
- Official NBA CDN headshots (`https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png`), without AI-generated player photos. If no headshot exists, the placeholder background remains.
- Selectable regular season for each player's analysis and separately for each side in comparisons.
- Session-state persistence during tab switching and Streamlit reruns.
- Preserved comparison tables, grouped production and percentage charts, scoring consistency, recent form, and performance insight.
- Added a basic Saved Players tab reading the SQLite database.
- Added a check so one recorded game is not presented as a reliable scoring-consistency measurement.

## Important boundaries

- This package was **syntax-checked**, but full Streamlit runtime and NBA endpoint calls were not available in the assembly environment. Please test locally before treating it as release-ready.
- Some professional players, especially historic/retired ones, may not have an available NBA CDN headshot. The app will not invent images.
- This uses an independently branded dashboard, not Nike artwork, proprietary Nike campaign assets, or an official NBA website theme.
- The historical season dropdown depends on NBA career data; sometimes an NBA endpoint has missing or unavailable season game logs.
- The new optional `season` parameter in `calculate_stats(career_data, season=None)` maintains the old call signature used by your unit tests.
- `courtvision.db` is intentionally excluded from Git. Never upload your database, `.venv`, or backup files.

## Tests to run

1. `python test_consistency.py` — confirm old unit tests pass.
2. Analyze a current player in the newest season and in an older season.
3. Analyze Kobe Bryant in a historical season and confirm the season selector responds.
4. Compare two different players; change both season dropdowns.
5. Enter an invalid player and compare the same player to themself; confirm friendly validation.
6. Check a one-game season; confirm the scoring consistency notice.
7. Refresh and switch between tabs; confirm selected players remain available.
8. Check database persistence; see that old records still exist.
