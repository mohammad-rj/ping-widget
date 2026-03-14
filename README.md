# Ping Widget

A lightweight, always-on-top desktop widget that shows a real-time ping latency graph — stays visible over all windows without stealing focus.

![Ping Widget](https://img.shields.io/badge/platform-Windows-blue) ![Python](https://img.shields.io/badge/python-3.12%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Real-time ping graph (pings `8.8.8.8` every second)
- Transparent, frameless window — always on top, never blocks your workflow
- Stays visible even when clicking on the desktop
- System tray icon — double-click to show/hide, right-click to exit
- Drag to move, `Ctrl+Drag` to resize
- Window position and size saved between sessions
- Auto-repositions to screen center if saved position is off-screen (e.g. after monitor change)

## Usage

### Run from source

```bash
pip install PySide6 matplotlib numpy
python ping_widget.py
```

### Download

Grab the latest `PingWidget.exe` from the [Releases](../../releases) page — no installation needed.

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
