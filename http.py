# http.py

import json
import logging

class HttpServer:
    """
    Acts as a dedicated request handler for the UNO game. It processes
    command strings from clients and interacts with the shared game state.
    """
    def __init__(self, game_instance, lock):
        """
        Initializes the handler with a direct reference to the shared
        game instance and the thread lock.
        """
        self.game = game_instance
        self.lock = lock

    def process_command(self, command_str):
        """
        Parses a command from a client, executes the corresponding game action,
        and returns the updated game state as a JSON string.
        """
        try:
            parts = command_str.strip().split()
            cmd = parts[0].lower()
            player_id = parts[1] if len(parts) > 1 else None

            # The lock ensures that only one thread can modify the game state at a time,
            # preventing race conditions and data corruption.
            with self.lock:
                # --- Game Command Dispatcher ---
                if cmd == "join":
                    self.game.add_player(player_id)
                elif cmd == "play":
                    card_index = int(parts[2])
                    new_color = parts[3] if len(parts) > 3 else None
                    action_result = self.game.play_card(player_id, card_index, new_color)
                    # If the action is invalid, return the error message immediately.
                    if action_result and action_result.get("status") == "ERROR":
                        return json.dumps(action_result)
                elif cmd == "draw":
                    action_result = self.game.draw_card(player_id)
                    if action_result and action_result.get("status") == "ERROR":
                        return json.dumps(action_result)
                elif cmd == "uno":
                    self.game.declare_uno(player_id)
                elif cmd == "callout":
                    target_id = parts[2]
                    self.game.call_out_player(player_id, target_id)
                elif cmd == "get_state":
                    # No action needed; the current state will be sent automatically.
                    pass
                else:
                    return json.dumps({"status": "ERROR", "message": "Unknown command"})

                # After every successful action, return the latest game state to the client.
                return json.dumps(self.game.get_full_game_state(player_id))

        except (ValueError, IndexError) as e:
            logging.error(f"Command parsing error: {e}")
            return json.dumps({"status": "ERROR", "message": f"Invalid command format: {e}."})
        except Exception as e:
            logging.error(f"Internal server error: {e}", exc_info=True)
            return json.dumps({"status": "ERROR", "message": f"An internal server error occurred: {e}"})