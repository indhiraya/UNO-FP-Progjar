# server.py
from socket import *
import socket
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from game_logic import Game

logging.basicConfig(level=logging.INFO)
game = Game()
game_lock = threading.Lock()

def proses(command_str):
    try:
        parts = command_str.strip().split()
        cmd = parts[0].lower()
        player_id = parts[1] if len(parts) > 1 else None

        with game_lock:
            if cmd == "join":
                game.add_player(player_id)
            elif cmd == "play":
                card_index = int(parts[2])
                new_color = parts[3] if len(parts) > 3 else None
                game.play_card(player_id, card_index, new_color)
            elif cmd == "draw":
                game.draw_card(player_id)
            elif cmd == "uno":
                game.declare_uno(player_id)
            elif cmd == "callout":
                target_id = parts[2]
                game.call_out_player(player_id, target_id)
            
            # Perintah "get_state" untuk polling
            elif cmd == "get_state":
                pass # Cukup lewati dan kirim state terbaru
            
            else:
                return json.dumps({"status": "ERROR", "message": "Unknown command"})

            # Selalu kirim state game lengkap setelah aksi apapun
            return json.dumps(game.get_full_game_state(player_id))

    except Exception as e:
        logging.error(f"Error processing command '{command_str}': {e}", exc_info=True)
        return json.dumps({"status": "ERROR", "message": f"Server error: {e}"})

def handle_client(connection, address):
    try:
        data = connection.recv(4096)
        if data:
            rcv = data.decode('utf-8')
            if not rcv.strip(): return
            logging.info(f"📥 dari {address}: {rcv.strip()}")
            hasil = proses(rcv.strip())
            hasil += "\r\n\r\n"
            connection.sendall(hasil.encode('utf-8'))
    except Exception as e:
        logging.warning(f"⚠️ Error dari {address}: {e}")
    finally:
        connection.close()

def run_server(host='0.0.0.0', port=8889, max_workers=20):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.bind((host, port))
        my_socket.listen(5)
        print(f"✅ Server UNO dengan ThreadPool aktif di {host}:{port}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                try:
                    conn, addr = my_socket.accept()
                    executor.submit(handle_client, conn, addr)
                except KeyboardInterrupt:
                    print("\nServer dimatikan.")
                    break
                except Exception as e:
                    logging.error(f"Server loop error: {e}")

if __name__ == "__main__":
    run_server()