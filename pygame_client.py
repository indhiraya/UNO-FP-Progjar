# pygame_client.py
import socket
import json
import pygame
import time

# --- Network Communication ---
# This section handles all communication with the game server.

SERVER_ADDRESS = ('localhost', 8889)

def send_command(command):
    """
    Connects to the server, sends a command, and returns the parsed JSON response.
    Includes robust error handling for common network issues.
    """
    try:
        # Establish a new connection for each command.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)  # Prevent the client from hanging indefinitely.
            s.connect(SERVER_ADDRESS)
            
            # Send the command with a clear terminator.
            s.sendall((command + '\r\n').encode('utf-8'))
            
            # Read the response until the terminator is found.
            response_raw = bytearray()
            while True:
                packet = s.recv(4096)
                if not packet: break
                response_raw.extend(packet)
                if b"\r\n\r\n" in response_raw: break
            
            # Process and parse the response.
            response_str = response_raw.decode('utf-8', errors='ignore')
            if not response_str:
                return {"status": "ERROR", "message": "Server didn't send a response."}
            
            # The server uses a double newline to separate the JSON from other data.
            json_part = response_str.split("\r\n\r\n", 1)[0]
            if not json_part:
                return {"status": "ERROR", "message": "Empty response from server."}
            
            return json.loads(json_part)

    # Handle specific network and data parsing errors gracefully.
    except socket.timeout:
        return {"status": "ERROR", "message": "Timeout: Server didn't respond."}
    except ConnectionRefusedError:
        return {"status": "ERROR", "message": "Connection refused. Is the server running?"}
    except json.JSONDecodeError:
        return {"status": "ERROR", "message": "Failed to parse server response (not valid JSON)."}
    except Exception as e:
        return {"status": "ERROR", "message": f"An unexpected network error occurred: {e}"}

# --- Pygame UI Constants and Setup ---
# This section initializes Pygame and defines all constants for UI elements.

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
BACKGROUND_COLOR = (7, 99, 36) # Dark green
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
RED, YELLOW, GREEN, BLUE = (217, 30, 24), (247, 202, 24), (30, 130, 76), (0, 119, 182)

# Map color names to their RGB values for easy lookup.
COLOR_MAP = {"red": RED, "yellow": YELLOW, "green": GREEN, "blue": BLUE, "wild": BLACK, "black": BLACK}

# Define fonts for different text elements.
TITLE_FONT = pygame.font.Font(None, 74)
INPUT_FONT = pygame.font.Font(None, 48)
BUTTON_FONT = pygame.font.Font(None, 40)
CARD_FONT = pygame.font.Font(None, 32)
INFO_FONT = pygame.font.Font(None, 28)
MSG_FONT = pygame.font.Font(None, 24)

# Define dimensions for cards.
CARD_WIDTH, CARD_HEIGHT, CARD_MARGIN = 80, 120, 10

# Define the different states the game can be in.
GAME_STATE_NAME_ENTRY = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

# --- UI Helper Functions ---
# These functions handle the drawing of common UI components.

def draw_card(screen, x, y, card_str, selected=False):
    """Draws a single UNO card on the screen."""
    parts = card_str.split()
    color_str, value_str = parts[0], " ".join(parts[1:])
    card_color = COLOR_MAP.get(color_str, BLACK)
    
    card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
    pygame.draw.rect(screen, card_color, card_rect, border_radius=10)
    
    # Draw a white border if the card is selected (hovered over).
    if selected:
        pygame.draw.rect(screen, WHITE, card_rect, 4, border_radius=10)
    
    text_surf_value = CARD_FONT.render(value_str, True, WHITE)
    screen.blit(text_surf_value, text_surf_value.get_rect(center=card_rect.center))
    
    return card_rect

def draw_button(screen, text, rect, color, text_color, font=BUTTON_FONT):
    """Draws a clickable button with text."""
    pygame.draw.rect(screen, color, rect, border_radius=15)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))
    return rect

