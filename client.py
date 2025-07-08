# client.py
import pygame
import sys
import json
import socket
import time

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
    parts = card_str.split(" ", 1)
    color_str, value_str = parts[0], parts[1]
    
    display_text = value_str
    if value_str == "Draw Two": display_text = "+2"
    elif value_str == "Wild Draw Four": display_text = "+4"

    card_color = COLOR_MAP.get(color_str.lower(), BLACK)
    card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
    pygame.draw.rect(screen, card_color, card_rect, border_radius=10)
    if selected: pygame.draw.rect(screen, WHITE, card_rect, 4, border_radius=10)
    text_surf = CARD_FONT.render(display_text, True, WHITE)
    screen.blit(text_surf, text_surf.get_rect(center=card_rect.center))

def draw_button(screen, text, rect, color, text_color, font=BUTTON_FONT):
    pygame.draw.rect(screen, color, rect, border_radius=15)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))

def draw_text(screen, text, font, color, pos, align="center"):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if align == "center": text_rect.center = pos
    elif align == "topleft": text_rect.topleft = pos
    elif align == "topright": text_rect.topright = pos
    screen.blit(text_surf, text_rect)

def ask_color_choice(screen):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    draw_text(screen, "Pilih Warna Baru", TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 100))
    colors, rects = ["red", "green", "blue", "yellow"], []
    button_width, button_height = 120, 60
    start_x = (SCREEN_WIDTH - (len(colors) * button_width + (len(colors) - 1) * 40)) / 2
    for i, color in enumerate(colors):
        rect = pygame.Rect(start_x + i * (button_width + 40), SCREEN_HEIGHT/2, button_width, button_height)
        draw_button(screen, color.upper(), rect, COLOR_MAP[color], WHITE)
        rects.append((rect, color))
    pygame.display.flip()
    while True:
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
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                active = input_box.collidepoint(event.pos)
                if join_button.collidepoint(event.pos) and player_name.strip(): return player_name.strip()
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN and player_name.strip(): return player_name.strip()
                    elif event.key == pygame.K_BACKSPACE: player_name = player_name[:-1]
                    else:
                        if len(player_name) < 15: player_name += event.unicode
        screen.fill(BACKGROUND_COLOR)
        draw_text(screen, "UNO MULTIPLAYER", TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/4))
        draw_text(screen, "Masukkan Nama Pemain:", INFO_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 70))
        color = pygame.Color('dodgerblue2') if active else pygame.Color('lightskyblue3')
        pygame.draw.rect(screen, color, input_box, 2, border_radius=10)
        text_surface = INPUT_FONT.render(player_name, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))
        btn_color = BLUE if player_name.strip() else GRAY
        draw_button(screen, "Join Game", join_button, btn_color, WHITE)
        pygame.display.flip()
        clock.tick(30)

# --- Kelas Utama Client & Game Loop ---
class UnoClient:
    def __init__(self, player_id):
        self.player_id = player_id
        self.server_address = ('localhost', 8889)

    def send_command(self, command_body):
        try:
            request = f"POST /uno HTTP/1.0\r\n\r\n{command_body}"
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect(self.server_address)
                sock.sendall(request.encode('utf-8'))
                data_received = bytearray()
                while True:
                    chunk = sock.recv(4096)
                    if not chunk: break
                    data_received.extend(chunk)
                response_str = data_received.decode('utf-8', errors='ignore')
                header_end = response_str.find('\r\n\r\n')
                if header_end == -1: return {"status": "ERROR", "message": "Invalid HTTP response"}
                body = response_str[header_end:].strip()
                return json.loads(body) if body else {"status": "ERROR", "message": "Empty JSON body"}
        except Exception as e:
            print(f"Client Error: {e}")
            return {"status": "ERROR", "message": str(e)}

