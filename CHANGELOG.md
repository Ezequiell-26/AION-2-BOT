# Changelog

## 2026-10-08
- Improved screen perception with full-resolution bar scanning for small HUD regions.
- Added separate HP/MP normalization to avoid using one maximum for both bars.
- Added EMA smoothing for transient HP/MP detection noise.
- Added HUD grace period to prevent one missed frame from forcing BLOCKED_UI.
- Added target confirmation and short target-loss grace to reduce target flicker.
- Added a game_active field to Perception so VisualStateProvider does not query the foreground window twice per cycle.
- Expanded tests from 8 to 10 cases covering pixel-run detection and EMA behavior.
- Verified Python compilation and pytest: 10 passed.
- Frida MCP validation performed against the bot process only; AION 2 process injection remains unsupported by the game.
