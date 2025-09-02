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
HEADER_SIZE = 30
BASE_CELL_SIZE = 8
PARSANG_X_MAX = 80
PARSANG_Y_MAX = 25
ZONE_DIM = 3

# --- Zoom & Pan Configuration ---
ZOOM_SPEED = 0.5
MIN_ZOOM = 0.2
MAX_ZOOM = 10.0

# --- Colors (RGB Tuples) ---
CACHED_LOC_COLOR = (44, 105, 129)
HEADER_BG_COLOR = (20, 20, 20)
COLOR_MAP = {
    'cached': CACHED_LOC_COLOR, 'grey': (128, 128, 128),
    'lightgrey': (211, 211, 211), 'magenta': (255, 0, 255),
    'white': (255, 255, 255), 'black': (0, 0, 0),
}
GRID_BASE_COLOR = (40, 40, 40)
PARSANG_GRID_COLOR = (80, 80, 80)
CURRENT_LOC_BORDER_COLOR = (255, 255, 0)

# --- Global Data Structures ---
zones = {}
current_location_str = "None"
current_z_level = 10

# --- Utility & Core Logic Functions (Unchanged from your last version) ---
def trim(s: str) -> str: return s.strip()

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
                try:
                    *xy_parts, z_part = zone_loc.split('.')
                    xy_key = ".".join(xy_parts)
                    z_level = int(z_part)
                    zones.setdefault(z_level, {}).setdefault(xy_key, {'color': 'cached'})
                except ValueError: continue
        print(f"Loaded {len(rows)} historical locations from cache.\n")
    except sqlite3.Error as e:
        print(f"Error reading cache.db file: {e}")

