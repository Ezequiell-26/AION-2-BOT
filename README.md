# AION 2 Farmer

Windows-first automation bot for AION 2 PC mode.

## Implemented

- Farming cycle: select target -> approach -> combat rotation -> loot -> repeat.
- Default AION 2 controls:
  - W/A/S/D movement
  - Tab target selection
  - Left mouse basic attack
  - F interaction/loot
  - X auto-potion toggle
- Configurable skill rotation through keys 1-8.
- Auto-potion activation at bot start.
- Recovery mode stops movement and waits for the in-game potion system instead of repeatedly toggling X.
- Active-window guard: when real input is enabled, input is only sent while the active window title contains "AION 2".
- F8 pause/resume and F9 emergency stop.
- Screen capture layer via mss.
- Dry-run mode for safe testing.
- JSON configuration.
- Unit tests and GitHub Actions CI.
- Windows launcher and PyInstaller build script.

## Important limitation

This repository deliberately does not pretend that arbitrary pixels are enough to reliably identify every mob, HP bar, death screen, loot prompt, or UI state. Those detections need calibration against the user's current AION 2 client resolution/UI.

The current farming engine therefore uses AION 2's deterministic PC controls and a configurable combat timeout. In real use, set the combat timeout close to the actual kill time for the chosen farming spot. The next reliability step is a calibrated screen profile that detects target/HP/death/loot state directly.

## Windows setup

1. Install Python 3.11, 3.12 or 3.13.
2. Extract the repository.
3. Run `start_windows.bat`.
4. Keep AION 2 in a dedicated game window.
5. Start with `dry_run: true`.
6. For real input, set `dry_run: false`.

Before the first real run, make sure AION 2's built-in auto-potion option is OFF so the bot's startup `X` toggle turns it ON deterministically.

Build the standalone executable with:

```bat
build_windows.bat
```

Output:

```text
dist\\AION2-Farmer.exe
```

The executable should be built on Windows; PyInstaller is not a cross-compiler.

## Configuration

Copy:

```text
config\\default.json
```

to:

```text
config\\config.local.json
```

and edit the local file.

Useful values:

- `combat_timeout_s`: maximum time spent attacking one target before looting.
- `approach_pulse_s`: forward movement after target selection.
- `skill_keys`: class-specific rotation.
- `skill_interval_s`: delay between skill presses.
- `loot_pulses`: number of F presses per loot cycle.
- `enable_auto_potion`: whether the bot toggles AION 2 auto-potion at start.
- `game_window_title_contains`: input safety guard.

## Testing

Run:

```bat
python -m compileall -q .
python -m pip install -r requirements.txt
python -m pip install pytest
pytest -q tests
```

Use automation only where it is permitted by the game's rules.
