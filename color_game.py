import pygame
import serial
import threading
import time
import random

# ==========================================
# CONFIGURATION
# ==========================================
SERIAL_PORT = 'COM6'  # <--- CHECK YOUR ARDUINO PORT
BAUD_RATE = 9600
WIDTH, HEIGHT = 1200, 800

# ==========================================
# COLORS
# ==========================================
C_BG = (30, 30, 35)        
C_WHITE = (240, 240, 240)
C_ACCENT = (255, 215, 0)   # Gold
C_RED = (235, 60, 60)
C_GREEN = (46, 204, 113)
C_BLUE = (52, 152, 219)
C_LIGHT_OFF = (60, 20, 20) 
C_LIGHT_ON = (255, 0, 0)   

GAME_COLORS = {"RED": C_RED, "GREEN": C_GREEN, "BLUE": C_BLUE}

# ==========================================
# SERIAL CONNECTION
# ==========================================
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) 
    print(f"Connected to Arduino on {SERIAL_PORT}")
except:
    print(f"ERROR: Could not connect to Arduino.")
    ser = None

# ==========================================
# GLOBAL VARIABLES & THREADING
# ==========================================
incoming_data = ""
lock = threading.Lock()

def read_serial():
    global incoming_data
    while True:
        if ser and ser.in_waiting:
            try:
                raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                if raw_line:
                    print(f"[ARDUINO] {raw_line}") 

                cmd = raw_line.upper()
                if cmd in ["TAP", "RED", "GREEN", "BLUE"]:
                    with lock:
                        incoming_data = cmd
            except:
                pass

if ser:
    threading.Thread(target=read_serial, daemon=True).start()

# ==========================================
# PYGAME SETUP
# ==========================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CHROMA REFLEX: PRO")

font_title = pygame.font.SysFont("impact", 100)
font_badge = pygame.font.SysFont("impact", 60) 
font_main = pygame.font.SysFont("arial", 40)
font_small = pygame.font.SysFont("arial", 28)

# ==========================================
# STATES
# ==========================================
STATE_LANDING = 0
STATE_WAIT_TAP = 1    
STATE_COUNTDOWN = 1.5
STATE_GAME_ACTIVE = 2
STATE_ROUND_RESULT = 3
STATE_GAME_OVER = 4

current_state = STATE_LANDING
round_count = 1
max_rounds = 5

# NEW: We store a dictionary for every round: {'time': 300, 'result': True/False}
game_history = [] 

target_color = "RED"
start_time = 0
countdown_start = 0
hold_time = 0

# Result Tracking for current round
round_message = ""
last_round_success = False 

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def draw_text_centered(text, font, color, y_offset=0):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    screen.blit(surface, rect)

def get_serial_input():
    global incoming_data
    with lock:
        if incoming_data:
            data = incoming_data
            incoming_data = "" 
            return data
    return None

def flush_serial():
    global incoming_data
    with lock:
        incoming_data = ""

