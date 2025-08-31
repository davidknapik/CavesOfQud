
import os
import time
import re
from datetime import datetime

# --- Configuration ---
# Define the base directory for Caves of Qud game saves and logs.
# This path is specific to a Windows user.
# IMPORTANT: Adjust this path to your actual Caves of Qud save directory.
SAVE_DIR = "C:\\Users\\owner\\AppData\\LocalLow\\Freehold Games\\CavesOfQud"

# Define the unique ID for a specific game save.
# You can find this in your SAVE_DIR/Saves/ directory (it's the folder name).
SAVE_UID = "0469531a-048d-4549-b26d-88034706eeac"

# Define the name of the output HTML file for the map.
HTML_FILE = 'parsang_map.html'

# Define the name of the CSV file containing known city locations.
# This file should be located in the SAVE_DIR.
LOCATIONS_CSV = 'cities.csv'

# --- Global Data Structure (using a dictionary for zones) ---
# A dictionary to store information about game zones.
# Keys will be zone coordinates (e.g., "1.1.1.1.10").
# Values will be dictionaries containing 'name', 'color', and 'current' status.
zones = {}

# --- Utility Functions ---

def trim(s: str) -> str:
    """
    Trims leading and trailing whitespace from a string.
    """
    return s.strip()

# --- Core Logic Functions ---

# This function is equivalent to Perl's 'read_cache_dir' and is currently unused
# in the main loop, mirroring the commented-out status in the original Perl.
# It's included here for completeness if you decide to use it later.
def read_zone_cache_dir():
    """
    Reads filenames from the game's ZoneCache directory.
    Marks these zones as 'lightgrey' (visited) in the global 'zones' dictionary.
    """
    zone_cache_dir = os.path.join(SAVE_DIR, "Saves", SAVE_UID, "ZoneCache")

    if not os.path.exists(zone_cache_dir):
        print(f"Warning: ZoneCache directory not found: {zone_cache_dir}")
        return

    try:
        # List all files and directories in the ZoneCache.
        # Filter for actual zone files.
        zone_files = [f for f in os.listdir(zone_cache_dir) if f.endswith(".zone.gz")]

        for filename in zone_files:
            # Remove "JoppaWorld." prefix and ".zone.gz" suffix to get the pure zone coordinate.
            zone_loc = filename.replace("JoppaWorld.", "").replace(".zone.gz", "")
            zones[zone_loc] = zones.get(zone_loc, {}) # Ensure the inner dict exists
            zones[zone_loc]['color'] = 'lightgrey'
    except OSError as e:
        print(f"Error reading ZoneCache directory {zone_cache_dir}: {e}")

