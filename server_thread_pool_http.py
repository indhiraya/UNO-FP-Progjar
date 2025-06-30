# server_thread_pool_http.py

import socket
import logging
import threading
import json
from concurrent.futures import ThreadPoolExecutor

# --- Game and Handler Imports ---
from game_logic import Game
from http import HttpServer

# --- Shared State Initialization ---
# The single Game object holds the state for all players.
game_instance = Game()
# The lock is crucial for preventing race conditions when multiple clients
# try to access or modify the game state simultaneously.
game_lock = threading.Lock()

# --- Handler Initialization ---
# The HttpServer is instantiated once and is given access to the shared game
# state and lock. It will be used by all threads to process commands.
request_handler = HttpServer(game_instance, game_lock)

def process_client_connection(connection, address):
    """
    Handles the entire lifecycle of a single client connection. It receives data,
    passes it to the handler, sends the response, and closes the connection.
    """
    try:
        # The client is expected to send one command and then disconnect.
        data = connection.recv(4096)
        if data:
            command_string = data.decode('utf-8').strip()
            logging.info(f"<- Received from {address}: {command_string}")

            # The core processing logic is delegated to the shared request handler.
            response_json = request_handler.process_command(command_string)

            # The response is sent back with a clear terminator.
            response_bytes = (response_json + "\r\n\r\n").encode('utf-8')
            connection.sendall(response_bytes)
    except OSError as e:
        logging.warning(f"Socket error with {address}: {e}")
    except Exception as e:
        logging.error(f"Error processing client {address}: {e}", exc_info=True)
    finally:
        # Ensure the connection is always closed.
        connection.close()

def run_server():
    """
    Initializes and runs the main server loop, accepting connections and
    assigning them to worker threads from a thread pool.
    """
    # Standard socket setup.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8889))
    server_socket.listen(5)
    logging.info("UNO Game Server with ThreadPool is running at port 8889")

    # The ThreadPoolExecutor manages a pool of worker threads.
    with ThreadPoolExecutor(max_workers=20) as executor:
        while True:
            try:
                # Accept a new client connection.
                connection, client_address = server_socket.accept()
                # Submit the connection to the thread pool for processing. This call
                # is non-blocking and immediately allows the server to listen for new connections.
                executor.submit(process_client_connection, connection, client_address)
            except KeyboardInterrupt:
                logging.info("Server is shutting down.")
                break
            except Exception as e:
                logging.error(f"Server main loop error: {e}", exc_info=True)

if __name__ == "__main__":
    # Configure logging to show timestamps and messages.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_server()