# AION 2 Farmer

Windows-first modular automation project for AION 2 PC mode.

## Architecture

The bot is built around a state-provider architecture:

`StateProvider -> GameState -> DecisionEngine -> Actions`

The provider contract exposes game state without coupling decision logic to a particular acquisition method.

### Providers

- `VisualStateProvider`: current calibrated screen/HUD implementation.
- `SimulatedStateProvider`: deterministic provider for tests and development.

The architecture is intentionally ready for an **authorized** game-state source/API in the future. It does not include memory injection, anti-cheat bypasses, or process tampering.

## Implemented

- Farming loop: target -> approach -> combat -> loot -> recovery.
- Player HP/MP monitoring.
- Selected target HP monitoring.
- Blocked UI detection.
- Target-loss confirmation before loot.
- Retarget fallback when no target is acquired.
- No-damage approach pulses.
- Scheduled basic attack and skills.
- Built-in auto-potion activation.
- Native Windows SendInput.
- Foreground-window safety guard.
- Low-cost regional screen capture.
- Dry-run mode.
- JSON configuration.
- Unit tests and GitHub Actions CI.
- Windows launcher and PyInstaller build.

## Configuration

`config/default.json` contains the default settings.

Important values:

- `state_provider`: `visual` or `simulated`.
- `dry_run`: keep `true` for initial testing.
- `skill_keys`: class-specific skill rotation.
- `combat_timeout_s`: fallback before retargeting.
- `low_hp_ratio` / `resume_hp_ratio`: recovery thresholds.
- `enable_auto_potion`: use AION 2's built-in auto-potion.
- `game_window_title_contains`: real-input safety guard.

## Windows

Run `start_windows.bat` to prepare the environment.

Build:

`build_windows.bat`

Output:

`dist/AION2-Farmer.exe`

## Validation

The connected Windows 11 environment has been used to validate Python compilation, the state-machine tests, screen capture and Windows executable packaging.

Use automation only where it is permitted by the game's rules.
