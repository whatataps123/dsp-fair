import pygame
import serial
import threading
import time
import random
import re
import math
from collections import deque

# ==========================================
# CONFIGURATION
# ==========================================
SERIAL_PORT = 'COM8'  # <--- CHECK YOUR PORT
BAUD_RATE = 9600
WIDTH, HEIGHT = 1280, 720 

# ==========================================
# F1 THEME PALETTE
# ==========================================
C_BG = (20, 20, 23)           
C_PANEL = (30, 32, 35)        
C_WHITE = (240, 240, 245)
C_F1_RED = (255, 24, 1)       
C_TEAL = (0, 240, 200)        
C_ORANGE = (255, 140, 0)      
C_GREEN = (50, 220, 50)       
C_YELLOW = (255, 240, 0)      # Bright Renault/Jordan Yellow
C_BLUE = (0, 110, 255)        # Alpine/Williams Blue
C_GRID = (50, 50, 55)         

# --- UPDATED GAME COLORS ---
GAME_COLORS = {"YELLOW": C_YELLOW, "GREEN": C_GREEN, "BLUE": C_BLUE}

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
# GLOBAL VARIABLES
# ==========================================
incoming_data = ""
lock = threading.Lock()
sensor_history = deque(maxlen=150) 
dsp_threshold = 150 

# --- TELEMETRY STATE MACHINE ---
TEL_IDLE = 0
TEL_IMPACT = 1
TEL_WAIT_BTN = 2

telemetry_status = TEL_IDLE
impact_timer = 0
telemetry_cooldown = 0 

def read_serial():
    global incoming_data, telemetry_status, impact_timer, telemetry_cooldown
    pattern = re.compile(r"RAW:\s*(-?\d+)\s*\|\s*FILTER:\s*(-?\d+)\s*\|\s*ENVELOPE:\s*(-?\d+)")
    while True:
        if ser and ser.in_waiting:
            try:
                raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                match = pattern.search(raw_line)
                if match:
                    env_val = int(match.group(3))
                    with lock:
                        sensor_history.append((int(match.group(1)), int(match.group(2)), env_val))
                        
                        if env_val > dsp_threshold:
                            if telemetry_status == TEL_IDLE and time.time() > telemetry_cooldown:
                                telemetry_status = TEL_IMPACT
                                impact_timer = time.time()

                else:
                    cmd = raw_line.upper()
                    if cmd in ["TAP", "RED", "GREEN", "BLUE"]:
                        with lock: 
                            # --- COLOR MAPPING ---
                            # Convert hardware RED button to software YELLOW
                            if cmd == "RED":
                                incoming_data = "YELLOW"
                            else:
                                incoming_data = cmd
                            
                            # --- TELEMETRY LOGIC ---
                            if cmd == "TAP":
                                if telemetry_status == TEL_IDLE and time.time() > telemetry_cooldown:
                                    telemetry_status = TEL_IMPACT
                                    impact_timer = time.time()
                            
                            elif cmd in ["RED", "GREEN", "BLUE"]:
                                telemetry_status = TEL_IDLE
                                telemetry_cooldown = time.time() + 1.0

            except: pass

if ser:
    threading.Thread(target=read_serial, daemon=True).start()

# ==========================================
# PYGAME SETUP
# ==========================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ColorTap: DSP-Enabled Reaction Game")

# Fonts
font_huge = pygame.font.SysFont("impact", 90)
font_large = pygame.font.SysFont("impact", 60)
font_med = pygame.font.SysFont("bahnschrift", 30)
font_mono = pygame.font.SysFont("consolas", 18)
font_label = pygame.font.SysFont("bahnschrift", 14)

# ==========================================
# STATES & VARIABLES
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
game_history = [] 

