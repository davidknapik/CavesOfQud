# Caves of Qud - Live Parsang Map

A real-time, interactive map viewer for the game [Caves of Qud](https://www.cavesofqud.com/). This Python script reads your game's log and cache files to generate a live map that tracks your current location, previously visited areas, and custom landmarks across different Z-levels.

---

## Features

*   **Live Player Tracking:** Monitors the `Player.log` file to update your character's position on the map in real-time.
*   **Z-Level Filtering:** Automatically detects when you change depth (e.g., go underground) and redraws the map to show only the locations discovered at that Z-level.
*   **Historical Data:** Reads the `cache.db` file from your save game to display all zones you have visited in previous sessions, giving a complete picture of your explorations.
*   **Custom Landmarks:** Load custom locations, names, and colors from a `cities.csv` file to permanently mark important sites like villages, ruins, or lairs.
*   **Interactive Viewport:**
    *   **Zoom:** Use the **mouse wheel** to zoom in and out. The zoom is centered on your cursor for intuitive navigation.
    *   **Pan:** **Click and drag with the middle mouse button** to pan the map and explore the world.
*   **Dynamic Coordinate Headers:** The map is framed by row and column headers that display the major parsang coordinates, updating as you pan the view.
*   **Optimized Rendering:** Only the visible portion of the map is drawn to the screen, ensuring smooth performance even when zoomed in on the large world map.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.x:** Can be downloaded from the [official Python website](https://www.python.org/downloads/).
*   **Pygame:** A cross-platform set of Python modules designed for writing video games.

## Installation

1.  **Ensure Python is installed.** You can check this by opening a terminal or command prompt and typing `python --version`.

2.  **Install the Pygame library.** Open your terminal or command prompt and run the following command:
    ```sh
    pip install pygame
    ```

3.  **Download the script.** Save the `qud_map.py` file to a location of your choice on your computer.

## Configuration

You **must** configure the script to point to your Caves of Qud save directory before running it.

1.  **Open `qud_map.py`** in a text editor.

2.  **Locate the Configuration section** at the top of the file:
    ```python
    # --- Configuration (Same as before) ---
    SAVE_DIR = "C:\\Users\\owner\\AppData\\LocalLow\\Freehold Games\\CavesOfQud"
    SAVE_UID = "1cb0687f-93fc-4c45-b53a-a2a33a9e0e36"
    LOCATIONS_CSV = 'cities.csv'
    ```

3.  **Update `SAVE_DIR`:** Change the path to match your Caves of Qud installation. It is typically located in your user's `AppData\LocalLow` folder on Windows.

4.  **Update `SAVE_UID`:** This is the most important step.
    *   Navigate to your `SAVE_DIR` and open the `Saves` or `Synced\Saves` subfolder.
    *   Inside, you will find a folder with a long, unique name like `1cb0687f-93fc-4c45-b53a-a2a33a9e0e36`. This is your Save UID.
    *   Copy this folder name and paste it as the value for the `SAVE_UID` variable.

5.  **(Optional) Create `cities.csv`:**
    *   If you wish to add permanent landmarks, create a file named `cities.csv` inside your main `SAVE_DIR`.
    *   Each line in the file defines one landmark in the format: `coordinate,color,name`.
    *   **Example:** `77.23.1.0.10,#554f97,Joppa`
    *   This data has a high priority and will be displayed over historical and current session data.

## Usage

1.  Save your changes to the `qud_map.py` file after configuring the paths.
2.  Run the script from your terminal:
    ```sh
    python qud_map.py
    ```
3.  A Pygame window will open, displaying the world map.
4.  Launch and play Caves of Qud. The map will automatically update every 5 seconds to reflect your in-game movement and discoveries.

### Controls

*   **Zoom:** Use the **Mouse Wheel** up and down.
*   **Pan:** Click and hold the **Middle Mouse Button** and drag the mouse.

---

## How It Works

The script visualizes data from three different sources, loading them in a specific order of priority to ensure the map is accurate.

1.  **`cache.db` (Lowest Priority):** The SQLite database is read first to populate the map with all historically visited zones. These are displayed in a distinct color (dark teal).
2.  **`cities.csv` (Medium Priority):** The custom landmarks file is read next. Any location defined here will overwrite the historical data, allowing you to give important locations a permanent, custom color and name.
3.  **`Player.log` (Highest Priority):** The log for the current game session is monitored continuously. Data from this file (visited zones and current location) will overwrite all other data, ensuring that the map always reflects the state of your active game.

## License

This project is licensed under the MIT License.

## Acknowledgments

A big thank you to **Freehold Games** for creating the amazing and deeply immersive Caves of Qud.