def read_player_log():
    global current_location_str, current_z_level
    player_log_file = os.path.join(SAVE_DIR, "Player.log")
    if not os.path.exists(player_log_file): return
    for z_data in zones.values():
        for loc_data in z_data.values(): loc_data.pop('current', None)
    current_location = None
    log_pattern = re.compile(r"INFO - Finished '(?:Thawing|Building) JoppaWorld\.(\d+\.\d+\.\d+\.\d+\.\d+)'")
    try:
        with open(player_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = log_pattern.search(line)
                if match:
                    zone_loc = match.group(1)
                    try:
                        *xy_parts, z_part = zone_loc.split('.')
                        xy_key = ".".join(xy_parts)
                        z_level = int(z_part)
                        zones.setdefault(z_level, {}).setdefault(xy_key, {})['color'] = 'grey'
                        current_location = zone_loc
                    except ValueError: continue
        if current_location:
            *xy_parts, z_part = current_location.split('.')
            xy_key = ".".join(xy_parts)
            z_level = int(z_part)
            if z_level != current_z_level:
                print(f"Z-Level changed from {current_z_level} to {z_level}!")
                current_z_level = z_level
            zones[z_level][xy_key]['color'] = 'magenta'
            zones[z_level][xy_key]['current'] = True
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
                    try:
                        *xy_parts, z_part = zone_loc.split('.')
                        xy_key = ".".join(xy_parts)
                        z_level = int(z_part)
                        print(f"Loading {name} {zone_loc}\n")
                        zones.setdefault(z_level, {})[xy_key] = {'name': name, 'color': color}
                    except ValueError: continue
    except IOError as e:
        print(f"Error reading locations CSV file: {e}")

# --- Pygame Drawing & Transformation Functions (Mostly Unchanged) ---
def world_to_screen(world_x, world_y, zoom, camera_offset, map_area):
    screen_x = (world_x * zoom) - camera_offset[0] + map_area.left
    screen_y = (world_y * zoom) - camera_offset[1] + map_area.top
    return int(screen_x), int(screen_y)

def screen_to_world(screen_x, screen_y, zoom, camera_offset, map_area):
    world_x = (screen_x - map_area.left + camera_offset[0]) / zoom
    world_y = (screen_y - map_area.top + camera_offset[1]) / zoom
    return world_x, world_y

def draw_map(screen, zoom, camera_offset, map_area, z_level):
    level_zones = zones.get(z_level, {})
    effective_cell_size = BASE_CELL_SIZE * zoom
    world_tl_x, world_tl_y = screen_to_world(map_area.left, map_area.top, zoom, camera_offset, map_area)
    world_br_x, world_br_y = screen_to_world(map_area.right, map_area.bottom, zoom, camera_offset, map_area)
    start_gx, start_gy = max(0, int(world_tl_x / BASE_CELL_SIZE)), max(0, int(world_tl_y / BASE_CELL_SIZE))
    end_gx, end_gy = min(PARSANG_X_MAX * ZONE_DIM, int(world_br_x / BASE_CELL_SIZE) + 1), min(PARSANG_Y_MAX * ZONE_DIM, int(world_br_y / BASE_CELL_SIZE) + 1)
    for grid_y in range(start_gy, end_gy):
        for grid_x in range(start_gx, end_gx):
            parsang_x, zone_x = divmod(grid_x, ZONE_DIM)
            parsang_y, zone_y = divmod(grid_y, ZONE_DIM)
            world_x, world_y = grid_x * BASE_CELL_SIZE, grid_y * BASE_CELL_SIZE
            screen_x, screen_y = world_to_screen(world_x, world_y, zoom, camera_offset, map_area)
            rect = pygame.Rect(screen_x, screen_y, int(effective_cell_size + 1), int(effective_cell_size + 1))
            xy_key = f"{parsang_x}.{parsang_y}.{zone_x}.{zone_y}"
            zone_data = level_zones.get(xy_key, {})
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
    start_px, end_px = max(0, int(world_tl_x / (BASE_CELL_SIZE * ZONE_DIM))), min(PARSANG_X_MAX, int(world_br_x / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for i in range(start_px, end_px + 1):
        world_x = i * ZONE_DIM * BASE_CELL_SIZE
        start_pos, end_pos = world_to_screen(world_x, world_tl_y, zoom, camera_offset, map_area), world_to_screen(world_x, world_br_y, zoom, camera_offset, map_area)
        pygame.draw.line(screen, PARSANG_GRID_COLOR, start_pos, end_pos)
    start_py, end_py = max(0, int(world_tl_y / (BASE_CELL_SIZE * ZONE_DIM))), min(PARSANG_Y_MAX, int(world_br_y / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for i in range(start_py, end_py + 1):
        world_y = i * ZONE_DIM * BASE_CELL_SIZE
        start_pos, end_pos = world_to_screen(world_tl_x, world_y, zoom, camera_offset, map_area), world_to_screen(world_br_x, world_y, zoom, camera_offset, map_area)
        pygame.draw.line(screen, PARSANG_GRID_COLOR, start_pos, end_pos)

def draw_headers(screen, font, zoom, camera_offset, map_area):
    if BASE_CELL_SIZE * zoom < 6: return
    world_tl_x, world_tl_y = screen_to_world(map_area.left, map_area.top, zoom, camera_offset, map_area)
    world_br_x, world_br_y = screen_to_world(map_area.right, map_area.bottom, zoom, camera_offset, map_area)
    start_px, end_px = max(0, int(world_tl_x / (BASE_CELL_SIZE * ZONE_DIM))), min(PARSANG_X_MAX, int(world_br_x / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for px in range(start_px, end_px):
        world_x = (px + 0.5) * ZONE_DIM * BASE_CELL_SIZE
        screen_x, _ = world_to_screen(world_x, 0, zoom, camera_offset, map_area)
        if map_area.left <= screen_x <= map_area.right:
            text = font.render(str(px), True, COLOR_MAP['lightgrey'])
            screen.blit(text, text.get_rect(center=(screen_x, map_area.top / 2)))
            screen.blit(text, text.get_rect(center=(screen_x, map_area.bottom + (SCREEN_HEIGHT - map_area.bottom) / 2)))
    start_py, end_py = max(0, int(world_tl_y / (BASE_CELL_SIZE * ZONE_DIM))), min(PARSANG_Y_MAX, int(world_br_y / (BASE_CELL_SIZE * ZONE_DIM)) + 1)
    for py in range(start_py, end_py):
        world_y = (py + 0.5) * ZONE_DIM * BASE_CELL_SIZE
        _, screen_y = world_to_screen(0, world_y, zoom, camera_offset, map_area)
        if map_area.top <= screen_y <= map_area.bottom:
            text = font.render(str(py), True, COLOR_MAP['lightgrey'])
            screen.blit(text, text.get_rect(center=(map_area.left / 2, screen_y)))
            screen.blit(text, text.get_rect(center=(map_area.right + (SCREEN_WIDTH - map_area.right) / 2, screen_y)))

# --- MODIFIED draw_hud function ---
def draw_hud(screen, font, show_controls):
    """Draws the HUD, conditionally showing the controls based on the show_controls flag."""
    depth = current_z_level - 10
    depth_str = "Surface" if depth == 0 else f"{depth} strata deep" if depth > 0 else f"{abs(depth)} strata high"

    # Build the list of text to display
    info_text = [
        f"Current: {current_location_str}",
        f"Depth: {depth_str} (Z={current_z_level})",
    ]
    
    # Conditionally add the controls section
    if show_controls:
        info_text.extend([
            " ", # Adds a little space
            "Controls:",
            "  Mouse Wheel to Zoom",
            "  Middle-Click + Drag to Pan",
        ])
    
    # Add the toggle hint at the end
    info_text.append(f"  Press 'H' to {'hide' if show_controls else 'show'} controls")
    
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
    map_area = pygame.Rect(HEADER_SIZE, HEADER_SIZE, SCREEN_WIDTH - 2 * HEADER_SIZE, SCREEN_HEIGHT - 2 * HEADER_SIZE)
    
    zoom_level = 3.0
    camera_offset = [0, 0]
    is_panning = False
    pan_start_pos = (0, 0)
    show_controls_hud = False  # <-- NEW: State for toggling controls

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
            
            # --- NEW: Keyboard event for toggling help ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    show_controls_hud = not show_controls_hud

            if event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                world_pos_before = screen_to_world(mouse_pos[0], mouse_pos[1], zoom_level, camera_offset, map_area)
                zoom_factor = (1 + ZOOM_SPEED) if event.y > 0 else 1 / (1 + ZOOM_SPEED)
                zoom_level = max(MIN_ZOOM, min(MAX_ZOOM, zoom_level * zoom_factor))
                world_pos_after = screen_to_world(mouse_pos[0], mouse_pos[1], zoom_level, camera_offset, map_area)
                camera_offset[0] += (world_pos_after[0] - world_pos_before[0]) * zoom_level
                camera_offset[1] += (world_pos_after[1] - world_pos_before[1]) * zoom_level

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                is_panning = True
                pan_start_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                is_panning = False
            if event.type == pygame.MOUSEMOTION and is_panning:
                dx, dy = event.rel
                camera_offset[0] -= dx
                camera_offset[1] -= dy

        screen.fill(HEADER_BG_COLOR)
        screen.fill(GRID_BASE_COLOR, map_area)
        draw_map(screen, zoom_level, camera_offset, map_area, current_z_level)
        draw_grid_lines(screen, zoom_level, camera_offset, map_area)
        draw_headers(screen, header_font, zoom_level, camera_offset, map_area)
        
        # --- MODIFIED: Pass the toggle state to the HUD ---
        draw_hud(screen, font, show_controls_hud)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()