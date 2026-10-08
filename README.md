# AION 2 Farmer

Windows-first automation bot for AION 2 PC mode.

## Implemented

- Farming loop: target -> approach -> combat -> loot -> repeat.
- Live HUD perception calibrated for the current 1360x768 layout.
- Player HP and MP monitoring.
- Selected target HP monitoring.
- Blocked UI/menu detection.
- Combat reacts to observed target health instead of relying only on a fixed delay.
- Confirmed target loss triggers loot.
- Failed target acquisition retries selection instead of falsely looting.
- No-damage approach pulses to close distance.
- Basic attack and skill rotation are scheduled independently so perception is not blocked by an 8-skill burst.
- Auto-potion activation is delayed until the AION 2 HUD is visible.
- Recovery stops movement and waits for the game's auto-potion system.
- Native Windows SendInput for keyboard/mouse.
- Foreground-window guard for real input.
- F8 pause/resume and F9 emergency stop.
- Two small capture regions instead of full-screen analysis for low CPU usage.
- Dry-run mode, JSON configuration, unit tests, CI, Windows launcher and PyInstaller build.

## Current reliability boundary

The bot has real HUD-based HP/MP/target detection, but it is calibrated to the visible PC HUD geometry and colors. Mob identity, pathfinding, loot confirmation, death/resurrection and inventory-full handling are not yet semantic computer-vision modules.

For a real farm run, use a dedicated farming location where Tab selects hostile mobs and the configured skill bar matches the character class. Keep dry_run=true for the first validation, then switch to false only after checking the configuration.

## Windows setup

1. Install Python 3.11, 3.12, 3.13 or 3.14.
2. Clone or extract the repository.
3. Run start_windows.bat.
4. Keep AION 2 in a dedicated game window.
5. Start with dry_run=true.
6. For real input, set dry_run=false.

Before the first real run, make sure AION 2's built-in auto-potion option is OFF so the bot's startup X toggle turns it ON deterministically.

Build the standalone executable with build_windows.bat.

Output: dist/AION2-Farmer.exe

PyInstaller should be run on Windows for a Windows executable.

## Configuration

Copy config/default.json to config/config.local.json and edit the local file.

Useful values:
- combat_timeout_s: fallback before retargeting.
- approach_pulse_s: forward movement pulse when no damage is observed.
- skill_keys: class-specific rotation.
- skill_interval_s: delay between skill casts.
- attack_pulse_s: basic-attack interval.
- loot_pulses: number of F presses after confirmed target loss.
- no_damage_approach_s: delay before another approach pulse.
- low_hp_ratio / resume_hp_ratio: recovery thresholds.
- enable_auto_potion: whether the bot toggles AION 2 auto-potion after HUD detection.
- game_window_title_contains: input safety guard.

## Validation performed

On the connected Windows 11 machine:
- Python bytecode compiled successfully.
- Unit tests: 7 passed.
- Screen capture verified at 1360x768.
- The executable built successfully with PyInstaller 6.22.3 and Python 3.14.7.
- The executable started successfully in dry-run mode and was responsive.

## Important

Use automation only where it is permitted by the game's rules.
