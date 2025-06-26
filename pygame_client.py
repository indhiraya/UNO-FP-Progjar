# pygame_client.py
import socket
import json
import pygame
import time

# --- Bagian Komunikasi Jaringan ---
SERVER_ADDRESS = ('localhost', 8889)

def send_command(command):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect(SERVER_ADDRESS)
            s.sendall((command + '\r\n').encode('utf-8'))
            response_raw = bytearray()
            while True:
                packet = s.recv(4096)
                if not packet: break
                response_raw.extend(packet)
                if b"\r\n\r\n" in response_raw: break
            
            response_str = response_raw.decode('utf-8', errors='ignore')
            if not response_str: return {"status": "ERROR", "message": "Server tidak mengirim respons."}
            
            json_part = response_str.split("\r\n\r\n", 1)[0]
            if not json_part: return {"status": "ERROR", "message": "Respons dari server kosong."}
            
            return json.loads(json_part)
    except socket.timeout:
        return {"status": "ERROR", "message": "Timeout: Server tidak merespon."}
    except ConnectionRefusedError:
        return {"status": "ERROR", "message": "Koneksi ditolak. Server belum jalan."}
    except json.JSONDecodeError:
        return {"status": "ERROR", "message": "Gagal parse respons (bukan JSON)."}
    except Exception as e:
        return {"status": "ERROR", "message": f"Error jaringan: {e}"}

# --- Inisialisasi dan Konfigurasi Pygame ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
BACKGROUND_COLOR = (7, 99, 36)
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
RED, YELLOW, GREEN, BLUE = (217, 30, 24), (247, 202, 24), (30, 130, 76), (0, 119, 182)
COLOR_MAP = {"red": RED, "yellow": YELLOW, "green": GREEN, "blue": BLUE, "wild": BLACK, "black": BLACK}
TITLE_FONT = pygame.font.Font(None, 74)
INPUT_FONT = pygame.font.Font(None, 48)
BUTTON_FONT = pygame.font.Font(None, 40)
CARD_FONT = pygame.font.Font(None, 32)
INFO_FONT = pygame.font.Font(None, 28)
MSG_FONT = pygame.font.Font(None, 24)
CARD_WIDTH, CARD_HEIGHT, CARD_MARGIN = 80, 120, 10

# --- Fungsi Helper Visual ---
def draw_card(screen, x, y, card_str, selected=False):
    parts = card_str.split()
    color_str, value_str = parts[0], " ".join(parts[1:])
    card_color = COLOR_MAP.get(color_str, BLACK)
    card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
    pygame.draw.rect(screen, card_color, card_rect, border_radius=10)
    if selected: pygame.draw.rect(screen, WHITE, card_rect, 4, border_radius=10)
    text_surf = CARD_FONT.render(value_str, True, WHITE)
    screen.blit(text_surf, text_surf.get_rect(center=card_rect.center))
    return card_rect

def draw_button(screen, text, rect, color, text_color, font=BUTTON_FONT):
    pygame.draw.rect(screen, color, rect, border_radius=15)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))
    return rect

def draw_text(screen, text, font, color, pos, align="center"):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if align == "center":
        text_rect.center = pos
    elif align == "topleft":
        text_rect.topleft = pos
    elif align == "topright":
        text_rect.topright = pos
    screen.blit(text_surf, text_rect)

def ask_color_choice(screen):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    draw_text(screen, "Pilih Warna Baru", TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 100))
    button_width, button_height = 120, 60
    colors = ["red", "green", "blue", "yellow"]
    rects = []
    start_x_colors = (SCREEN_WIDTH - (len(colors) * button_width + (len(colors) - 1) * 40)) / 2
    for i, color in enumerate(colors):
        rect = pygame.Rect(start_x_colors + i * (button_width + 40), SCREEN_HEIGHT/2, button_width, button_height)
        draw_button(screen, color.upper(), rect, COLOR_MAP[color], WHITE)
        rects.append((rect, color))
    pygame.display.flip()
    choosing = True
    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, color in rects:
                    if rect.collidepoint(event.pos): return color

