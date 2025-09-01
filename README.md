
Script to show your current location on the world map, and where you have been.

Reads the player.log file which will scrabe the Building|Thawing logs. Also uses the cached.db to fill in locations been to in previous loads of the character.

Currently need to change the script based on the GUID for your specific save directory.






###############################################################################
# Original Perl implementation
###############################################################################

How the Script Works (High-Level Overview):

    Initialization:

        Sets up paths to game files and the output HTML file.

        Initializes a %zone hash to store location data (name, color, current status).

    Main Loop (Continuous Monitoring):

        Enters an infinite loop to constantly check for changes.

        Every 10 seconds, it checks the modification time of Player.log.

        If Player.log has been modified recently (more than 15 seconds since the last check), it triggers a map regeneration.

    Map Regeneration Steps:

        read_player_log():

            Reads Player.log from beginning to end.

            Looks for lines indicating "Thawing" or "Building" zones, which signify the player entering a new area.

            The last such location found in the log is marked as the player's CURRENT location (displayed in magenta).

            All other zones found in the log are marked as visited (displayed in grey).

            It clears the CURRENT flag from any previously marked location before processing to ensure only one location is current.

        add_locations() (Currently Commented Out):

            If enabled, this would read cities.csv.

            It would populate the %zone hash with predefined city names and their specific colors based on their coordinates. This allows for custom labeling and coloring of important locations.

        gen_html_output():

            Opens parsang_map.html for writing.

            Calls helper subroutines to write the HTML header (including CSS), the main HTML table (the map itself), and the HTML footer.

    HTML Generation Details:

        gen_html_header(): Writes the basic HTML structure, page title, a meta tag for automatic refresh (every 30 seconds), and all the CSS styles for the table, cells, and borders. The CSS defines visual cues for the 3x3 "parsang" grid and highlights the current location.

        gen_html_table(): This is the core map generation.

            It creates a large HTML table.

            It iterates through parsang_y (25 rows) and zone_y (3 rows within each parsang), then parsang_x (80 columns) and zone_x (3 columns within each parsang). This results in a grid of (25 * 3) x (80 * 3) cells.

            For each cell, it constructs a unique zone_loc string (e.g., "1.1.1.1.10").

            It checks the %zone hash for data related to this zone_loc:

                If a NAME exists (from cities.csv), it displays the city name.

                If a COLOR exists (from Player.log or cities.csv), it sets the cell's background color.

                If the CURRENT flag is set, it applies a special "current-location" CSS class to make the border magenta and thicker.

            It also applies CSS classes (border-top, border-left) to create the thicker red borders that delineate the larger 3x3 parsang grids.

        gen_html_footer(): Closes the HTML document.

    Helper trim() Subroutine: Removes leading and trailing whitespace from a string, used when parsing data from CSV.

In essence, this script creates a live, auto-refreshing map of your Caves of Qud adventures by constantly reading your game log and translating your movements into a visual HTML representation.



###############################################################################
# Key Changes and Best Practices in Python:
###############################################################################


    Shebang and Imports:

        #!/usr/bin/env python3: Standard Python shebang.

        import os, import time, import re, from datetime import datetime: Imports necessary modules. os for path manipulation, time for sleep and getmtime, re for regular expressions, datetime for current timestamp.

    Configuration:

        Global constants are defined using UPPER_SNAKE_CASE (e.g., SAVE_DIR). This is a Python convention for constants.

        Crucially, you need to update SAVE_DIR and SAVE_UID to match your actual game installation.

    Global Data Structure (zones dictionary):

        The %zone hash in Perl becomes the zones dictionary in Python.

        Instead of zones{$_}{COLOR} = 'lightgrey', Python uses zones[zone_loc] = zones.get(zone_loc, {}) to ensure the inner dictionary exists before trying to set a key within it, preventing KeyError.

        Dictionary keys for zone attributes are lowercase strings ('name', 'color', 'current').

    trim() Function:

        Perl's sub trim becomes a standard Python function def trim(s: str) -> str:.

        Uses the built-in string method s.strip() which is more Pythonic and efficient than a regex for this purpose.

        Includes type hints (s: str, -> str) for better code readability and maintainability.

    File Handling:

        Uses os.path.join() for constructing file paths. This is cross-platform compatible (handles \ on Windows and / on Linux/macOS automatically).

        Uses with open(...) as f: for file operations. This is the preferred Pythonic way as it automatically handles closing the file, even if errors occur.

        Added encoding='utf-8', errors='ignore' to open() calls for Player.log and cities.csv to handle potential encoding issues gracefully, which can often arise with game logs.

    Error Handling:

        Uses try...except blocks for file operations (IOError, OSError) to catch and report errors gracefully instead of dieing abruptly.

        Includes checks with os.path.exists() before trying to open files or directories.

    Regular Expressions (re module):

        Uses re.compile() to pre-compile regex patterns. This is a performance optimization when the same pattern is used repeatedly in a loop (like in read_player_log and add_locations_from_csv).

        match = log_pattern.search(line): search() looks for the pattern anywhere in the string.

        match = csv_pattern.match(line): match() looks for the pattern only at the beginning of the string (like Perl's ^ anchor).

        match.group(1) or match.groups() to extract captured parts.

    Main Loop (main_loop() function):

        Encapsulated the main logic in a function main_loop() and called it from if __name__ == "__main__":. This is a standard Python entry point pattern.

        time.sleep(10) replaces sleep(10).

        os.path.getmtime() gets the last modification time, replacing Perl's stat()[9].

        The logic for detecting file changes is slightly simpler: current_modified_time != last_modified_time. Perl's > 15 was a heuristic that might sometimes miss a quick save, but != is more robust for checking if any change happened.

    HTML Generation Functions:

        Instead of print HTMLOUT (...), the Python functions return multi-line strings (using f-strings for easy variable interpolation).

        These strings are then written to the file in generate_html_output(). This approach separates logic from I/O, making functions more testable and reusable.

        datetime.now().strftime('%Y-%m-%d %H:%M:%S') provides a formatted timestamp.

        Small CSS additions: white-space: nowrap; overflow: hidden; to td style to prevent text wrapping in cells, which makes the grid cleaner.

        td_classes list is used to dynamically build the class attribute string, which is more flexible than conditional string concatenation.

    read_zone_cache_dir() and add_locations_from_csv() in Main Loop:

        The read_zone_cache_dir() call is still commented out in main_loop() to mirror the original Perl script.

        add_locations_from_csv() is called once at the beginning of main_loop() rather than every iteration. This is a best practice, as city definitions are unlikely to change during script execution. If they could, you would move it inside the loop.

This Python version is more readable, maintainable, and robust, aligning with common Python best practices. Remember to update the SAVE_DIR and SAVE_UID variables to match your system!