def draw_f1_lights(lights_on):
    box_w, box_h = 600, 150
    box_x = WIDTH//2 - box_w//2
    box_y = HEIGHT//2 - 200
    pygame.draw.rect(screen, (10, 10, 10), (box_x, box_y, box_w, box_h), border_radius=15)
    
    spacing = 100
    start_x = WIDTH//2 - 200
    for i in range(5):
        color = C_LIGHT_ON if i < lights_on else C_LIGHT_OFF
        pygame.draw.circle(screen, color, (start_x + (i * spacing), box_y + box_h//2), 40)

def draw_result_badge(is_correct):
    box_w, box_h = 400, 120
    box_x = WIDTH // 2 - box_w // 2
    box_y = HEIGHT // 2 - 150
    
    color = C_GREEN if is_correct else C_RED
    text_str = "CORRECT" if is_correct else "WRONG"
    
    pygame.draw.rect(screen, color, (box_x, box_y, box_w, box_h), border_radius=20)
    pygame.draw.rect(screen, C_WHITE, (box_x, box_y, box_w, box_h), 5, border_radius=20)
    
    text_surf = font_badge.render(text_str, True, C_WHITE)
    text_rect = text_surf.get_rect(center=(WIDTH // 2, box_y + box_h // 2))
    screen.blit(text_surf, text_rect)

# ==========================================
# MAIN LOOP
# ==========================================
running = True
while running:
    screen.fill(C_BG)
    serial_input = get_serial_input()
    
    keys = pygame.key.get_pressed()
    mouse_click = False 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_click = True

    # ------------------------------------------------
    # 1. LANDING PAGE
    # ------------------------------------------------
    if current_state == STATE_LANDING:
        draw_text_centered("CHROMA REFLEX", font_title, C_ACCENT, -100)
        draw_text_centered("F1 PRO EDITION", font_main, C_WHITE, 0)
        
        if int(time.time() * 2) % 2 == 0:
            draw_text_centered("- PRESS SPACE TO ENTER -", font_small, C_GREEN, 100)
        
        if keys[pygame.K_SPACE] or mouse_click:
            round_count = 1
            game_history = [] # Reset History
            flush_serial()
            current_state = STATE_WAIT_TAP

    # ------------------------------------------------
    # 2. WAIT FOR PIEZO
    # ------------------------------------------------
    elif current_state == STATE_WAIT_TAP:
        draw_text_centered(f"ROUND {round_count} / {max_rounds}", font_title, C_WHITE, -50)
        draw_text_centered("HIT PIEZO TO INITIATE COUNTDOWN", font_small, C_ACCENT, 50)

        if serial_input == "TAP":
            current_state = STATE_COUNTDOWN
            countdown_start = time.time()
            hold_time = random.uniform(0.2, 1.5) 

    # ------------------------------------------------
    # 2.5 F1 COUNTDOWN
    # ------------------------------------------------
    elif current_state == STATE_COUNTDOWN:
        elapsed = time.time() - countdown_start
        light_interval = 0.5 
        
        lights_active = int(elapsed // light_interval)
        if lights_active > 5: lights_active = 5
        draw_f1_lights(lights_active)
        
        if elapsed > (5 * light_interval) + hold_time:
            target_color = random.choice(["RED", "GREEN", "BLUE"])
            current_state = STATE_GAME_ACTIVE
            start_time = time.time()
            flush_serial()

    # ------------------------------------------------
    # 3. GAME ACTIVE
    # ------------------------------------------------
    elif current_state == STATE_GAME_ACTIVE:
        card_rect = pygame.Rect(0, 0, 400, 400)
        card_rect.center = (WIDTH // 2, HEIGHT // 2 + 50)
        pygame.draw.rect(screen, GAME_COLORS[target_color], card_rect, border_radius=20)
        
        text = font_title.render(target_color, True, (255,255,255))
        screen.blit(text, (card_rect.centerx - text.get_width()//2, card_rect.centery - text.get_height()//2))

        if serial_input in ["RED", "GREEN", "BLUE"]:
            reaction = (time.time() - start_time) * 1000
            
            if serial_input == target_color:
                last_round_success = True
                round_message = f"Reaction: {int(reaction)} ms"
                # Store Data
                game_history.append({'time': reaction, 'correct': True})
            else:
                last_round_success = False
                round_message = f"Penalized Time: {int(reaction + 1000)} ms"
                # Store Data (with penalty)
                game_history.append({'time': reaction + 1000, 'correct': False})
            
            current_state = STATE_ROUND_RESULT

    # ------------------------------------------------
    # 4. ROUND RESULT (Badge)
    # ------------------------------------------------
    elif current_state == STATE_ROUND_RESULT:
        draw_result_badge(last_round_success)
        draw_text_centered(round_message, font_main, C_WHITE, 50)
        draw_text_centered("Press SPACE to Prepare Next Round", font_small, (150, 150, 150), 120)

        if keys[pygame.K_SPACE] or mouse_click:
            if round_count < max_rounds:
                round_count += 1
                flush_serial()
                current_state = STATE_WAIT_TAP 
            else:
                current_state = STATE_GAME_OVER
            time.sleep(0.2) 

    # ------------------------------------------------
    # 5. GAME OVER (Tally Board)
    # ------------------------------------------------
    elif current_state == STATE_GAME_OVER:
        draw_text_centered("SESSION TALLY", font_title, C_ACCENT, -300)
        
        total_time = 0
        
        # Loop through history to draw table
        start_y = -180
        for i, entry in enumerate(game_history):
            t = entry['time']
            is_good = entry['correct']
            
            total_time += t
            
            # Format: "ROUND 1 | 345 ms | CORRECT"
            status_text = "CORRECT" if is_good else "WRONG"
            color = C_GREEN if is_good else C_RED
            
            row_str = f"ROUND {i+1}   |   {int(t)} ms   |   {status_text}"
            draw_text_centered(row_str, font_small, color, start_y + (i * 45))

        # Average Calculation
        avg = total_time / len(game_history) if len(game_history) > 0 else 0
        
        # Draw Average Box
        pygame.draw.rect(screen, C_WHITE, (WIDTH//2 - 200, HEIGHT//2 + 100, 400, 100), 2)
        draw_text_centered(f"AVG TIME: {int(avg)} ms", font_main, C_ACCENT, 150)
        
        draw_text_centered("Press 'R' to Restart", font_small, (150, 150, 150), 250)

        if keys[pygame.K_r]:
            current_state = STATE_LANDING
            flush_serial()

    pygame.display.flip()

pygame.quit()
if ser:
    ser.close()