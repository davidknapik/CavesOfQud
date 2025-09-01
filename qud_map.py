import os
import sys
import time
import re
import pygame
import sqlite3

# --- Configuration (Same as before) ---
SAVE_DIR = "C:\\Users\\owner\\AppData\\LocalLow\\Freehold Games\\CavesOfQud"
SAVE_UID = "1cb0687f-93fc-4c45-b53a-a2a33a9e0e36"
LOCATIONS_CSV = 'cities.csv'

# --- Pygame Display Configuration ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
HEADER_SIZE = 30  # <-- NEW: Space in pixels for the top/bottom/left/right headers
BASE_CELL_SIZE = 8
PARSANG_X_MAX = 80
PARSANG_Y_MAX = 25
ZONE_DIM = 3

# --- Zoom & Pan Configuration ---
ZOOM_SPEED = 0.1
MIN_ZOOM = 0.2
MAX_ZOOM = 10.0

# --- Colors (RGB Tuples) ---
CACHED_LOC_COLOR = (44, 105, 129)
HEADER_BG_COLOR = (20, 20, 20) # <-- NEW: Background for header area
COLOR_MAP = {
    'cached': CACHED_LOC_COLOR,
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

# --- Utility & Core Logic Functions (Unchanged) ---
def trim(s: str) -> str:
    return s.strip()

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return COLOR_MAP['white']

def read_locations_from_cache_db():
    db_path = os.path.join(SAVE_DIR, "Synced\Saves", SAVE_UID, "cache.db")
    if not os.path.exists(db_path):
        print(f"Warning - {db_path} file not found, skipping historical data.\n")
        return
    print("Loading historical data from cache.db...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ZoneID FROM FrozenZone")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            zone_id_str = row[0]
            if zone_id_str and zone_id_str.startswith("JoppaWorld."):
                zone_loc = zone_id_str.replace("JoppaWorld.", "")
                zones.setdefault(zone_loc, {'color': 'cached'})
        print(f"Loaded {len(rows)} historical locations from cache.\n")
    except sqlite3.Error as e:
        print(f"Error reading cache.db file: {e}")

def read_player_log():
    global current_location_str
    player_log_file = os.path.join(SAVE_DIR, "Player.log")
    if not os.path.exists(player_log_file): return
    for loc_data in zones.values(): loc_data.pop('current', None)
    current_location = None
    log_pattern = re.compile(r"INFO - Finished '(?:Thawing|Building) JoppaWorld\.(\d+\.\d+\.\d+\.\d+\.\d+)'")
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
            print(f"Current Location: {current_location_str}\n")
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

def world_to_screen(world_x, world_y, zoom, camera_offset, map_area):
    """Converts world coordinates to screen coordinates, accounting for the map area offset."""
    screen_x = (world_x * zoom) - camera_offset[0] + map_area.left
    screen_y = (world_y * zoom) - camera_offset[1] + map_area.top
    return int(screen_x), int(screen_y)

def screen_to_world(screen_x, screen_y, zoom, camera_offset, map_area):
    """Converts screen coordinates to world coordinates, accounting for the map area offset."""
    world_x = (screen_x - map_area.left + camera_offset[0]) / zoom
    world_y = (screen_y - map_area.top + camera_offset[1]) / zoom
    return world_x, world_y

def draw_map(screen, zoom, camera_offset, map_area):
    """Draws only the visible portion of the map grid within the specified map_area."""
    effective_cell_size = BASE_CELL_SIZE * zoom
    ZONE_DEPTH = 10
    world_tl_x, world_tl_y = screen_to_world(map_area.left, map_area.top, zoom, camera_offset, map_area)
    world_br_x, world_br_y = screen_to_world(map_area.right, map_area.bottom, zoom, camera_offset, map_area)
    start_gx = max(0, int(world_tl_x / BASE_CELL_SIZE))
    start_gy = max(0, int(world_tl_y / BASE_CELL_SIZE))
    end_gx = min(PARSANG_X_MAX * ZONE_DIM, int(world_br_x / BASE_CELL_SIZE) + 1)
    end_gy = min(PARSANG_Y_MAX * ZONE_DIM, int(world_br_y / BASE_CELL_SIZE) + 1)
    for grid_y in range(start_gy, end_gy):
        for grid_x in range(start_gx, end_gx):
            parsang_x, zone_x = divmod(grid_x, ZONE_DIM)
            parsang_y, zone_y = divmod(grid_y, ZONE_DIM)
            world_x = grid_x * BASE_CELL_SIZE
            world_y = grid_y * BASE_CELL_SIZE
            screen_x, screen_y = world_to_screen(world_x, world_y, zoom, camera_offset, map_area)
            rect = pygame.Rect(screen_x, screen_y, int(effective_cell_size + 1), int(effective_cell_size + 1))
            zone_loc = f"{parsang_x}.{parsang_y}.{zone_x}.{zone_y}.{ZONE_DEPTH}"
            zone_data = zones.get(zone_loc, {})
            color_str = zone_data.get('color')
            final_color = GRID_BASE_COLOR
            if color_str:
                final_color = hex_to_rgb(color_str) if color_str.startswith('#') else COLOR_MAP.get(color_str, GRID_BASE_COLOR)
            pygame.draw.rect(screen, final_color, rect)
            if zone_data.get('current'):
                pygame.draw.rect(screen, CURRENT_LOC_BORDER_COLOR, rect, width=max(1, int(2 * zoom)))

def draw_grid_lines(screen, zoom, camera_offset, map_area):
    if BASE_CELL_SIZE * zoom < 4: return
    world_tl_x, world_tl_y = screen_to_world(map_area.left, map_area.top, zoom, camera_offset, map_area)
    world_br_x, world_br_y = screen_to_world(map_area.right, map_area.bottom, zoom, camera_offset, map_area)
    start_px = max(0, int(world_tl_x / (BASE_CELL_SIZE * ZONE_DIM)))
    end_px = min(PARSANG_X_MAX, int(world_br_x / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for i in range(start_px, end_px + 1):
        world_x = i * ZONE_DIM * BASE_CELL_SIZE
        start_pos = world_to_screen(world_x, world_tl_y, zoom, camera_offset, map_area)
        end_pos = world_to_screen(world_x, world_br_y, zoom, camera_offset, map_area)
        pygame.draw.line(screen, PARSANG_GRID_COLOR, start_pos, end_pos)
    start_py = max(0, int(world_tl_y / (BASE_CELL_SIZE * ZONE_DIM)))
    end_py = min(PARSANG_Y_MAX, int(world_br_y / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for i in range(start_py, end_py + 1):
        world_y = i * ZONE_DIM * BASE_CELL_SIZE
        start_pos = world_to_screen(world_tl_x, world_y, zoom, camera_offset, map_area)
        end_pos = world_to_screen(world_br_x, world_y, zoom, camera_offset, map_area)
        pygame.draw.line(screen, PARSANG_GRID_COLOR, start_pos, end_pos)

def draw_headers(screen, font, zoom, camera_offset, map_area):
    """Draws the parsang coordinate headers in the margins around the map area."""
    if BASE_CELL_SIZE * zoom < 6: return # Hide headers if too zoomed out
    
    # --- X-Axis Headers (Top and Bottom) ---
    world_tl_x, _ = screen_to_world(map_area.left, map_area.top, zoom, camera_offset, map_area)
    world_br_x, _ = screen_to_world(map_area.right, map_area.bottom, zoom, camera_offset, map_area)
    start_px = max(0, int(world_tl_x / (BASE_CELL_SIZE * ZONE_DIM)))
    end_px = min(PARSANG_X_MAX, int(world_br_x / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    
    for px in range(start_px, end_px):
        # Find the center of the parsang in world coordinates
        world_x = (px + 0.5) * ZONE_DIM * BASE_CELL_SIZE
        screen_x, _ = world_to_screen(world_x, 0, zoom, camera_offset, map_area)
        
        if map_area.left <= screen_x <= map_area.right:
            text = font.render(str(px), True, COLOR_MAP['lightgrey'])
            # Top header
            text_rect = text.get_rect(center=(screen_x, map_area.top / 2))
            screen.blit(text, text_rect)
            # Bottom header
            text_rect = text.get_rect(center=(screen_x, map_area.bottom + (SCREEN_HEIGHT - map_area.bottom) / 2))
            screen.blit(text, text_rect)

    # --- Y-Axis Headers (Left and Right) ---
    _, world_tl_y = screen_to_world(map_area.left, map_area.top, zoom, camera_offset, map_area)
    _, world_br_y = screen_to_world(map_area.right, map_area.bottom, zoom, camera_offset, map_area)
    start_py = max(0, int(world_tl_y / (BASE_CELL_SIZE * ZONE_DIM)))
    end_py = min(PARSANG_Y_MAX, int(world_br_y / (BASE_CELL_SIZE * ZONE_DIM)) + 1)

    for py in range(start_py, end_py):
        world_y = (py + 0.5) * ZONE_DIM * BASE_CELL_SIZE
        _, screen_y = world_to_screen(0, world_y, zoom, camera_offset, map_area)
        
        if map_area.top <= screen_y <= map_area.bottom:
            text = font.render(str(py), True, COLOR_MAP['lightgrey'])
            # Left header
            text_rect = text.get_rect(center=(map_area.left / 2, screen_y))
            screen.blit(text, text_rect)
            # Right header
            text_rect = text.get_rect(center=(map_area.right + (SCREEN_WIDTH - map_area.right) / 2, screen_y))
            screen.blit(text, text_rect)

def draw_hud(screen, font):
    info_text = [
        f"Current: {current_location_str}",
        "Controls:", "  Mouse Wheel to Zoom", "  Middle-Click + Drag to Pan"
    ]
    y_offset = 10
    for line in info_text:
        text_surface = font.render(line, True, COLOR_MAP['white'], COLOR_MAP['black'])
        screen.blit(text_surface, (10, y_offset))
        y_offset += font.get_height()

# --- Main Program Loop ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Caves of Qud - Live Parsang Map")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    header_font = pygame.font.SysFont("consolas", 14, bold=True)

    # --- NEW: Define the central map drawing area ---
    map_area = pygame.Rect(HEADER_SIZE, HEADER_SIZE, SCREEN_WIDTH - 2 * HEADER_SIZE, SCREEN_HEIGHT - 2 * HEADER_SIZE)

    zoom_level = 1.0
    camera_offset = [0, 0]
    is_panning = False
    pan_start_pos = (0, 0)

    print("Loading initial location data...")
    read_locations_from_cache_db()
    add_locations_from_csv()
    read_player_log()

    UPDATE_LOG_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(UPDATE_LOG_EVENT, 5000)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == UPDATE_LOG_EVENT:
                print("Checking for updates in Player.log...")
                read_player_log()
            if event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                world_pos_before_zoom = screen_to_world(mouse_pos[0], mouse_pos[1], zoom_level, camera_offset, map_area)
                zoom_factor = (1 + ZOOM_SPEED) if event.y > 0 else 1 / (1 + ZOOM_SPEED)
                zoom_level = max(MIN_ZOOM, min(MAX_ZOOM, zoom_level * zoom_factor))
                world_pos_after_zoom = screen_to_world(mouse_pos[0], mouse_pos[1], zoom_level, camera_offset, map_area)
                camera_offset[0] += (world_pos_after_zoom[0] - world_pos_before_zoom[0]) * zoom_level
                camera_offset[1] += (world_pos_after_zoom[1] - world_pos_before_zoom[1]) * zoom_level
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                is_panning = True
                pan_start_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                is_panning = False
            if event.type == pygame.MOUSEMOTION and is_panning:
                dx, dy = event.rel
                camera_offset[0] -= dx
                camera_offset[1] -= dy

        # --- Refactored Drawing Order ---
        # 1. Fill entire screen with header color
        screen.fill(HEADER_BG_COLOR)
        # 2. Fill the central map area with the map background color
        screen.fill(GRID_BASE_COLOR, map_area)
        # 3. Draw map tiles and grid lines (clipped to map_area by their internal logic)
        draw_map(screen, zoom_level, camera_offset, map_area)
        draw_grid_lines(screen, zoom_level, camera_offset, map_area)
        # 4. Draw the headers in the margins
        draw_headers(screen, header_font, zoom_level, camera_offset, map_area)
        # 5. Draw the HUD on top of everything
        draw_hud(screen, font)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()