def draw_text(screen, text, font, color, pos, align="center"):
    """Draws text on the screen with specified alignment."""
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
    """
    Displays a modal dialog for the player to choose a color after playing a Wild card.
    This function blocks until a color is chosen or the action is cancelled.
    """
    # Draw a semi-transparent overlay to focus the user's attention.
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    draw_text(screen, "Pilih Warna Baru", TITLE_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))
    
    # Create and draw the color choice buttons.
    button_width, button_height = 120, 60
    colors = ["red", "green", "blue", "yellow"]
    rects = []
    start_x_colors = (SCREEN_WIDTH - (len(colors) * button_width + (len(colors) - 1) * 40)) / 2
    for i, color in enumerate(colors):
        rect = pygame.Rect(start_x_colors + i * (button_width + 40), SCREEN_HEIGHT / 2, button_width, button_height)
        draw_button(screen, color.upper(), rect, COLOR_MAP[color], WHITE)
        rects.append((rect, color))
        
    pygame.display.flip()
    
    # Event loop for the color choice dialog.
    choosing = True
    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, color in rects:
                    if rect.collidepoint(event.pos):
                        return color # Return the chosen color string.

def name_entry_scene(screen):
    """
    Displays the initial screen for the player to enter their name.
    This function runs its own loop until a name is submitted.
    """
    player_name = ""
    input_box = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 - 25, 400, 50)
    join_button = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 70, 200, 60)
    active = False
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    clock = pygame.time.Clock()
    
    while True:
        # Event handling for the name entry screen.
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
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
                        if len(player_name) < 15: # Limit name length.
                            player_name += event.unicode
                            
        # Drawing the name entry UI.
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

# --- Main Game Loop ---
# This is the core of the client application.

