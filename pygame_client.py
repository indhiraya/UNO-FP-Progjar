# pygame_client.py
import socket
import json
import pygame
import time

# ... (Fungsi send_command, ask_color_choice, dan konstanta tidak berubah) ...
SERVER_ADDRESS = ('localhost', 8889)

def ask_color_choice(screen):
    """Menampilkan popup untuk memilih warna jika kartu adalah +4 atau wild."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    draw_text(screen, "Pilih Warna Baru", TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 100))

    button_width, button_height = 120, 60
    colors = ["red", "green", "blue", "yellow"]
    rects = []
    # Posisi tombol warna di tengah
    start_x_colors = (SCREEN_WIDTH - (len(colors) * button_width + (len(colors) - 1) * 40)) / 2
    for i, color in enumerate(colors):
        rect = pygame.Rect(start_x_colors + i * (button_width + 40), SCREEN_HEIGHT/2, button_width, button_height)
        draw_button(screen, color.upper(), rect, COLOR_MAP[color], WHITE)
        rects.append((rect, color))

    pygame.display.flip()

    choosing = True
    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, color in rects:
                    if rect.collidepoint(event.pos):
                        return color

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

# --- Inisialisasi dan Konfigurasi Pygame (Tidak Berubah) ---
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
# ... (name_entry_scene, draw_card, draw_button, draw_text tidak berubah) ...
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

def draw_text(screen, text, font, color, center_pos, align="center"):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if align == "center":
        text_rect.center = center_pos
    elif align == "topleft":
        text_rect.topleft = center_pos
    screen.blit(text_surf, text_rect)

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
            if event.type == pygame.QUIT:
                return None
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
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        return player_name
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        if len(player_name) < 15:
                            player_name += event.unicode
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


# --- FUNGSI UTAMA GAME ---
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UNO Multiplayer")

    player_id = name_entry_scene(screen)
    if not player_id:
        pygame.quit()
        return

    screen.fill(BACKGROUND_COLOR)
    draw_text(screen, f"Joining as {player_id}...", INPUT_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    pygame.display.flip()

    join_response = send_command(f"join {player_id}")
    if join_response.get("status") != "OK":
        # ... (error handling tidak berubah) ...
        return
    
    # Inisialisasi variabel game
    hand, top_card, current_turn = [], "loading...", "loading..."
    is_my_turn = False
    status_message = f"Selamat datang, {player_id}!"
    last_game_status_message = ""
    # BARU: Variabel untuk menyimpan jumlah kartu lawan
    opponent_cards = {}

    # Definisi Rect Tombol
    draw_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2, 180, 50)
    # BARU: Tombol UNO!
    uno_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 70, 180, 50)

    last_update_time, UPDATE_INTERVAL = 0, 1000 # Update lebih cepat
    hand_card_rects = []
    clock = pygame.time.Clock()
    running = True
    scroll_x = 0
    winner = None

    arrow_button_y = SCREEN_HEIGHT - 170 + (CARD_HEIGHT // 2) - 20
    left_arrow_rect = pygame.Rect(10, arrow_button_y, 40, 40)
    right_arrow_rect = pygame.Rect(SCREEN_WIDTH - 50, arrow_button_y, 40, 40)

    while running:
        # 1. UPDATE STATE DARI SERVER
        current_time = pygame.time.get_ticks()
        if not winner and current_time - last_update_time > UPDATE_INTERVAL:
            last_update_time = current_time
            
            # Ambil info kartu teratas dan status game
            top_card_info = send_command("top_card")
            if top_card_info.get("status") == "OK":
                top_card = top_card_info.get("top_card", "Error")
                current_turn = top_card_info.get("current_turn", "Error")
                # BARU: Ambil pesan status dari server
                game_status = top_card_info.get("last_status", "")
                if game_status and game_status != last_game_status_message:
                    status_message = game_status
                    last_game_status_message = game_status

            # Ambil info tangan
            hand_info = send_command(f"hand {player_id}")
            if hand_info.get("status") == "OK":
                hand = hand_info.get("hand", [])
                is_my_turn = hand_info.get("your_turn", False)

            # BARU: Ambil info jumlah kartu semua pemain
            status_info = send_command("status")
            if status_info.get("status") == "OK":
                opponent_cards = status_info.get("players", {})

            # Cek pemenang
            winner_check = send_command("winner")
            if winner_check.get("winner"):
                winner = winner_check["winner"]
                if winner == player_id:
                    status_message = "🎉 Kamu MENANG! 🎉"
                else:
                    status_message = f"Pemenang: {winner}"
                is_my_turn = False

        # 2. PROSES INPUT
        mouse_pos = pygame.mouse.get_pos()
        # ... (logika posisi kartu dinamis tidak berubah) ...
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

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEWHEEL: scroll_x -= event.y * 40

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Klik tombol scroll
                if left_arrow_rect.collidepoint(mouse_pos): scroll_x -= 60
                elif right_arrow_rect.collidepoint(mouse_pos): scroll_x += 60

                # BARU: Klik tombol UNO!
                if len(hand) == 1 and uno_button_rect.collidepoint(mouse_pos):
                    response = send_command(f"uno {player_id}")
                    status_message = response.get("message", "Error")

                if is_my_turn and not winner:
                    # Klik kartu
                    for i, rect in enumerate(hand_card_rects):
                        if rect.collidepoint(mouse_pos):
                            selected_card = hand[i]
                            if "wild" in selected_card.lower() or "+4" in selected_card:
                                chosen_color = ask_color_choice(screen)
                                if chosen_color:
                                    result = send_command(f"play {player_id} {i} {chosen_color}")
                                    status_message = result.get("result") or result.get("message", "Error")
                                    last_update_time = 0
                            else:
                                result = send_command(f"play {player_id} {i}")
                                status_message = result.get("result") or result.get("message", "Error")
                                last_update_time = 0
                            break
                    # Klik tombol Ambil Kartu
                    if draw_button_rect.collidepoint(mouse_pos):
                        result = send_command(f"draw {player_id}")
                        status_message = result.get("message", "Error")
                        last_update_time = 0
        
        max_scroll = max(0, total_hand_width - visible_width)
        scroll_x = max(0, min(scroll_x, max_scroll))

        # 3. GAMBAR SEMUANYA
        screen.fill(BACKGROUND_COLOR)
        
        # Gambar info utama
        draw_text(screen, "Kartu Teratas", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, 50))
        if top_card != "loading...":
            draw_card(screen, SCREEN_WIDTH / 2 - CARD_WIDTH / 2, 80, top_card)
        turn_text = f"Giliran: {current_turn}"
        turn_color = YELLOW if is_my_turn else WHITE
        draw_text(screen, turn_text, INPUT_FONT, turn_color, (SCREEN_WIDTH / 2, 250))
        if is_my_turn and not winner:
            draw_text(screen, "GILIRAN ANDA!", INPUT_FONT, YELLOW, (SCREEN_WIDTH / 2, 290))
        draw_text(screen, status_message, MSG_FONT, GRAY, (SCREEN_WIDTH / 2, 350))

        # Gambar kartu di tangan
        draw_text(screen, "Kartu Anda", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 200))
        for i, card_str in enumerate(hand):
            # ... (logika render kartu tidak berubah) ...
            rect = hand_card_rects[i]
            if rect.right > 0 and rect.left < SCREEN_WIDTH:
                is_hovered = is_my_turn and not winner and rect.collidepoint(mouse_pos)
                draw_card(screen, rect.x, rect.y, card_str, selected=is_hovered)

        # Gambar tombol-tombol
        draw_button(screen, "Ambil Kartu", draw_button_rect, BLUE, WHITE, font=INFO_FONT)
        # BARU: Gambar tombol UNO! jika kartu sisa 1
        if len(hand) == 1:
            draw_button(screen, "UNO!", uno_button_rect, RED, WHITE)
        if max_scroll > 0:
            draw_button(screen, "<", left_arrow_rect, GRAY, WHITE, font=INPUT_FONT)
            draw_button(screen, ">", right_arrow_rect, GRAY, WHITE, font=INPUT_FONT)

        # BARU: Gambar status kartu lawan
        opponent_y = 40
        draw_text(screen, "Pemain Lain:", INFO_FONT, WHITE, (820, opponent_y))
        opponent_y += 30
        for pid, count in opponent_cards.items():
            if pid != player_id:
                text = f"- {pid}: {count} kartu"
                draw_text(screen, text, MSG_FONT, WHITE, (820, opponent_y), align="topleft")
                opponent_y += 25

        pygame.display.flip()
        clock.tick(30)
    
    if winner:
        time.sleep(5)
    pygame.quit()

if __name__ == "__main__":
    main()