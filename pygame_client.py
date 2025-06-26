# pygame_client.py (Versi dengan Input Nama di Pygame)

import socket
import json
import pygame
import time

# --- Bagian Komunikasi Jaringan (Tidak Berubah) ---
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
    for i, color in enumerate(colors):
        rect = pygame.Rect(150 + i * (button_width + 40), SCREEN_HEIGHT/2, button_width, button_height)
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
                if not packet:
                    break
                response_raw.extend(packet)
                if b"\r\n\r\n" in response_raw:
                    break
            response_str = response_raw.decode('utf-8')
            if not response_str:
                return {"status": "ERROR", "message": "Server tidak mengirim respons."}
            json_part = response_str.split("\r\n\r\n", 1)[0]
            if not json_part:
                return {"status": "ERROR", "message": "Respons dari server kosong."}
            return json.loads(json_part)
    except socket.timeout:
        return {"status": "ERROR", "message": "Timeout: Server tidak merespon."}
    except ConnectionRefusedError:
        return {"status": "ERROR", "message": "Koneksi ditolak. Pastikan server sudah berjalan."}
    except json.JSONDecodeError:
        return {"status": "ERROR", "message": "Gagal mem-parse respons server (bukan JSON)."}
    except Exception as e:
        return {"status": "ERROR", "message": f"Terjadi error jaringan: {e}"}

# --- Inisialisasi dan Konfigurasi Pygame (Tidak Berubah) ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
BACKGROUND_COLOR = (7, 99, 36)
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
RED, YELLOW, GREEN, BLUE = (217, 30, 24), (247, 202, 24), (30, 130, 76), (0, 119, 182)
COLOR_MAP = {"red": RED, "yellow": YELLOW, "green": GREEN, "blue": BLUE}
TITLE_FONT = pygame.font.Font(None, 74)
INPUT_FONT = pygame.font.Font(None, 48)
BUTTON_FONT = pygame.font.Font(None, 40)
CARD_FONT = pygame.font.Font(None, 32)
INFO_FONT = pygame.font.Font(None, 28)
MSG_FONT = pygame.font.Font(None, 24)
CARD_WIDTH, CARD_HEIGHT, CARD_MARGIN = 80, 120, 10

# --- Fungsi Helper (Tidak Berubah) ---
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

def draw_text(screen, text, font, color, center_pos):
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, text_surf.get_rect(center=center_pos))

# --- FUNGSI BARU UNTUK SCENE INPUT NAMA ---
def name_entry_scene(screen):
    """Menjalankan loop untuk mendapatkan nama pemain. Mengembalikan nama atau None jika keluar."""
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
                return None  # Sinyal untuk keluar dari program

            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
                
                # Cek klik tombol Join
                if join_button.collidepoint(event.pos) and len(player_name) > 0:
                    return player_name # Nama valid, lanjutkan ke game

            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        return player_name # Tekan Enter untuk join
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        # Batasi panjang nama
                        if len(player_name) < 15:
                            player_name += event.unicode

        screen.fill(BACKGROUND_COLOR)
        draw_text(screen, "UNO MULTIPLAYER", TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/4))
        draw_text(screen, "Masukkan Nama Pemain:", INFO_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 70))

        # Gambar input box
        pygame.draw.rect(screen, color, input_box, 2, border_radius=10)
        text_surface = INPUT_FONT.render(player_name, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))
        input_box.w = max(400, text_surface.get_width() + 20) # Lebarkan box jika nama panjang

        # Gambar tombol Join
        btn_color = BLUE if len(player_name) > 0 else GRAY
        draw_button(screen, "Join Game", join_button, btn_color, WHITE)
        
        pygame.display.flip()
        clock.tick(30)


