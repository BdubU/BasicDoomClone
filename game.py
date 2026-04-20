import pygame
import math

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
MAP_SIZE = 8
TILE_SIZE = SCREEN_WIDTH // (MAP_SIZE * 2)
FOV = math.pi / 3
HALF_FOV = FOV / 2
CASTED_RAYS = 120  # More rays for a denser wall view
STEP_ANGLE = FOV / CASTED_RAYS
MAX_DEPTH = 800

# Simple Map: 1 = Wall, 0 = Empty Space
MAP = [
    1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 1, 0, 0, 1, 0, 1,
    1, 0, 1, 0, 0, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 1, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1,
]

# --- Enemy Data ---
# A simple list of dictionaries, storing coordinates and visual properties.
enemies = [
    {'x': 250, 'y': 250, 'color': (255, 0, 0), 'radius': 10}, # Red blob
    {'x': 380, 'y': 200, 'color': (0, 255, 0), 'radius': 10}, # Green blob
    {'x': 100, 'y': 350, 'color': (0, 0, 255), 'radius': 10}, # Blue blob
]

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Medieval Raycaster Engine")
clock = pygame.time.Clock()

player_x, player_y = 150, 150
player_angle = 0

def draw_map_and_player():
    """Helper to visualize the 2D map and player state (debug/logic view)."""
    map_surface = pygame.Surface((TILE_SIZE * MAP_SIZE, TILE_SIZE * MAP_SIZE))
    map_surface.fill((0, 0, 0))
    for i, tile in enumerate(MAP):
        row = i // MAP_SIZE
        col = i % MAP_SIZE
        if tile == 1:
            pygame.draw.rect(map_surface, (100, 100, 100), (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        else:
            pygame.draw.rect(map_surface, (50, 50, 50), (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)

    # Draw player in map view
    pygame.draw.circle(map_surface, (255, 255, 0), (int(player_x / TILE_SIZE * TILE_SIZE), int(player_y / TILE_SIZE * TILE_SIZE)), 3)
    # Draw player direction
    line_len = 20
    pygame.draw.line(map_surface, (255, 255, 0), 
                     (int(player_x / TILE_SIZE * TILE_SIZE), int(player_y / TILE_SIZE * TILE_SIZE)),
                     (int((player_x + math.cos(player_angle) * line_len) / TILE_SIZE * TILE_SIZE),
                      int((player_y + math.sin(player_angle) * line_len) / TILE_SIZE * TILE_SIZE)))

    screen.blit(map_surface, (0, 0))

def draw_weapon():
    """Draws a simple geometric medieval axe/weapon (static)."""
    weapon_color = (139, 69, 19) # Dark wood
    blade_color = (169, 169, 169) # Dark gray metal
    
    # Axe Shaft (Grip)
    shaft_rect = pygame.Rect(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT - 120, 20, 120)
    pygame.draw.rect(screen, weapon_color, shaft_rect)
    
    # Axe Head (A simple triangle/rectangle)
    # The shaft top is at SCREEN_HEIGHT - 120
    blade_top = SCREEN_HEIGHT - 120
    # Left Point, Right Point, Top Point
    points = [
        (SCREEN_WIDTH // 2 - 30, blade_top),        # Bottom left
        (SCREEN_WIDTH // 2 + 30, blade_top),        # Bottom right
        (SCREEN_WIDTH // 2, blade_top - 40)        # Top center point
    ]
    pygame.draw.polygon(screen, blade_color, points)
    # Small cross-guard/axe head detail
    cross_rect = pygame.Rect(SCREEN_WIDTH // 2 - 25, blade_top, 50, 10)
    pygame.draw.rect(screen, blade_color, cross_rect)

running = True
while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Controls
    keys = pygame.key.get_pressed()
    rot_speed = 0.05
    move_speed = 3
    
    if keys[pygame.K_LEFT]: player_angle -= rot_speed
    if keys[pygame.K_RIGHT]: player_angle += rot_speed
    if keys[pygame.K_w]:
        player_x += math.cos(player_angle) * move_speed
        player_y += math.sin(player_angle) * move_speed
    if keys[pygame.K_s]:
        player_x -= math.cos(player_angle) * move_speed
        player_y -= math.sin(player_angle) * move_speed
    # Basic collision check for player moving outside map boundaries
    if player_x < TILE_SIZE: player_x = TILE_SIZE
    if player_x > SCREEN_WIDTH / 2 - TILE_SIZE: player_x = SCREEN_WIDTH / 2 - TILE_SIZE
    if player_y < TILE_SIZE: player_y = TILE_SIZE
    if player_y > SCREEN_HEIGHT - TILE_SIZE: player_y = SCREEN_HEIGHT - TILE_SIZE

    # 3. Standard Raycasting (Walls) and Z-buffer Creation
    # The Z-buffer will store the depth of the closest wall for EVERY column.
    wall_depth_buffer = [MAX_DEPTH] * CASTED_RAYS
    
    screen.fill((50, 50, 50)) # Ceiling
    pygame.draw.rect(screen, (100, 100, 100), (0, SCREEN_HEIGHT/2, SCREEN_WIDTH, SCREEN_HEIGHT/2)) # Floor

    start_angle = player_angle - HALF_FOV
    
    # Pre-calculating useful constants outside the loop
    ray_width = SCREEN_WIDTH / CASTED_RAYS
    
    for ray in range(CASTED_RAYS):
        # Cast the ray step by step
        for depth in range(1, MAX_DEPTH, 2): # Stepping by 2 for performance
            target_x = player_x + math.cos(start_angle) * depth
            target_y = player_y + math.sin(start_angle) * depth
            
            # Map coordinates
            col = int(target_x / TILE_SIZE)
            row = int(target_y / TILE_SIZE)
            
            # Bounds checking for safety
            if 0 <= col < MAP_SIZE and 0 <= row < MAP_SIZE:
                # Wall hit
                if MAP[row * MAP_SIZE + col] == 1:
                    # Fix fish-eye effect: correct depth by cosine of relative angle
                    relative_angle = player_angle - start_angle
                    corrected_depth = depth * math.cos(relative_angle)
                    
                    # Store corrected wall depth in the Z-buffer for this column
                    wall_depth_buffer[ray] = corrected_depth
                    
                    # Standard height calculation and shading based on uncorrected depth for a basic effect
                    wall_height = 21000 / (corrected_depth + 0.0001) # constant to adjust height scaling
                    
                    # Color shading based on distance (closer is brighter)
                    color_v = 255 / (1 + depth * depth * 0.00005)
                    wall_color = (color_v, color_v, color_v)
                    
                    # Draw wall slice
                    x_start = ray * ray_width
                    y_start = (SCREEN_HEIGHT / 2) - wall_height / 2
                    pygame.draw.rect(screen, wall_color, (x_start, y_start, ray_width + 1, wall_height))
                    break
            else:
                # Ray left the map area
                wall_depth_buffer[ray] = MAX_DEPTH
                break
        
        # Advance the angle
        start_angle += STEP_ANGLE

    # 4. Enemy Raycasting (Sprite Raycasting)
    # The trick is to draw sprites column by column, checking the Z-buffer.
    
    # Sort enemies by distance from the player (closest last) so they draw on top of each other correctly
    enemies_with_dist = []
    for en in enemies:
        dx = en['x'] - player_x
        dy = en['y'] - player_y
        distance = math.sqrt(dx*dx + dy*dy)
        enemies_with_dist.append((distance, en))
    enemies_with_dist.sort(key=lambda x: x[0], reverse=True) # Sort descending by distance

    for dist, en in enemies_with_dist:
        dx = en['x'] - player_x
        dy = en['y'] - player_y
        
        # Calculate angle from player to enemy
        theta = math.atan2(dy, dx)
        
        # Correct the angle wrapping (-PI to PI range)
        diff_angle = theta - player_angle
        if diff_angle < -math.pi: diff_angle += 2 * math.pi
        if diff_angle > math.pi: diff_angle -= 2 * math.pi
        
        # If the enemy is within the player's field of view
        if abs(diff_angle) < HALF_FOV:
            # Enemy screen position
            # Use diff_angle and FOV to locate the enemy center column
            enemy_center_ray = (diff_angle + HALF_FOV) / STEP_ANGLE
            enemy_screen_x = enemy_center_ray * ray_width
            enemy_screen_y = SCREEN_HEIGHT / 2 # Enemies are centered on the horizon

            # Scaling: Smaller distance = bigger height
            # Use corrected distance for scaling
            relative_angle_sprite = player_angle - theta
            # corrected_dist = dist * math.cos(relative_angle_sprite) # Simplified correcting approach
            corrected_dist = dist
            
            if corrected_dist == 0: corrected_dist = 0.0001
            
            sprite_scale = 10000 / corrected_dist
            
            sprite_screen_size = 2 * en['radius'] * (sprite_scale / 100) # Constant for scale adjusting

            # Iterate through the columns the sprite covers on the screen
            sprite_start_x = enemy_screen_x - sprite_screen_size / 2
            sprite_end_x = enemy_screen_x + sprite_screen_size / 2
            
            # Start column and end column index
            col_start = int(sprite_start_x / ray_width)
            col_end = int(sprite_end_x / ray_width)
            
            # Check boundaries of columns
            if col_start < 0: col_start = 0
            if col_end >= CASTED_RAYS: col_end = CASTED_RAYS
            
            # Shading the enemy based on distance (simulating lighting)
            color_shade = 255 / (1 + dist * dist * 0.00005)
            shaded_color = tuple(c * (color_shade/255) for c in en['color'])

            # Draw the enemy geometry billboard column by column
            for col in range(col_start, col_end):
                # The crucial step: only draw if the enemy is CLOSER than the wall depth recorded for this column
                if corrected_dist < wall_depth_buffer[col]:
                    # Draw a vertical slice for the enemy at this screen col
                    x_col = col * ray_width
                    y_start_sprite = enemy_screen_y - sprite_screen_size / 2
                    pygame.draw.rect(screen, shaded_color, (x_col, y_start_sprite, ray_width + 1, sprite_screen_size))

    # 5. Weapon Drawing (Static 2D geometric axe)
    draw_weapon()

    # 6. Display map overview (debug)
    # draw_map_and_player()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()