def main():
    """Initializes and runs the main game loop."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UNO Multiplayer")
    
    # --- State Initialization ---
    player_id = name_entry_scene(screen)
    if not player_id:
        pygame.quit()
        return
        
    current_game_state = GAME_STATE_PLAYING
    
    # Local game variables that are updated from the server state.
    hand = []
    top_card = "loading..."
    current_turn = "loading..."
    winner = None
    is_my_turn = False
    status_message = f"Welcome, {player_id}!"
    player_statuses = {}
    
    # Define UI element rectangles.
    draw_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2, 180, 50)
    uno_button_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 70, 180, 50)
    callout_buttons = []
    hand_card_rects = []
    left_arrow_rect = pygame.Rect(10, SCREEN_HEIGHT - 170 + 40, 40, 40)
    right_arrow_rect = pygame.Rect(SCREEN_WIDTH - 50, SCREEN_HEIGHT - 170 + 40, 40, 40)
    
    # Timing and control variables.
    last_update_time, UPDATE_INTERVAL = 0, 750 # ms
    clock, running, scroll_x = pygame.time.Clock(), True, 0

    def update_local_state(new_state):
        """A helper function to update all local game variables from a server response."""
        nonlocal hand, top_card, current_turn, winner, is_my_turn, status_message, player_statuses, current_game_state, scroll_x
        if new_state and new_state.get("status") == "OK":
            hand = new_state.get("hand", [])
            top_card = new_state.get("top_card", "Error")
            current_turn = new_state.get("current_turn", "Error")
            player_statuses = new_state.get("player_statuses", {})
            is_my_turn = new_state.get("your_turn", False)
            
            # Update status message if server sent one.
            server_msg = new_state.get("last_action_message")
            if server_msg:
                status_message = server_msg
                
            # Check for a winner to change the game state.
            new_winner = new_state.get("winner")
            if new_winner and not winner:
                winner = new_winner
                current_game_state = GAME_STATE_GAME_OVER
            # Handle game reset on the server.
            elif not new_winner and winner:
                winner = None
                current_game_state = GAME_STATE_PLAYING
                scroll_x = 0

        elif new_state and new_state.get("status") == "ERROR":
            status_message = new_state.get("message", "Unknown error from server.")

    # Join the game and get the initial state.
    initial_state = send_command(f"join {player_id}")
    update_local_state(initial_state)

    # --- Main Application Loop ---
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEWHEEL:
                scroll_x -= event.y * 40 # Allow scrolling the hand with the mouse wheel.

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Helper to reduce code duplication for sending commands.
                def _send_and_update_helper(command):
                    response = send_command(command)
                    update_local_state(response)
                    nonlocal last_update_time
                    last_update_time = pygame.time.get_ticks()

                if current_game_state == GAME_STATE_PLAYING:
                    # Handle clicks on hand scroll arrows.
                    if left_arrow_rect.collidepoint(mouse_pos): scroll_x -= 60
                    elif right_arrow_rect.collidepoint(mouse_pos): scroll_x += 60

                    # Handle clicks on player action buttons.
                    if uno_button_rect.collidepoint(mouse_pos):
                        _send_and_update_helper(f"uno {player_id}")

                    for rect, target_id in callout_buttons:
                        if rect.collidepoint(mouse_pos):
                            _send_and_update_helper(f"callout {player_id} {target_id}")
                            break
                    
                    # Handle actions that are only available on the player's turn.
                    if is_my_turn:
                        # Playing a card from hand.
                        for i, rect in enumerate(hand_card_rects):
                            if rect.collidepoint(mouse_pos):
                                selected_card = hand[i]
                                # If a Wild card is played, ask for a color choice first.
                                if "wild" in selected_card.lower() or "+4" in selected_card:
                                    chosen_color = ask_color_choice(screen)
                                    if chosen_color:
                                        _send_and_update_helper(f"play {player_id} {i} {chosen_color}")
                                    else:
                                        status_message = "Color selection was cancelled."
                                else:
                                    _send_and_update_helper(f"play {player_id} {i}")
                                break
                        
                        # Drawing a card.
                        if draw_button_rect.collidepoint(mouse_pos):
                            _send_and_update_helper(f"draw {player_id}")
                
                elif current_game_state == GAME_STATE_GAME_OVER:
                    # On the game over screen, only the quit button is active.
                    quit_rect = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 130, 200, 60)
                    if quit_rect.collidepoint(mouse_pos):
                        running = False

        # --- Periodic State Update ---
        # Fetch the latest game state from the server periodically.
        current_time = pygame.time.get_ticks()
        if (current_time - last_update_time > UPDATE_INTERVAL):
            last_update_time = current_time
            response = send_command(f"get_state {player_id}")
            update_local_state(response)

        # --- Drawing Logic ---
        screen.fill(BACKGROUND_COLOR)
        
        if current_game_state == GAME_STATE_PLAYING:
            # Clear lists that are rebuilt every frame.
            hand_card_rects.clear()
            callout_buttons.clear()

            # Calculate hand scrolling parameters.
            total_hand_width = len(hand) * (CARD_WIDTH + CARD_MARGIN) - CARD_MARGIN
            hand_area_margin = 70
            visible_width = SCREEN_WIDTH - (2 * hand_area_margin)
            
            # Clamp scroll value to valid range.
            if total_hand_width > visible_width:
                hand_render_start_x = hand_area_margin
                max_scroll = max(0, total_hand_width - visible_width)
                scroll_x = max(0, min(scroll_x, max_scroll))
            else:
                hand_render_start_x = (SCREEN_WIDTH - total_hand_width) / 2
                scroll_x = 0

            # Create rectangles for cards in hand for click detection.
            for i in range(len(hand)):
                card_pos_x = hand_render_start_x + i * (CARD_WIDTH + CARD_MARGIN) - scroll_x
                rect = pygame.Rect(card_pos_x, SCREEN_HEIGHT - 170, CARD_WIDTH, CARD_HEIGHT)
                hand_card_rects.append(rect)

            # Draw the main game elements.
            draw_text(screen, "Top Card", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, 50))
            if top_card != "loading...":
                draw_card(screen, SCREEN_WIDTH / 2 - CARD_WIDTH / 2, 80, top_card)
            
            turn_text = f"Turn: {current_turn}"
            turn_color = YELLOW if is_my_turn else WHITE
            draw_text(screen, turn_text, INPUT_FONT, turn_color, (SCREEN_WIDTH / 2, 250))
            if is_my_turn:
                draw_text(screen, "YOUR TURN!", INPUT_FONT, YELLOW, (SCREEN_WIDTH / 2, 290))
            
            draw_text(screen, status_message, MSG_FONT, GRAY, (SCREEN_WIDTH / 2, 350))

            # Draw the player's hand.
            draw_text(screen, "Your Hand", INFO_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 200))
            for i, card_str in enumerate(hand):
                rect = hand_card_rects[i]
                # Only draw cards that are actually visible on screen.
                if rect.right > 0 and rect.left < SCREEN_WIDTH:
                    is_hovered = is_my_turn and rect.collidepoint(mouse_pos)
                    draw_card(screen, rect.x, rect.y, card_str, selected=is_hovered)

            # Draw action buttons.
            draw_button(screen, "Draw Card", draw_button_rect, BLUE, WHITE, font=INFO_FONT)
            if total_hand_width > visible_width:
                draw_button(screen, "<", left_arrow_rect, GRAY, WHITE, font=INPUT_FONT)
                draw_button(screen, ">", right_arrow_rect, GRAY, WHITE, font=INPUT_FONT)
            
            # Draw the player's own "UNO!" button.
            my_status = player_statuses.get(player_id, {})
            if my_status.get("count") == 1 and not my_status.get("safe"):
                draw_button(screen, "UNO!", uno_button_rect, RED, WHITE)
            else:
                draw_button(screen, "UNO!", uno_button_rect, GRAY, (100, 100, 100))

            # Draw opponent information.
            draw_text(screen, "Other Players:", INFO_FONT, WHITE, (SCREEN_WIDTH - 10, 20), align="topright")
            opponent_y = 50
            if player_statuses:
                for pid, p_status in player_statuses.items():
                    if pid != player_id:
                        count = p_status.get("count", "?")
                        text = f"{pid}: {count} cards"
                        draw_text(screen, text, MSG_FONT, WHITE, (SCREEN_WIDTH - 10, opponent_y), align="topright")
                        
                        # Draw a callout button if an opponent is on UNO but hasn't declared it.
                        if p_status.get("on_uno") and not p_status.get("safe"):
                            text_width = MSG_FONT.size(text)[0]
                            callout_rect = pygame.Rect(SCREEN_WIDTH - 10 - text_width - 90, opponent_y - 3, 80, 28)
                            draw_button(screen, "Call Out!", callout_rect, RED, WHITE, font=MSG_FONT)
                            callout_buttons.append((callout_rect, pid))
                        
                        opponent_y += 25
        
        elif current_game_state == GAME_STATE_GAME_OVER:
            # Draw the Game Over screen.
            is_this_player_winner = (player_id == winner)
            if is_this_player_winner:
                screen.fill((100, 200, 100)) # Light Green for winner
                draw_text(screen, "CONGRATULATIONS!", TITLE_FONT, YELLOW, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))
                draw_text(screen, "YOU ARE THE WINNER!", INPUT_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20))
            else:
                screen.fill((150, 100, 100)) # Muted Red for loser
                draw_text(screen, "GAME OVER!", TITLE_FONT, BLACK, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))
                winner_text = f"The winner is {winner}." if winner else "The winner is unknown."
                draw_text(screen, winner_text, INPUT_FONT, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20))
            
            # Draw the quit button.
            quit_rect = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 130, 200, 60)
            draw_button(screen, "Quit", quit_rect, RED, WHITE)
            
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()