def read_player_log():
    """
    Parses the Player.log file to find the player's current and recently visited zones.
    Updates the global 'zones' dictionary with color and current status.
    """
    player_log_file = os.path.join(SAVE_DIR, "Player.log")

    if not os.path.exists(player_log_file):
        print(f"Error: Player.log not found at {player_log_file}")
        return

    # Unset the 'current' flag for all previously known zones.
    for loc_data in zones.values():
        if 'current' in loc_data:
            del loc_data['current']

    current_location = None
    # Regex to capture the zone coordinate from log lines indicating zone loading.
    # e.g., "INFO - Finished 'Thawing Zone 1.1.1.1.10'"
    log_pattern = re.compile(r"INFO - Finished '(?:Thawing|Building) \b.+\.(\d+\.\d+\.\d+\.\d+\.\d+)'")

    try:
        with open(player_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Read all lines and process them to find the last known location.
            # This ensures we get the *most recent* location even if the log is large.
            for line in f:
                match = log_pattern.search(line)
                if match:
                    zone_loc = match.group(1)
                    zones[zone_loc] = zones.get(zone_loc, {}) # Ensure the inner dict exists
                    zones[zone_loc]['color'] = 'grey' # Mark as visited
                    current_location = zone_loc # Update the last found location

        if current_location:
            # Set the last found location as the current one (magenta).
            zones[current_location]['color'] = 'magenta'
            zones[current_location]['current'] = True
            print(f"Current Location: {current_location}")
        else:
            print("No current location found in Player.log.")

    except IOError as e:
        print(f"Error reading Player.log file {player_log_file}: {e}")

def add_locations_from_csv():
    """
    Reads known city/site locations from the 'cities.csv' file.
    Populates the global 'zones' dictionary with names and specific colors.
    CSV format: Location,Color,Name (e.g., 11.22.1.1.10,#554f97,Joppa)
    """
    filename = os.path.join(SAVE_DIR, LOCATIONS_CSV)

    if not os.path.exists(filename):
        print(f"Warning: Locations CSV file not found at {filename}")
        return

    # Regex to parse the CSV line: captures location, color, and name.
    csv_pattern = re.compile(r"^(\d{1,2}\.\d{1,2}\.\d\.\d\.\d{1,2}),(.+),(.+)$")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = trim(line) # Trim leading/trailing whitespace from the line
                match = csv_pattern.match(line)
                if match:
                    zone_loc, color, name = match.groups()
                    zone_loc = trim(zone_loc)
                    color = trim(color)
                    name = trim(name)

                    zones[zone_loc] = zones.get(zone_loc, {}) # Ensure the inner dict exists
                    zones[zone_loc]['name'] = name
                    zones[zone_loc]['color'] = color
    except IOError as e:
        print(f"Error reading locations CSV file {filename}: {e}")

# --- HTML Generation Functions ---

def generate_html_header() -> str:
    """
    Generates the HTML <head> section with title, auto-refresh, and CSS styles.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>CavesOfQud Parsang Map</title>
    <meta http-equiv="refresh" content="30">
    <style>
        table {{
            font-family: arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
        }}
        th {{
            background-color: lightslategrey;
            border: 4px solid #d70513;
            position: sticky;
            top: 0;
            left: 0;
            text-align: center;
            padding: 8px;
        }}
        td {{
            border: 1px solid #dddddd;
            text-align: center;
            text-overflow: ellipsis;
            padding: 8px;
            white-space: nowrap; /* Prevent text wrapping in cells */
            overflow: hidden; /* Hide overflow */
        }}
        tr.border-bottom {{
            border-bottom: solid 4px #d70513;
        }}
        tr.border-top {{
            border-top: solid 4px #d70513;
        }}
        td.border-left {{
            border-left: solid 4px #d70513;
        }}
        td.border-right {{
            border-right: solid 4px #d70513;
        }}
        td.border-top {{
            border-top: solid 4px #d70513;
        }}
        td.border-bottom {{
            border-bottom: solid 4px #d70513;
        }}
        td.current-location {{
            border: solid 8px #f817d6;
        }}
    </style>
</head>
"""

def generate_html_table() -> str:
    """
    Generates the main HTML table content representing the map.
    """
    html_content = []
    html_content.append("<body>")
    html_content.append("\t<center><h1>Caves Of Qud Parsang Map</h1></center>")
    html_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    html_content.append("\t<table>")

    ZONE_DEPTH = 10
    PARSANG_X_MAX = 80
    PARSANG_Y_MAX = 25
    ZONE_DIM = 3 # 0, 1, 2 for x and y

    # Output map header row (Parsang X and Zone X labels)
    html_content.append("\t\t<tr>")
    html_content.append("\t\t\t<th>&nbsp;</th>") # Top-left empty cell
    for parsang_x in range(PARSANG_X_MAX):
        for zone_x in range(ZONE_DIM):
            html_content.append(f"<th>{parsang_x}.{zone_x}</th>")
    html_content.append("\t\t</tr>")

    # Output map data rows
    for parsang_y in range(PARSANG_Y_MAX):
        for zone_y in range(ZONE_DIM):
            tr_class = 'class="border-top"' if zone_y == 0 else ''
            html_content.append(f"\t\t<tr {tr_class}>")
            html_content.append(f"\t\t\t<th>{parsang_y}.{zone_y}</th>") # Row index (Parsang Y and Zone Y)

            for parsang_x in range(PARSANG_X_MAX):
                for zone_x in range(ZONE_DIM):
                    td_classes = []
                    if zone_x == 0:
                        td_classes.append("border-left")

                    zone_loc = f"{parsang_x}.{parsang_y}.{zone_x}.{zone_y}.{ZONE_DEPTH}"
                    zone_data = zones.get(zone_loc, {})

                    td_str = zone_data.get('name', '&nbsp;')
                    td_bgcolor = ''

                    if 'color' in zone_data:
                        if zone_data.get('current'):
                            td_classes.append("current-location")
                            # If it's the current location and has no name, show coordinates.
                            # The Perl script commented this out, so we'll mirror that.
                            # if td_str == '&nbsp;':
                            #     td_str = f"{parsang_x}.{zone_x} {parsang_y}.{zone_y}"
                        td_bgcolor = f"bgcolor=\"{zone_data['color']}\""

                    td_class_str = f"class=\"{' '.join(td_classes)}\"" if td_classes else ''
                    html_content.append(f"<td {td_class_str} {td_bgcolor}>{td_str}</td>")
            html_content.append("\t\t</tr>")

    html_content.append("\t</table>")
    html_content.append("</body>")
    return "\n".join(html_content)

def generate_html_footer() -> str:
    """
    Generates the HTML </html> closing tag.
    """
    return "</html>"

def generate_html_output():
    """
    Combines header, table, and footer to create the complete HTML map file.
    """
    try:
        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(generate_html_header())
            f.write(generate_html_table())
            f.write(generate_html_footer())
        print(f"HTML map generated successfully to {HTML_FILE}")
    except IOError as e:
        print(f"Error writing HTML file {HTML_FILE}: {e}")

# --- Main Program Loop ---

def main_loop():
    """
    The main execution loop that monitors the Player.log file
    and regenerates the HTML map when changes are detected.
    """
    last_modified_time = 0
    # The Perl script had `read_cache_dir()` commented out, so we will too.
    # If you want to initially load zones from the cache, uncomment the line below.
    # read_zone_cache_dir()

    # The Perl script also had `add_locations()` commented out in the loop,
    # but it's common to load these at startup. Let's load them once here.
    add_locations_from_csv()

    while True:
        player_log_path = os.path.join(SAVE_DIR, "Player.log")

        if not os.path.exists(player_log_path):
            print(f"Waiting for Player.log to exist at {player_log_path}...")
            time.sleep(10)
            continue

        try:
            current_modified_time = os.path.getmtime(player_log_path)
            # Compare modification times. The Perl script used a difference of 15 seconds.
            # We'll use a simple inequality for more responsiveness.
            if current_modified_time != last_modified_time:
                print(f"Detected file change in Player.log... Regenerating map {current_modified_time}")

                read_player_log()
                # If you want to re-read cities.csv on every change (unlikely to be needed), uncomment below:
                # add_locations_from_csv()
                generate_html_output()

                last_modified_time = current_modified_time
            else:
                # print("No change detected in Player.log. Waiting...") # Optional: uncomment for more verbose output
                pass # No change, just sleep

        except OSError as e:
            print(f"Error accessing Player.log at {player_log_path}: {e}")

        # Limit disk thrashing and CPU usage.
        time.sleep(5) # Sleep for 10 seconds

# --- Entry Point ---
if __name__ == "__main__":
    main_loop()
