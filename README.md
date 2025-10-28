# YTM-RPC Setup Guide

## Overview
YTM-RPC provides a Discord Rich Presence integration for YouTube Music. It consists of two components:

- **Server**: A minimal CLI server written in Python.
- **Extension**: A custom, unpackaged browser extension for Chrome/Chromium-based browsers.

## Prerequisites

- Python 3.11+
- `pip` (Python package installer)
- A Chromium-based browser (e.g., Chrome, Edge)

## Installation

### 1. Clone the Repository

`git clone https://github.com/Louchatfroff/YTM-RPC.git
cd YTM-RPC`
### 2. Install Server Dependencies
`pip install -r requirements.txt`
### 3. Run the Server
`python server.py`

The server will start and listen for connections from the browser extension.

### 4. Install the Browser Extension
- Open your browser's extensions page (chrome://extensions/).
- Enable "Developer mode".
- Click "Load unpacked" and select the extension/ directory from the cloned repository.
- The extension will now communicate with the server to display your YouTube Music activity in Discord.

### Customization
Server: Modify server.py to adjust the data sent to Discord. Refer to the Discord Rich Presence documentation for available fields.
Extension: Edit the manifest.json and background.js files in the extension/ directory to change extension behavior or appearance.

License
This project is licensed under the Apache-2.0 License. See the LICENSE file for details.