def name_entry_scene(screen):
    player_name = ""
    input_box = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 - 25, 400, 50)
    join_button = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 70, 200, 60)
    active = False
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
                if join_button.collidepoint(event.pos) and len(player_name) > 0:
                    return player_name
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN and len(player_name) > 0: return player_name
                    elif event.key == pygame.K_BACKSPACE: player_name = player_name[:-1]
                    else:
                        if len(player_name) < 15: player_name += event.unicode
        screen.fill(BACKGROUND_COLOR)
        draw_text(screen, "UNO MULTIPLAYER", TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/4))
        draw_text(screen, "Masukkan Nama Pemain:", INFO_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 70))
        pygame.draw.rect(screen, color, input_box, 2, border_radius=10)
        text_surface = INPUT_FONT.render(player_name, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))
        input_box.w = max(400, text_surface.get_width() + 20)
        btn_color = BLUE if len(player_name) > 0 else GRAY
        draw_button(screen, "Join Game", join_button, btn_color, WHITE)
        pygame.display.flip()
        clock.tick(30)


# --- FUNGSI UTAMA GAME (REVISI STRUKTUR LOOP) ---
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UNO Multiplayer")
    player_id = name_entry_scene(screen)
    if not player_id: pygame.quit(); return
    
    # Inisialisasi variabel game
    hand, top_card, current_turn, winner = [], "loading...", "loading...", None
    is_my_turn = False
    status_message = f"Selamat datang, {player_id}!"
    player_statuses = {}
    
    # Tombol
    draw_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2, 180, 50)
    uno_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 70, 180, 50)
    callout_buttons = []

    last_update_time, UPDATE_INTERVAL = 0, 1500
    hand_card_rects, clock, running, scroll_x = [], pygame.time.Clock(), True, 0
    left_arrow_rect = pygame.Rect(10, SCREEN_HEIGHT - 170 + 40, 40, 40)
    right_arrow_rect = pygame.Rect(SCREEN_WIDTH - 50, SCREEN_HEIGHT - 170 + 40, 40, 40)
    
    def update_local_state(new_state):
        nonlocal hand, top_card, current_turn, winner, is_my_turn, status_message, player_statuses
        if new_state and new_state.get("status") == "OK":
            hand = new_state.get("hand", [])
            top_card = new_state.get("top_card", "Error")
            current_turn = new_state.get("current_turn", "Error")
            winner = new_state.get("winner")
            is_my_turn = new_state.get("your_turn", False)
            player_statuses = new_state.get("player_statuses", {})
            server_msg = new_state.get("last_action_message")
            if server_msg: status_message = server_msg
    
    initial_state = send_command(f"join {player_id}")
    update_local_state(initial_state)

    while running:
        # 1. UPDATE STATE DARI SERVER (saat idle)
        current_time = pygame.time.get_ticks()
        if not is_my_turn and not winner and current_time - last_update_time > UPDATE_INTERVAL:
            last_update_time = current_time
            response = send_command(f"get_state {player_id}")
            update_local_state(response)

        # 2. PROSES INPUT EVENT
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEWHEEL: scroll_x -= event.y * 40

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                def send_and_update(command):
                    response = send_command(command)
                    update_local_state(response)

                if left_arrow_rect.collidepoint(mouse_pos): scroll_x -= 60
                elif right_arrow_rect.collidepoint(mouse_pos): scroll_x += 60

                if uno_button_rect.collidepoint(mouse_pos):
                    my_status = player_statuses.get(player_id, {})
                    if my_status.get("count") == 1 and my_status.get("on_uno"):
                        send_and_update(f"uno {player_id}")

                for rect, target_id in callout_buttons:
                    if rect.collidepoint(mouse_pos):
                        send_and_update(f"callout {player_id} {target_id}")
                        break
                
                if is_my_turn and not winner:
                    for i, rect in enumerate(hand_card_rects):
                        if rect.collidepoint(mouse_pos):
                            selected_card = hand[i]
                            if "wild" in selected_card.lower() or "+4" in selected_card:
                                chosen_color = ask_color_choice(screen)
                                if chosen_color: send_and_update(f"play {player_id} {i} {chosen_color}")
                            else: send_and_update(f"play {player_id} {i}")
                            break
                    if draw_button_rect.collidepoint(mouse_pos):
                        send_and_update(f"draw {player_id}")
        
        # 3. UPDATE LOGIKA UI (SETELAH SEMUA INPUT DIPROSES)
        # Blok ini dipindahkan ke sini untuk mencegah IndexError
        hand_card_rects.clear()
        total_hand_width = len(hand) * (CARD_WIDTH + CARD_MARGIN) - CARD_MARGIN
        hand_area_margin = 70 
        visible_width = SCREEN_WIDTH - (2 * hand_area_margin)
        if total_hand_width <= visible_width:
            hand_render_start_x = (SCREEN_WIDTH - total_hand_width) / 2
            scroll_x = 0
        else:
            hand_render_start_x = hand_area_margin
        
        for i in range(len(hand)):
            card_pos_x = hand_render_start_x + i * (CARD_WIDTH + CARD_MARGIN) - scroll_x
            rect = pygame.Rect(card_pos_x, SCREEN_HEIGHT - 170, CARD_WIDTH, CARD_HEIGHT)
            hand_card_rects.append(rect)
        
        max_scroll = max(0, total_hand_width - visible_width)
        scroll_x = max(0, min(scroll_x, max_scroll))

        # 4. GAMBAR SEMUANYA KE LAYAR
        screen.fill(BACKGROUND_COLOR)
        
        draw_text(screen, "Kartu Teratas", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, 50))
        if top_card != "loading...": draw_card(screen, SCREEN_WIDTH / 2 - CARD_WIDTH / 2, 80, top_card)
        turn_text = f"Giliran: {current_turn}"
        turn_color = YELLOW if is_my_turn else WHITE
        draw_text(screen, turn_text, INPUT_FONT, turn_color, (SCREEN_WIDTH / 2, 250))
        if is_my_turn and not winner: draw_text(screen, "GILIRAN ANDA!", INPUT_FONT, YELLOW, (SCREEN_WIDTH / 2, 290))
        draw_text(screen, status_message, MSG_FONT, GRAY, (SCREEN_WIDTH / 2, 350))

        draw_text(screen, "Kartu Anda", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 200))
        for i, card_str in enumerate(hand):
            rect = hand_card_rects[i]
            if rect.right > 0 and rect.left < SCREEN_WIDTH:
                is_hovered = is_my_turn and not winner and rect.collidepoint(mouse_pos)
                draw_card(screen, rect.x, rect.y, card_str, selected=is_hovered)

        draw_button(screen, "Ambil Kartu", draw_button_rect, BLUE, WHITE, font=INFO_FONT)
        if max_scroll > 0:
            draw_button(screen, "<", left_arrow_rect, GRAY, WHITE, font=INPUT_FONT)
            draw_button(screen, ">", right_arrow_rect, GRAY, WHITE, font=INPUT_FONT)
        
        my_status = player_statuses.get(player_id, {})
        if my_status.get("count") == 1 and my_status.get("on_uno"):
            draw_button(screen, "UNO!", uno_button_rect, RED, WHITE)

        draw_text(screen, "Pemain Lain:", INFO_FONT, WHITE, (SCREEN_WIDTH - 10, 20), align="topright")
        opponent_y = 50
        callout_buttons.clear()
        if player_statuses:
            for pid, p_status in player_statuses.items():
                if pid != player_id:
                    count = p_status.get("count", "?")
                    is_on_uno = p_status.get("on_uno", False)
                    text = f"{pid}: {count} kartu"
                    draw_text(screen, text, MSG_FONT, WHITE, (SCREEN_WIDTH - 10, opponent_y), align="topright")
                    if is_on_uno:
                        text_width = MSG_FONT.size(text)[0]
                        button_x = SCREEN_WIDTH - 10 - text_width - 10 - 50
                        callout_rect = pygame.Rect(button_x, opponent_y - 3, 50, 24)
                        draw_button(screen, "!", callout_rect, YELLOW, BLACK, font=MSG_FONT)
                        callout_buttons.append((callout_rect, pid))
                    opponent_y += 25
        
        pygame.display.flip()
        clock.tick(30)
    
    if winner:
        time.sleep(5)

    pygame.quit()

if __name__ == "__main__":
    main()