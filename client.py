import socket
import json
import pygame
import time

SERVER_ADDRESS = ('localhost', 8889)

def send_command(command):
    try:
        request_body = command + "\r\n\r\n"
        http_request = (
            f"POST /uno HTTP/1.0\r\n"
            f"Host: {SERVER_ADDRESS[0]}\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(request_body)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{request_body}"
        )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect(SERVER_ADDRESS)
            s.sendall(http_request.encode('utf-8'))

            response_raw = bytearray()
            while True:
                packet = s.recv(4096)
                if not packet:
                    break
                response_raw.extend(packet)

        response_str = response_raw.decode('utf-8', errors='ignore')
        header_end = response_str.find("\r\n\r\n")
        if header_end == -1:
            return {"status": "ERROR", "message": "Invalid HTTP response from server."}

        body = response_str[header_end + 4:].strip()
        if not body:
            return {"status": "ERROR", "message": "Empty response body from server."}

        return json.loads(body)

    except socket.timeout:
        return {"status": "ERROR", "message": "Timeout: Server didn't respond."}
    except ConnectionRefusedError:
        return {"status": "ERROR", "message": "Connection refused. Is the server running?"}
    except json.JSONDecodeError as e:
        return {"status": "ERROR", "message": f"Failed to parse JSON: {e}"}
    except Exception as e:
        return {"status": "ERROR", "message": f"Unexpected error: {e}"}


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

GAME_STATE_NAME_ENTRY = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

def draw_card(screen, x, y, card_str, selected=False):
    parts = card_str.split()
    color_str, value_str = parts[0].lower(), " ".join(parts[1:])
    card_color = COLOR_MAP.get(color_str, BLACK)

    card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
    pygame.draw.rect(screen, card_color, card_rect, border_radius=10)

    if selected:
        pygame.draw.rect(screen, WHITE, card_rect, 4, border_radius=10)

    text_surf_value = CARD_FONT.render(value_str, True, WHITE)
    screen.blit(text_surf_value, text_surf_value.get_rect(center=card_rect.center))
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
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_text(screen, "Pilih Warna Baru", TITLE_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))

    button_width, button_height = 120, 60
    colors = ["red", "green", "blue", "yellow"]
    rects = []
    start_x_colors = (SCREEN_WIDTH - (len(colors) * button_width + (len(colors) - 1) * 40)) / 2
    for i, color in enumerate(colors):
        rect = pygame.Rect(start_x_colors + i * (button_width + 40), SCREEN_HEIGHT / 2, button_width, button_height)
        draw_button(screen, color.upper(), rect, COLOR_MAP[color], WHITE)
        rects.append((rect, color))

    pygame.display.flip()

    choosing = True
    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, color in rects:
                    if rect.collidepoint(event.pos):
                        return color

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
                active = input_box.collidepoint(event.pos)
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
        draw_text(screen, "UNO MULTIPLAYER", TITLE_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
        draw_text(screen, "Masukkan Nama Pemain:", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 70))

        pygame.draw.rect(screen, color, input_box, 2, border_radius=10)
        text_surface = INPUT_FONT.render(player_name, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))

        btn_color = BLUE if len(player_name) > 0 else GRAY
        draw_button(screen, "Join Game", join_button, btn_color, WHITE)

        pygame.display.flip()
        clock.tick(30)