class UnoGame:
    def __init__(self, screen, player_id):
        self.screen = screen
        self.player_id = player_id
        self.client = UnoClient(player_id)
        self.clock = pygame.time.Clock()
        self.state = {}
        self.hand_cards = []
        self.hand_card_rects = []
        self.callout_buttons = []
        self.scroll_x = 0
        self.last_update_time = 0
        self.UPDATE_INTERVAL = 1500

    def _update_local_state(self, new_state):
        if new_state and new_state.get("status") == "OK":
            self.state = new_state
            self.hand_cards = new_state.get("hand", [])
        elif new_state:
            print(f"Server returned error: {new_state.get('message')}")

    def _send_and_update(self, command):
        response = self.client.send_command(command)
        self._update_local_state(response)

    def run(self):
        self._send_and_update(f"state {self.player_id}")
        
        draw_btn_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2, 180, 50)
        uno_btn_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 70, 180, 50)
        left_arrow_rect = pygame.Rect(10, SCREEN_HEIGHT - 170 + 40, 40, 40)
        right_arrow_rect = pygame.Rect(SCREEN_WIDTH - 50, SCREEN_HEIGHT - 170 + 40, 40, 40)

        running = True
        while running:
            is_my_turn = self.state.get("your_turn", False)
            winner = self.state.get("winner")
            if not is_my_turn and not winner and pygame.time.get_ticks() - self.last_update_time > self.UPDATE_INTERVAL:
                self.last_update_time = pygame.time.get_ticks()
                self._send_and_update(f"state {self.player_id}")

            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEWHEEL: self.scroll_x -= event.y * 40
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if left_arrow_rect.collidepoint(mouse_pos): self.scroll_x -= 60
                    elif right_arrow_rect.collidepoint(mouse_pos): self.scroll_x += 60
                    elif uno_btn_rect.collidepoint(mouse_pos): self._send_and_update(f"uno {self.player_id}")
                    elif draw_btn_rect.collidepoint(mouse_pos) and is_my_turn: self._send_and_update(f"draw {self.player_id}")
                    else:
                        clicked_on_callout = False
                        for rect, target_id in self.callout_buttons:
                            if rect.collidepoint(mouse_pos):
                                self._send_and_update(f"callout {self.player_id} {target_id}")
                                clicked_on_callout = True
                                break
                        
                        if not clicked_on_callout and is_my_turn and not winner:
                            for i, rect in enumerate(self.hand_card_rects):
                                if rect.collidepoint(mouse_pos):
                                    card_str = self.hand_cards[i]
                                    if "black" in card_str:
                                        color = ask_color_choice(self.screen)
                                        if color: self._send_and_update(f"play {self.player_id} {i} {color}")
                                    else:
                                        self._send_and_update(f"play {self.player_id} {i}")
                                    break
            
            self._update_ui_logic()
            self._draw_all(mouse_pos, draw_btn_rect, uno_btn_rect, left_arrow_rect, right_arrow_rect)
            
            self.clock.tick(30)
            if winner:
                time.sleep(5)
                running = False
        
        pygame.quit()
        sys.exit()

    def _update_ui_logic(self):
        self.hand_card_rects.clear()
        total_hand_width = len(self.hand_cards) * (CARD_WIDTH + CARD_MARGIN) - CARD_MARGIN
        hand_area_margin = 70 
        visible_width = SCREEN_WIDTH - (2 * hand_area_margin)
        
        if total_hand_width <= visible_width:
            start_x, self.scroll_x = (SCREEN_WIDTH - total_hand_width) / 2, 0
        else:
            start_x = hand_area_margin
        
        for i in range(len(self.hand_cards)):
            card_pos_x = start_x + i * (CARD_WIDTH + CARD_MARGIN) - self.scroll_x
            rect = pygame.Rect(card_pos_x, SCREEN_HEIGHT - 170, CARD_WIDTH, CARD_HEIGHT)
            self.hand_card_rects.append(rect)
        
        max_scroll = max(0, total_hand_width - visible_width)
        self.scroll_x = max(0, min(self.scroll_x, max_scroll))

    def _draw_all(self, mouse_pos, draw_btn, uno_btn, left_arrow, right_arrow):
        self.screen.fill(BACKGROUND_COLOR)
        
        top_card = self.state.get("top_card", "")
        current_turn = self.state.get("current_turn", "")
        status_message = self.state.get("last_action_message", "")
        is_my_turn = self.state.get("your_turn", False)
        winner = self.state.get("winner")
        player_statuses = self.state.get("player_statuses", {})

        draw_text(self.screen, "Kartu Teratas", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, 50))
        if top_card: draw_card(self.screen, SCREEN_WIDTH / 2 - CARD_WIDTH / 2, 80, top_card)
        turn_color = YELLOW if is_my_turn else WHITE
        draw_text(self.screen, f"Giliran: {current_turn}", INPUT_FONT, turn_color, (SCREEN_WIDTH / 2, 250))
        if is_my_turn and not winner: draw_text(self.screen, "GILIRAN ANDA!", INPUT_FONT, YELLOW, (SCREEN_WIDTH / 2, 290))
        draw_text(self.screen, status_message, MSG_FONT, GRAY, (SCREEN_WIDTH / 2, 350))

        draw_text(self.screen, "Kartu Anda", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 200))
        for i, card_str in enumerate(self.hand_cards):
            rect = self.hand_card_rects[i]
            if rect.right > 0 and rect.left < SCREEN_WIDTH:
                hover = is_my_turn and not winner and rect.collidepoint(mouse_pos)
                draw_card(self.screen, rect.x, rect.y, card_str, hover)
        
        draw_button(self.screen, "Ambil Kartu", draw_btn, BLUE, WHITE, font=INFO_FONT)
        if self.scroll_x > 0 or (self.hand_card_rects and self.hand_card_rects[-1].right > SCREEN_WIDTH):
            draw_button(self.screen, "<", left_arrow, GRAY, WHITE, font=INPUT_FONT)
            draw_button(self.screen, ">", right_arrow, GRAY, WHITE, font=INPUT_FONT)
        
        # --- PERUBAHAN UTAMA DI SINI ---
        # 1. Tentukan warna tombol UNO berdasarkan state semua pemain
        uno_button_color = GRAY  # Warna default (netral)
        is_anybody_on_uno = any(p_status.get("on_uno", False) for p_status in player_statuses.values())
        if is_anybody_on_uno:
            uno_button_color = RED # Warna bahaya jika ada yang UNO

        # 2. Gambar tombol UNO secara permanen dengan warna dinamis
        draw_button(self.screen, "UNO!", uno_btn, uno_button_color, WHITE)
            
        # Gambar status pemain lain
        draw_text(self.screen, "Pemain Lain:", INFO_FONT, WHITE, (SCREEN_WIDTH - 10, 20), align="topright")
        y_offset = 50
        self.callout_buttons.clear()
        for pid, p_status in player_statuses.items():
            if pid != self.player_id:
                count, on_uno = p_status.get("count", "?"), p_status.get("on_uno", False)
                text = f"{pid}: {count} kartu"
                draw_text(self.screen, text, MSG_FONT, WHITE, (SCREEN_WIDTH - 10, y_offset), align="topright")
                if on_uno:
                    text_width = MSG_FONT.size(text)[0]
                    btn_x = SCREEN_WIDTH - 10 - text_width - 10 - 50
                    rect = pygame.Rect(btn_x, y_offset - 3, 50, 24)
                    draw_button(self.screen, "!", rect, YELLOW, BLACK, font=MSG_FONT)
                    self.callout_buttons.append((rect, pid))
                y_offset += 25
        pygame.display.flip()

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    player_id = name_entry_scene(screen)
    if player_id:
        game = UnoGame(screen, player_id)
        game.run()

if __name__ == "__main__":
    main()