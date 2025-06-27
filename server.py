# server.py
import socket
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from game_logic import Game

# --- Server Setup ---
# Configure logging and initialize the shared game state and its lock.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
game = Game()
game_lock = threading.Lock() # Ensures thread-safe access to the game state.

def process_command(command_str):
    """
    Parses a command string from a client and interacts with the game logic.
    This function is the central dispatcher for all game actions.
    """
    try:
        parts = command_str.strip().split()
        cmd = parts[0].lower()
        player_id = parts[1] if len(parts) > 1 else None

        # The game_lock ensures that only one command is processed at a time,
        # preventing race conditions and inconsistent states.
        with game_lock:
            # --- Command Dispatcher ---
            if cmd == "join":
                game.add_player(player_id)
            elif cmd == "play":
                card_index = int(parts[2])
                new_color = parts[3] if len(parts) > 3 else None
                action_result = game.play_card(player_id, card_index, new_color)
                # If the action returned an error, send it back immediately.
                if action_result and action_result.get("status") == "ERROR":
                    return json.dumps(action_result)
            elif cmd == "draw":
                action_result = game.draw_card(player_id)
                if action_result and action_result.get("status") == "ERROR":
                    return json.dumps(action_result)
            elif cmd == "uno":
                game.declare_uno(player_id)
            elif cmd == "callout":
                target_id = parts[2]
                game.call_out_player(player_id, target_id)
            elif cmd == "get_state":
                pass # No action needed, will just return the state below.
            else:
                return json.dumps({"status": "ERROR", "message": "Unknown command"})

            # After any valid action, return the complete, updated game state.
            return json.dumps(game.get_full_game_state(player_id))

    except (ValueError, IndexError) as e:
        logging.error(f"Command parsing error for '{command_str}': {e}", exc_info=True)
        return json.dumps({"status": "ERROR", "message": f"Invalid command format: {e}."})
    except Exception as e:
        logging.error(f"Error processing command '{command_str}': {e}", exc_info=True)
        return json.dumps({"status": "ERROR", "message": f"Internal server error: {e}"})

def handle_client(connection, address):
    """
    Manages a single client connection: receives a command, processes it,
    sends a response, and closes the connection.
    """
    try:
        data = connection.recv(4096)
        if data:
            command = data.decode('utf-8').strip()
            if not command: return
            
            logging.info(f"<- Received from {address}: {command}")
            response = process_command(command)
            
            # Append a terminator to the response.
            response += "\r\n\r\n"
            connection.sendall(response.encode('utf-8'))
    except ConnectionResetError:
        logging.warning(f"Connection reset by {address}.")
    except Exception as e:
        logging.warning(f"Error handling client {address}: {e}")
    finally:
        connection.close()

def run_server(host='0.0.0.0', port=8889, max_workers=20):
    """
    Sets up the listening socket and uses a ThreadPoolExecutor to handle
    incoming client connections concurrently.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.bind((host, port))
        my_socket.listen(5)
        print(f"UNO Server with ThreadPool is running at {host}:{port}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                try:
                    conn, addr = my_socket.accept()
                    # Submit each new client connection to the thread pool.
                    executor.submit(handle_client, conn, addr)
                except KeyboardInterrupt:
                    print("\nServer is shutting down.")
                    break
                except Exception as e:
                    logging.error(f"Server main loop error: {e}")

if __name__ == "__main__":
    run_server()