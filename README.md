# Ping Widget

A lightweight, always-on-top desktop widget that shows a real-time ping latency graph — stays visible over all windows without stealing focus.

![Ping Widget](https://img.shields.io/badge/platform-Windows-blue) ![Python](https://img.shields.io/badge/python-3.12%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Real-time ping latency graph updated every second
- Configurable target IP via `ping_widget_config.json` (default: `8.8.8.8`)
- Transparent, frameless window — always on top, never blocks your workflow
- Stays visible even when clicking on the desktop
- System tray icon — double-click to show/hide, right-click to exit
- Drag to move, `Ctrl+Drag` to resize
- Window position and size saved between sessions
- Auto-repositions to top-right corner if saved position is off-screen (e.g. after monitor change)
- No subprocess or `ping.exe` — uses TCP socket for latency measurement (no DLL conflicts)

## Usage

### Download

Grab the latest `PingWidget-*.zip` from the [Releases](../../releases) page — no installation needed.

Extract the zip and run `PingWidget.exe`.

### Configuration

Edit `ping_widget_config.json` in the same folder as the exe:

```json
{
    "ping_target": "8.8.8.8",
    "ping_port": 53,
    "ping_timeout": 1.0
}
```

| Field | Description | Default |
|---|---|---|
| `ping_target` | IP or hostname to measure latency to | `8.8.8.8` |
| `ping_port` | TCP port used for connection | `53` |
| `ping_timeout` | Timeout in seconds per measurement | `1.0` |

If the config file is missing, defaults are used automatically.

### Run from source

```bash
pip install PySide6 matplotlib numpy
python ping_widget.py
```

## Controls

| Action | How |
|---|---|
| Move | Drag the small red dot (bottom-right corner) |
| Resize | `Ctrl` + Drag the red dot |
| Show / Hide | Double-click tray icon |
| Exit | Right-click tray icon → Exit, or right-click widget → Exit |

## Requirements

- Windows 10/11
- Python 3.12+ (if running from source)