def main_game_loop(screen, player_name):
    clock = pygame.time.Clock()
    selected_card_index = None
    message = ""
    state = None
    last_state_fetch = 0
    polling_interval = 0.2  

    draw_button_rect = pygame.Rect(850, SCREEN_HEIGHT - 160, 120, 50)
    uno_button_rect = pygame.Rect(850, SCREEN_HEIGHT - 100, 120, 50)

    running = True
    while running:
        now = time.time()
        if now - last_state_fetch > polling_interval:
            state = send_command(f"state {player_name}")
            last_state_fetch = now

        screen.fill(BACKGROUND_COLOR)

        if not state or state.get("status") != "OK":
            draw_text(screen, "Error fetching game state or not connected.", INFO_FONT, RED, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            clock.tick(30)
            continue

        if state.get("winner"):
            winner = state["winner"]
            if winner == player_name:
                msg = "Selamat! Kamu menang!"
            else:
                msg = f"Pemenang: {winner}"
            draw_text(screen, msg, TITLE_FONT, WHITE, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            clock.tick(30)
            continue

        hand = state.get("hand", [])
        top_card = state.get("top_card", "")
        turn = state.get("current_turn", "")
        last_action_message = state.get("last_action_message", "")
        can_declare_uno = state.get("can_declare_uno", False)

        draw_text(screen, f"Nama: {player_name}", INFO_FONT, WHITE, (20, 20), "topleft")
        draw_text(screen, f"Giliran: {turn}", INFO_FONT, WHITE, (20, 50), "topleft")
        draw_text(screen, f"Top Card: {top_card}", INFO_FONT, WHITE, (20, 80), "topleft")
        draw_text(screen, f"Pesan: {last_action_message}", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, 20), "center")

        if top_card:
            draw_card(screen, 20, 100, top_card)

        hand_start_x = 20
        hand_y = SCREEN_HEIGHT - CARD_HEIGHT - 60
        card_rects = []
        for idx, card in enumerate(hand):
            x = hand_start_x + idx * (CARD_WIDTH + CARD_MARGIN)
            rect = draw_card(screen, x, hand_y, card, selected=(idx == selected_card_index))
            card_rects.append(rect)

        draw_button(screen, "Draw Card", draw_button_rect, BLUE, WHITE)
        draw_button(screen, "UNO", uno_button_rect, GREEN if state.get("can_press_uno", False) else GRAY, WHITE)


        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos

                if turn == player_name:
                    for idx, rect in enumerate(card_rects):
                        if rect.collidepoint(mouse_pos):
                            if selected_card_index == idx:
                                card_to_play = hand[idx]
                                if "wild" in card_to_play.lower() or "+4" in card_to_play.lower():
                                    chosen_color = ask_color_choice(screen)
                                    if chosen_color is None:
                                        message = "Batal memilih warna."
                                        continue
                                    command = f"play {player_name} {idx} {chosen_color}"
                                else:
                                    command = f"play {player_name} {idx}"

                                response = send_command(command)
                                if response.get("status") == "OK":
                                    message = f"Berhasil main kartu {card_to_play}"
                                    selected_card_index = None
                                else:
                                    message = f"Gagal main kartu: {response.get('message')}"
                                    selected_card_index = None
                            else:
                                selected_card_index = idx

                if draw_button_rect.collidepoint(mouse_pos) and turn == player_name:
                    response = send_command(f"draw {player_name}")
                    if response.get("status") == "OK":
                        message = "Berhasil mengambil kartu."
                        selected_card_index = None
                    else:
                        message = f"Gagal draw: {response.get('message')}"
                elif uno_button_rect.collidepoint(mouse_pos) and state.get("can_press_uno", False):
                    response = send_command(f"press_uno_button {player_name}")
                    if response.get("status") == "OK":
                        message = response.get("message", "UNO ditekan!")
                    else:
                        message = f"Gagal tekan UNO: {response.get('message')}"
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        if message:
            draw_text(screen, message, MSG_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20))
            message = ""

        clock.tick(30)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UNO Multiplayer Client")

    player_name = name_entry_scene(screen)
    if not player_name:
        pygame.quit()
        return

    join_resp = send_command(f"join {player_name}")
    if join_resp.get("status") != "OK":
        print(f"Gagal join: {join_resp.get('message')}")
        pygame.quit()
        return

    main_game_loop(screen, player_name)

    pygame.quit()

if __name__ == "__main__":
    main()
