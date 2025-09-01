import os
import sys
import time
import re
import pygame

# --- Configuration (Same as before) ---
SAVE_DIR = "C:\\Users\\owner\\AppData\\LocalLow\\Freehold Games\\CavesOfQud"
SAVE_UID = "0469531a-048d-4549-b26d-88034706eeac"
LOCATIONS_CSV = 'cities.csv'

# --- Pygame Display Configuration ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
BASE_CELL_SIZE = 8  # The default size of a cell at 1.0 zoom
PARSANG_X_MAX = 80
PARSANG_Y_MAX = 25
ZONE_DIM = 3

# --- Zoom & Pan Configuration ---
ZOOM_SPEED = 0.1
MIN_ZOOM = 0.2
MAX_ZOOM = 10.0

# --- Colors (RGB Tuples) ---
COLOR_MAP = {
    'grey': (128, 128, 128),
    'lightgrey': (211, 211, 211),
    'magenta': (255, 0, 255),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
}
GRID_BASE_COLOR = (40, 40, 40)
PARSANG_GRID_COLOR = (80, 80, 80)
CURRENT_LOC_BORDER_COLOR = (255, 255, 0)

# --- Global Data Structures ---
zones = {}
current_location_str = "None"

# --- Utility & Core Logic Functions (Mostly unchanged) ---

def trim(s: str) -> str:
    return s.strip()

# "#0011FF" # Blue

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return COLOR_MAP['white']