target_color = "YELLOW" # Default
start_time = 0
countdown_start = 0
hold_time = 0
safety_cooldown = 0 
round_message = ""
last_round_success = False 
badge_text_override = "" 
session_start_timestamp = 0
session_end_timestamp = 0

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def draw_centered(text, font, color, y_off=0, x_off=0):
    game_center_x = 350 + (WIDTH - 350) // 2
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(game_center_x + x_off, HEIGHT // 2 + y_off))
    screen.blit(surf, rect)

def get_serial_input():
    global incoming_data
    with lock:
        if incoming_data:
            d = incoming_data
            incoming_data = "" 
            return d
    return None

def flush_serial():
    global incoming_data
    with lock: incoming_data = ""

def draw_stylized_f1_car(surface, center_x, center_y, scale=1.0):
    body_col = C_F1_RED
    tire_col = (30, 30, 35) 
    rim_col = (150, 150, 150) 
    wing_col = (200, 200, 200)
    def s(val): return int(val * scale)
    
    # Rear Wing
    pygame.draw.rect(surface, wing_col, (center_x - s(100), center_y - s(40), s(20), s(80)))
    # Rear Tires
    pygame.draw.rect(surface, tire_col, (center_x - s(80), center_y - s(65), s(50), s(40)), border_radius=s(5))
    pygame.draw.rect(surface, rim_col, (center_x - s(70), center_y - s(55), s(20), s(20)), border_radius=s(3))
    pygame.draw.rect(surface, tire_col, (center_x - s(80), center_y + s(25), s(50), s(40)), border_radius=s(5))
    pygame.draw.rect(surface, rim_col, (center_x - s(70), center_y + s(35), s(20), s(20)), border_radius=s(3))
    # Body
    pygame.draw.polygon(surface, body_col, [
        (center_x - s(60), center_y - s(15)),
        (center_x + s(100), center_y - s(8)),
        (center_x + s(100), center_y + s(8)),
        (center_x - s(60), center_y + s(15))
    ])
    pygame.draw.rect(surface, body_col, (center_x - s(50), center_y - s(25), s(60), s(50)), border_radius=s(5))
    # Front Tires
    pygame.draw.rect(surface, tire_col, (center_x + s(60), center_y - s(60), s(40), s(35)), border_radius=s(5))
    pygame.draw.rect(surface, rim_col, (center_x + s(70), center_y - s(52), s(15), s(18)), border_radius=s(3))
    pygame.draw.rect(surface, tire_col, (center_x + s(60), center_y + s(25), s(40), s(35)), border_radius=s(5))
    pygame.draw.rect(surface, rim_col, (center_x + s(70), center_y + s(33), s(15), s(18)), border_radius=s(3))
    # Front Wing
    pygame.draw.polygon(surface, wing_col, [
        (center_x + s(110), center_y - s(35)),
        (center_x + s(120), center_y - s(40)),
        (center_x + s(125), center_y),
        (center_x + s(120), center_y + s(40)),
        (center_x + s(110), center_y + s(35))
    ])
    # Helmet
    pygame.draw.circle(surface, (255, 215, 0), (center_x - s(10), center_y), s(7))

# --- TELEMETRY SIDEBAR ---
def draw_telemetry():
    global telemetry_status
    
    sidebar_w = 350
    pygame.draw.rect(screen, C_PANEL, (0, 0, sidebar_w, HEIGHT))
    pygame.draw.line(screen, C_F1_RED, (sidebar_w, 0), (sidebar_w, HEIGHT), 4)

    header = font_med.render("TELEMETRY", True, C_WHITE)
    screen.blit(header, (20, 20))
    pygame.draw.rect(screen, C_F1_RED, (20, 55, 60, 4)) 

    # LIVE GRAPH
    graph_h = 250
    graph_y = 100
    pygame.draw.rect(screen, (10, 10, 12), (15, graph_y, sidebar_w-30, graph_h))
    pygame.draw.rect(screen, C_GRID, (15, graph_y, sidebar_w-30, graph_h), 1)
    
    for i in range(1, 5):
        y_pos = graph_y + (graph_h / 5) * i
        pygame.draw.line(screen, (25, 25, 30), (16, y_pos), (sidebar_w-16, y_pos))

    thresh_y = graph_y + graph_h - (dsp_threshold / 500 * graph_h)
    pygame.draw.line(screen, C_F1_RED, (15, thresh_y), (sidebar_w-15, thresh_y), 1)
    screen.blit(font_label.render("TRIG THRESHOLD", True, C_F1_RED), (sidebar_w - 120, thresh_y - 15))

    if len(sensor_history) > 1:
        x_step = (sidebar_w - 30) / 150
        pts_raw, pts_filt, pts_env = [], [], []
        
        for i, (r, f, e) in enumerate(sensor_history):
            x = 15 + i * x_step
            pts_raw.append((x, graph_y + graph_h - (min(r, 500)/500 * graph_h)))
            pts_filt.append((x, graph_y + graph_h - (min(f, 500)/500 * graph_h)))
            pts_env.append((x, graph_y + graph_h - (min(e, 500)/500 * graph_h)))

        pygame.draw.lines(screen, (60, 60, 60), False, pts_raw, 1)  
        pygame.draw.lines(screen, C_TEAL, False, pts_filt, 2)       
        pygame.draw.lines(screen, C_ORANGE, False, pts_env, 2)      

    r, f, e = sensor_history[-1] if sensor_history else (0,0,0)
    y_start = 380
    labels = [("RAW INPUT", r, (150, 150, 150)), 
              ("DSP FILTER", f, C_TEAL), 
              ("ENVELOPE (N)", e, C_ORANGE)]
    
    for i, (lbl, val, col) in enumerate(labels):
        py = y_start + (i * 50)
        screen.blit(font_label.render(lbl, True, col), (20, py))
        val_surf = font_med.render(f"{val:03}", True, C_WHITE)
        screen.blit(val_surf, (sidebar_w - 80, py - 5))
        pygame.draw.line(screen, C_GRID, (20, py+35), (sidebar_w-20, py+35), 1)

    status_y = 560
    
    # --- LOGIC: STATE VISUALIZATION ---
    # 1. AUTO TRANSITION: Impact (Red) -> Wait Button (Yellow)
    if telemetry_status == TEL_IMPACT and (time.time() - impact_timer > 0.5):
        telemetry_status = TEL_WAIT_BTN
        
    # 2. RENDER STATES
    if telemetry_status == TEL_IMPACT:
        pygame.draw.rect(screen, C_F1_RED, (20, status_y, sidebar_w-40, 60), border_radius=4)
        msg = font_med.render("IMPACT DETECTED", True, C_WHITE)
        screen.blit(msg, (55, status_y + 15))
        
    elif telemetry_status == TEL_WAIT_BTN:
        pygame.draw.rect(screen, C_ORANGE, (20, status_y, sidebar_w-40, 60), border_radius=4)
        msg = font_med.render("PRESS A BUTTON", True, (20, 20, 20))
        screen.blit(msg, (65, status_y + 15))
        
    else: # IDLE
        pygame.draw.rect(screen, (20, 20, 20), (20, status_y, sidebar_w-40, 60), border_radius=4)
        pygame.draw.rect(screen, C_GRID, (20, status_y, sidebar_w-40, 60), 1, border_radius=4)
        msg = font_med.render("SENSOR IDLE", True, (80, 80, 80))
        screen.blit(msg, (100, status_y + 15))

def draw_session_graph(history):
    c_x = 350 + (WIDTH - 350) // 2
    g_w, g_h = 600, 150
    g_x, g_y = c_x - g_w // 2, HEIGHT - 200 
    
    pygame.draw.rect(screen, (15, 15, 20), (g_x, g_y, g_w, g_h))
    pygame.draw.rect(screen, (50, 50, 50), (g_x, g_y, g_w, g_h), 1)
    
    screen.blit(font_label.render("PACE EVOLUTION", True, (150, 150, 150)), (g_x, g_y - 20))
    
    if not history: return

    max_score = max([h['raw'] + h['penalty'] for h in history]) + 200
    if max_score < 1000: max_score = 1000 
    
    points = []
    for i, entry in enumerate(history):
        score = entry['raw'] + entry['penalty']
        px = g_x + (g_w / (len(history) + 1)) * (i + 1)
        py = (g_y + g_h) - (score / max_score * g_h) - 10 
        points.append((px, py))
        
        col = C_GREEN if entry['status'] == "CORRECT" else C_F1_RED
        pygame.draw.circle(screen, col, (int(px), int(py)), 6)
        lbl = font_label.render(str(int(score)), True, C_WHITE)
        screen.blit(lbl, (px - 10, py - 25))

    if len(points) > 1:
        pygame.draw.lines(screen, C_TEAL, False, points, 2)

# ==========================================
# MAIN LOOP
# ==========================================
def draw_f1_lights(active_lights):
    center_x = 350 + (WIDTH - 350) // 2
    w, h = 600, 140
    pygame.draw.rect(screen, (10, 10, 10), (center_x - w//2, HEIGHT//2 - 220, w, h), border_radius=20)
    pygame.draw.rect(screen, (80, 80, 80), (center_x - w//2, HEIGHT//2 - 220, w, h), 3, border_radius=20)
    spacing = 110
    start_x = center_x - 220
    for i in range(5):
        color = (255, 0, 0) if i < active_lights else (50, 10, 10)
        if i < active_lights:
             pygame.draw.circle(screen, (100, 0, 0), (start_x + i*spacing, HEIGHT//2 - 150), 45)
        pygame.draw.circle(screen, color, (start_x + i*spacing, HEIGHT//2 - 150), 35)
        pygame.draw.circle(screen, (255, 100, 100), (start_x + i*spacing - 10, HEIGHT//2 - 160), 8)

def draw_flag_card(color_name):
    center_x = 350 + (WIDTH - 350) // 2
    rect = pygame.Rect(0, 0, 350, 350)
    rect.center = (center_x, HEIGHT//2 + 20)
    pygame.draw.rect(screen, GAME_COLORS[color_name], rect, border_radius=10)
    pygame.draw.rect(screen, C_WHITE, rect, 5, border_radius=10)
    txt = font_huge.render(color_name, True, (20, 20, 20)) # Dark text on bright color
    
    screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

running = True
while running:
    serial_in = get_serial_input()
    keys = pygame.key.get_pressed()
    click = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN: click = True

    screen.fill(C_BG)
    draw_telemetry() # ALWAYS DRAW TELEMETRY

    if current_state == STATE_LANDING:
        draw_centered("ColorTap", font_huge, C_WHITE, -160)
        draw_centered("A DSP-Enabled Visual Reaction Game", font_med, C_F1_RED, -90)
        
        # --- DRAW F1 CAR WITH RIMS ---
        hover_y = math.sin(time.time() * 2) * 10
        center_x = 350 + (WIDTH - 350) // 2
        draw_stylized_f1_car(screen, center_x, HEIGHT//2 + 50 + hover_y, scale=1.5)
        # -----------------------------

        if int(time.time() * 2) % 2 == 0:
            pygame.draw.rect(screen, C_WHITE, (center_x - 150, HEIGHT//2 + 180, 300, 50), border_radius=5)
            lbl = font_med.render("PRESS SPACE", True, C_BG)
            screen.blit(lbl, (center_x - lbl.get_width()//2, HEIGHT//2 + 192))

        if keys[pygame.K_SPACE] or click:
            round_count = 1; game_history = []; flush_serial()
            current_state = STATE_WAIT_TAP
            safety_cooldown = time.time() + 1.0
            session_start_timestamp = time.time()

    elif current_state == STATE_WAIT_TAP:
        draw_centered(f"ROUND {round_count} / {max_rounds}", font_large, C_WHITE, -100)
        if time.time() < safety_cooldown:
            draw_centered("SYSTEM INITIALIZING...", font_med, (100, 100, 100), 50)
            if serial_in == "TAP":
                draw_centered("PLEASE WAIT...", font_med, C_F1_RED, 100)
                pygame.display.flip(); time.sleep(0.3)
        else:
            draw_centered("STRIKE SENSOR TO START", font_med, C_F1_RED, 50)
            if serial_in == "TAP":
                draw_centered("SENSOR TRIGGERED", font_med, C_GREEN, 100)
                pygame.display.flip(); time.sleep(0.3)
                current_state = STATE_COUNTDOWN
                countdown_start = time.time()
                hold_time = random.uniform(0.2, 1.5)

    elif current_state == STATE_COUNTDOWN:
        elapsed = time.time() - countdown_start
        lights = int(elapsed // 0.5)
        if lights > 5: lights = 5
        draw_f1_lights(lights)
        # Check for Jump Start
        if serial_in in ["YELLOW", "GREEN", "BLUE"]:
            last_round_success = False
            badge_text_override = "JUMP START"
            round_message = "Penalty: +1000ms"
            game_history.append({'raw': 0, 'penalty': 1000, 'status': "FALSE START"})
            current_state = STATE_ROUND_RESULT
            flush_serial()
        elif elapsed > 2.5 + hold_time:
            # Pick from NEW colors
            target_color = random.choice(["YELLOW", "GREEN", "BLUE"])
            current_state = STATE_GAME_ACTIVE
            start_time = time.time()
            flush_serial()

    elif current_state == STATE_GAME_ACTIVE:
        draw_flag_card(target_color)
        if serial_in in ["YELLOW", "GREEN", "BLUE"]:
            reaction = (time.time() - start_time) * 1000
            if serial_in == target_color:
                last_round_success = True; badge_text_override = ""
                round_message = f"Reaction: {int(reaction)} ms"
                game_history.append({'raw': reaction, 'penalty': 0, 'status': "CORRECT"})
            else:
                last_round_success = False; badge_text_override = "WRONG COLOR"
                round_message = f"Total: {int(reaction+1000)} ms"
                game_history.append({'raw': reaction, 'penalty': 1000, 'status': "WRONG COLOR"})
            current_state = STATE_ROUND_RESULT

    elif current_state == STATE_ROUND_RESULT:
        c_center = 350 + (WIDTH-350)//2
        bg_col = C_GREEN if last_round_success else C_F1_RED
        txt = badge_text_override if badge_text_override else ("SECTOR CLEAR" if last_round_success else "INCIDENT")
        pygame.draw.rect(screen, bg_col, (c_center-250, HEIGHT//2-80, 500, 100), border_radius=10)
        lbl = font_large.render(txt, True, C_WHITE)
        screen.blit(lbl, (c_center - lbl.get_width()//2, HEIGHT//2 - 60))
        draw_centered(round_message, font_med, C_WHITE, 60)
        draw_centered("PRESS SPACE FOR NEXT LAP", font_mono, (150, 150, 150), 120)

        if keys[pygame.K_SPACE] or click:
            if round_count < max_rounds:
                round_count += 1; current_state = STATE_WAIT_TAP
                flush_serial(); safety_cooldown = time.time() + 0.5
            else:
                current_state = STATE_GAME_OVER
                session_end_timestamp = time.time()
            time.sleep(0.2)

    elif current_state == STATE_GAME_OVER:
        draw_centered("SESSION CLASSIFICATION", font_large, C_F1_RED, -300)
        
        c_center = 350 + (WIDTH-350)//2
        headers = ["LAP", "REACT", "PENALTY", "TOTAL"]
        x_positions = [-200, -80, 50, 180]
        
        pygame.draw.line(screen, (80,80,80), (c_center-250, HEIGHT//2-220), (c_center+250, HEIGHT//2-220), 2)
        
        for i, h in enumerate(headers):
            surf = font_label.render(h, True, (150,150,150))
            screen.blit(surf, (c_center + x_positions[i], HEIGHT//2 - 240))

        total_score = 0
        start_y = -200
        
        for i, entry in enumerate(game_history):
            raw = int(entry['raw'])
            pen = int(entry['penalty'])
            score = raw + pen
            total_score += score
            
            col = C_GREEN if entry['status']=="CORRECT" else C_F1_RED
            y_pos = HEIGHT//2 + start_y + (i * 40) 
            
            screen.blit(font_mono.render(f"{i+1}", True, C_WHITE), (c_center + x_positions[0] + 10, y_pos))
            screen.blit(font_mono.render(f"{raw}", True, C_WHITE), (c_center + x_positions[1], y_pos))
            screen.blit(font_mono.render(f"+{pen}", True, (255,100,100) if pen > 0 else (100,100,100)), (c_center + x_positions[2] + 10, y_pos))
            screen.blit(font_mono.render(f"{score}", True, col), (c_center + x_positions[3], y_pos))
            pygame.draw.line(screen, (40,40,40), (c_center-250, y_pos+30), (c_center+250, y_pos+30), 1)

        avg = int(total_score / len(game_history)) if game_history else 0
        pygame.draw.rect(screen, C_WHITE, (c_center-200, HEIGHT//2 + 30, 200, 50), border_radius=5)
        lbl = font_med.render(f"AVG: {avg} ms", True, C_BG)
        screen.blit(lbl, (c_center - 200 + 100 - lbl.get_width()//2, HEIGHT//2 + 42))

        elapsed = session_end_timestamp - session_start_timestamp
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        pygame.draw.rect(screen, C_WHITE, (c_center+10, HEIGHT//2 + 30, 200, 50), border_radius=5)
        lbl_time = font_med.render(f"TIME: {mins}:{secs:02}", True, C_BG)
        screen.blit(lbl_time, (c_center + 10 + 100 - lbl_time.get_width()//2, HEIGHT//2 + 42))
        
        draw_session_graph(game_history)

        draw_centered("[R] RESTART SESSION", font_mono, (150,150,150), 320)

        if keys[pygame.K_r]:
            current_state = STATE_LANDING
            flush_serial()

    pygame.display.flip()

pygame.quit()
if ser: ser.close()