# --- FUNGSI UTAMA GAME (DIMODIFIKASI) ---
def main():
    selected_indexes = set()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UNO Multiplayer")

    # Panggil scene input nama terlebih dahulu
    player_id = name_entry_scene(screen)

    # Jika pemain menutup jendela saat input nama, keluar dari program
    if not player_id:
        pygame.quit()
        return

    # Tampilkan pesan "Joining..." di layar
    screen.fill(BACKGROUND_COLOR)
    draw_text(screen, f"Joining as {player_id}...", INPUT_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    pygame.display.flip()

    join_response = send_command(f"join {player_id}")
    if join_response.get("status") != "OK":
        # Tampilkan error jika gagal join dan tunggu sebelum keluar
        screen.fill(BACKGROUND_COLOR)
        draw_text(screen, "Gagal terhubung ke server.", INPUT_FONT, RED, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
        draw_text(screen, join_response.get('message', ''), MSG_FONT, GRAY, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
        pygame.display.flip()
        time.sleep(3)
        return
    
    # Inisialisasi variabel untuk loop game utama
    hand, top_card, current_turn = [], "loading...", "loading..."
    is_my_turn = False
    status_message = f"Selamat datang, {player_id}!"
    draw_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 25, 180, 50)
    last_update_time, UPDATE_INTERVAL = 0, 2000
    hand_card_rects = []
    clock = pygame.time.Clock()
    running = True

    # --- Loop Game Utama (tidak ada perubahan di dalam loop ini) ---
    while running:
        # 1. UPDATE STATE DARI SERVER
        current_time = pygame.time.get_ticks()
        if current_time - last_update_time > UPDATE_INTERVAL:
            # ... (logika polling sama seperti sebelumnya) ...
            last_update_time = current_time
            top_card_info = send_command("top_card")
            if top_card_info.get("status") == "OK":
                top_card = top_card_info.get("top_card", "Error Card")
                current_turn = top_card_info.get("current_turn", "Error Turn")
            else:
                status_message = top_card_info.get("message", "Gagal update status.")
            hand_info = send_command(f"hand {player_id}")
            if hand_info.get("status") == "OK":
                hand = hand_info.get("hand", [])
                is_my_turn = hand_info.get("your_turn", False)
                if len(hand) == 0:
                    status_message = "Kamu SUDAH MENANG! 🎉"
                    is_my_turn = False  # Jangan izinkan input lagi
            else:
                status_message = hand_info.get("message", "Gagal update tangan.")

            if len(hand) == 0 and top_card != "loading...":
                status_message = "Kamu MENANG! 🎉"

        # 2. HITUNG POSISI DAN PROSES INPUT
        mouse_pos = pygame.mouse.get_pos()
        hand_card_rects.clear()
        total_hand_width = len(hand) * (CARD_WIDTH + CARD_MARGIN) - CARD_MARGIN
        start_x = (SCREEN_WIDTH - total_hand_width) / 2
        for i in range(len(hand)):
            rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_MARGIN), SCREEN_HEIGHT - 170, CARD_WIDTH, CARD_HEIGHT)
            hand_card_rects.append(rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if is_my_turn:
                    for i, rect in enumerate(hand_card_rects):
                        if rect.collidepoint(mouse_pos):
                            selected_card = hand[i]
                            if "+4" in selected_card or "wild" in selected_card:
                                chosen_color = ask_color_choice(screen)
                                if not chosen_color:
                                    status_message = "Batal pilih warna."
                                    continue
                                result = send_command(f"play {player_id} {i} {chosen_color}")
                            else:
                                result = send_command(f"play {player_id} {i}")
                            status_message = result.get("result") or result.get("message", "Error")
                            last_update_time = 0
                            break 
                    if draw_button_rect.collidepoint(mouse_pos):
                        # Kirim perintah draw ke server, lalu update status dan giliran
                        result = send_command(f"draw {player_id}")
                        status_message = result.get("message", "Error")
                        last_update_time = 0
                        # Setelah draw, giliran otomatis pindah, jadi is_my_turn akan jadi False pada polling berikutnya
        winner_check = send_command("winner")
        
        if winner_check.get("winner"):
            winner_name = winner_check["winner"]
            if winner_name == player_id:
                status_message = "🎉 Kamu MENANG! 🎉"
            else:
                status_message = f"Permainan berakhir. Pemenang: {winner_name}"
            running = False  # keluar dari loop



        # 3. GAMBAR SEMUANYA
        screen.fill(BACKGROUND_COLOR)
        # ... (logika menggambar sama seperti sebelumnya) ...
        draw_text(screen, "Kartu Teratas", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, 50))
        if top_card != "loading...":
            draw_card(screen, SCREEN_WIDTH / 2 - CARD_WIDTH / 2, 80, top_card)
        turn_text = f"Giliran: {current_turn}"
        turn_color = YELLOW if is_my_turn else WHITE
        draw_text(screen, turn_text, INPUT_FONT, turn_color, (SCREEN_WIDTH / 2, 250))
        if is_my_turn:
            draw_text(screen, "GILIRAN ANDA!", INPUT_FONT, YELLOW, (SCREEN_WIDTH / 2, 290))
        draw_button(screen, "Ambil Kartu", draw_button_rect, BLUE, WHITE, font=INFO_FONT)
        draw_text(screen, status_message, MSG_FONT, GRAY, (SCREEN_WIDTH / 2, 350))
        draw_text(screen, "Kartu Anda", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 200))
        for i, card_str in enumerate(hand):
            rect = hand_card_rects[i] 
            is_hovered = is_my_turn and rect.collidepoint(mouse_pos)
            draw_card(screen, rect.x, rect.y, card_str, selected=is_hovered)
        pygame.display.flip()
        clock.tick(30)
        if len(hand) == 0:
            draw_text(screen, "🎉 KAMU MENANG! 🎉", TITLE_FONT, YELLOW, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))

    pygame.quit()

if __name__ == "__main__":
    main()