def read_player_log():
    global current_location_str
    player_log_file = os.path.join(SAVE_DIR, "Player.log")
    if not os.path.exists(player_log_file):
        return

    for loc_data in zones.values():
        loc_data.pop('current', None)

    current_location = None
    log_pattern = re.compile(r"INFO - Finished '(?:Thawing|Building) .+\.(\d+\.\d+\.\d+\.\d+\.\d+)'")
    try:
        with open(player_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = log_pattern.search(line)
                if match:
                    zone_loc = match.group(1)
                    zones.setdefault(zone_loc, {})['color'] = 'grey'
                    current_location = zone_loc
        if current_location:
            zones[current_location]['color'] = 'magenta'
            zones[current_location]['current'] = True
            current_location_str = current_location
        else:
            current_location_str = "None"
    except IOError as e:
        print(f"Error reading Player.log file: {e}")

def add_locations_from_csv():
    filename = os.path.join(SAVE_DIR, LOCATIONS_CSV)
    if not os.path.exists(filename):
        print("Warning - cities.csv file not found\n")
        return
    csv_pattern = re.compile(r"^(\d{1,2}\.\d{1,2}\.\d\.\d\.\d{1,2}),(.+),(.+)$")
    try:
        print("Loading cities.csv file")
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                match = csv_pattern.match(trim(line))
                if match:
                    zone_loc, color, name = (trim(g) for g in match.groups())
                    print(f"Loading {name} {zone_loc}\n")
                    zones[zone_loc] = {'name': name, 'color': color}
    except IOError as e:
        print(f"Error reading locations CSV file: {e}")

# --- Pygame Drawing & Transformation Functions ---

def world_to_screen(world_x, world_y, zoom, camera_offset):
    """Converts world coordinates (in pixels) to screen coordinates."""
    screen_x = (world_x * zoom) - camera_offset[0]
    screen_y = (world_y * zoom) - camera_offset[1]
    return int(screen_x), int(screen_y)

def screen_to_world(screen_x, screen_y, zoom, camera_offset):
    """Converts screen coordinates to world coordinates (in pixels)."""
    world_x = (screen_x + camera_offset[0]) / zoom
    world_y = (screen_y + camera_offset[1]) / zoom
    return world_x, world_y

def draw_map(screen, zoom, camera_offset):
    """Draws only the visible portion of the map grid."""
    effective_cell_size = BASE_CELL_SIZE * zoom
    ZONE_DEPTH = 10

    # --- Optimization: Calculate which cells are visible ---
    cam_x, cam_y = camera_offset
    # Get the world coordinates of the top-left and bottom-right of the screen
    world_tl_x, world_tl_y = screen_to_world(0, 0, zoom, camera_offset)
    world_br_x, world_br_y = screen_to_world(SCREEN_WIDTH, SCREEN_HEIGHT, zoom, camera_offset)

    # Determine the range of grid cells to draw
    start_gx = max(0, int(world_tl_x / BASE_CELL_SIZE))
    start_gy = max(0, int(world_tl_y / BASE_CELL_SIZE))
    end_gx = min(PARSANG_X_MAX * ZONE_DIM, int(world_br_x / BASE_CELL_SIZE) + 1)
    end_gy = min(PARSANG_Y_MAX * ZONE_DIM, int(world_br_y / BASE_CELL_SIZE) + 1)

    for grid_y in range(start_gy, end_gy):
        for grid_x in range(start_gx, end_gx):
            parsang_x, zone_x = divmod(grid_x, ZONE_DIM)
            parsang_y, zone_y = divmod(grid_y, ZONE_DIM)

            # Convert grid coordinates to world pixel coordinates
            world_x = grid_x * BASE_CELL_SIZE
            world_y = grid_y * BASE_CELL_SIZE

            # Convert world pixel coordinates to screen coordinates
            screen_x, screen_y = world_to_screen(world_x, world_y, zoom, camera_offset)

            rect = pygame.Rect(screen_x, screen_y, int(effective_cell_size), int(effective_cell_size))

            zone_loc = f"{parsang_x}.{parsang_y}.{zone_x}.{zone_y}.{ZONE_DEPTH}"
            zone_data = zones.get(zone_loc, {})

            color_str = zone_data.get('color')
            final_color = GRID_BASE_COLOR
            if color_str:
                final_color = hex_to_rgb(color_str) if color_str.startswith('#') else COLOR_MAP.get(color_str, GRID_BASE_COLOR)

            pygame.draw.rect(screen, final_color, rect)

            if zone_data.get('current'):
                pygame.draw.rect(screen, CURRENT_LOC_BORDER_COLOR, rect, width=max(1, int(2 * zoom)))

def draw_grid_lines(screen, zoom, camera_offset):
    """Draws only the visible parsang grid lines."""
    effective_cell_size = BASE_CELL_SIZE * zoom
    if effective_cell_size < 4: return # Don't draw grid if cells are too small

    # Similar optimization logic as draw_map
    world_tl_x, world_tl_y = screen_to_world(0, 0, zoom, camera_offset)
    world_br_x, world_br_y = screen_to_world(SCREEN_WIDTH, SCREEN_HEIGHT, zoom, camera_offset)
    
    # Vertical lines
    start_parsang_x = max(0, int(world_tl_x / (BASE_CELL_SIZE * ZONE_DIM)))
    end_parsang_x = min(PARSANG_X_MAX, int(world_br_x / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for i in range(start_parsang_x, end_parsang_x + 1):
        world_x = i * ZONE_DIM * BASE_CELL_SIZE
        start_pos = world_to_screen(world_x, world_tl_y, zoom, camera_offset)
        end_pos = world_to_screen(world_x, world_br_y, zoom, camera_offset)
        pygame.draw.line(screen, PARSANG_GRID_COLOR, start_pos, end_pos)
    
    # Horizontal lines
    start_parsang_y = max(0, int(world_tl_y / (BASE_CELL_SIZE * ZONE_DIM)))
    end_parsang_y = min(PARSANG_Y_MAX, int(world_br_y / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for i in range(start_parsang_y, end_parsang_y + 1):
        world_y = i * ZONE_DIM * BASE_CELL_SIZE
        start_pos = world_to_screen(world_tl_x, world_y, zoom, camera_offset)
        end_pos = world_to_screen(world_br_x, world_y, zoom, camera_offset)
        pygame.draw.line(screen, PARSANG_GRID_COLOR, start_pos, end_pos)

def draw_hud(screen, font):
    """Draws the Heads-Up Display with info and controls."""
    info_text = [
        f"Current: {current_location_str}",
        "Controls:",
        "  Mouse Wheel to Zoom",
        "  Middle-Click + Drag to Pan"
    ]
    y_offset = 10
    for i, line in enumerate(info_text):
        text_surface = font.render(line, True, COLOR_MAP['white'], COLOR_MAP['black'])
        screen.blit(text_surface, (10, y_offset))
        y_offset += font.get_height()

# --- Main Program Loop ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Caves of Qud - Live Parsang Map")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    # --- State Variables for Camera ---
    zoom_level = 1.0
    camera_offset = [0, 0]
    is_panning = False
    pan_start_pos = (0, 0)

    # Initial Data Load
    print("Loading initial location data...")
    add_locations_from_csv()
    read_player_log()

    # Timer for Log File Polling
    UPDATE_LOG_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(UPDATE_LOG_EVENT, 5000)

    # The Main Loop
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == UPDATE_LOG_EVENT:
                print("Checking for updates in Player.log...")
                read_player_log()

            # --- Zooming Logic ---
            if event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                world_pos_before_zoom = screen_to_world(mouse_pos[0], mouse_pos[1], zoom_level, camera_offset)

                if event.y > 0: # Scroll up to zoom in
                    zoom_level *= (1 + ZOOM_SPEED)
                else: # Scroll down to zoom out
                    zoom_level /= (1 + ZOOM_SPEED)
                zoom_level = max(MIN_ZOOM, min(MAX_ZOOM, zoom_level)) # Clamp zoom

                world_pos_after_zoom = screen_to_world(mouse_pos[0], mouse_pos[1], zoom_level, camera_offset)
                
                # Adjust camera to keep mouse position fixed relative to the world
                camera_offset[0] += (world_pos_after_zoom[0] - world_pos_before_zoom[0]) * zoom_level
                camera_offset[1] += (world_pos_after_zoom[1] - world_pos_before_zoom[1]) * zoom_level

            # --- Panning Logic ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # Middle mouse button
                is_panning = True
                pan_start_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                is_panning = False
            if event.type == pygame.MOUSEMOTION and is_panning:
                dx = event.pos[0] - pan_start_pos[0]
                dy = event.pos[1] - pan_start_pos[1]
                camera_offset[0] -= dx
                camera_offset[1] -= dy
                pan_start_pos = event.pos

        # --- Drawing ---
        screen.fill(GRID_BASE_COLOR)
        draw_map(screen, zoom_level, camera_offset)
        draw_grid_lines(screen, zoom_level, camera_offset)
        draw_hud(screen, font)
        
        # --- Update Display ---
        pygame.display.flip()
        clock.tick(60) # Limit to 60 FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()