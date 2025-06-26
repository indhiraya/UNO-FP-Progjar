# ======== server.py ========
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

        if cmd == "join":
            player_id = parts[1]
            with game_lock:
                game.add_player(player_id)
            return json.dumps({"status": "OK", "message": f"{player_id} joined"})

        elif cmd == "hand":
            player_id = parts[1]
            player = game.get_player(player_id)
            if not player:
                return json.dumps({"status": "ERROR", "message": "Player not found"})
            return json.dumps({
                "status": "OK",
                "hand": player.get_hand(),
                "your_turn": (player_id == game.get_current_player())
            })

        elif cmd == "top_card":
            return json.dumps({
                "status": "OK",
                "top_card": str(game.top_card),
                "current_turn": game.get_current_player()
            })

        elif cmd == "play":
            player_id = parts[1]
            card_index = int(parts[2])
            new_color = parts[3] if len(parts) > 3 else None
            with game_lock:
                result = game.play_card(player_id, card_index, new_color)
            return json.dumps({"status": "OK", "result": result})

        elif cmd == "draw":
            player_id = parts[1]
            with game_lock:
                result = game.draw_or_pass(player_id)
                if result in ["Not your turn", "You have already drawn a card this turn"]:
                    return json.dumps({"status": "ERROR", "message": result})
                else:
                    return json.dumps({"status": "OK", "message": result})
        
        elif cmd == "status":
            with game_lock:
                summary = {
                    pid: len(player.hand)
                    for pid, player in game.players.items()
                }
            return json.dumps({"status": "OK", "players": summary})

        elif cmd == "winner":
            return json.dumps({"status": "OK", "winner": game.winner})


        else:
            return json.dumps({"status": "ERROR", "message": "Unknown command"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

def handle_client(connection, address):
    rcv = ""
    try:
        while True:
            data = connection.recv(32)
            if data:
                d = data.decode()
                rcv += d
                if rcv.endswith('\r\n'):
                    logging.info(f"📥 dari {address}: {rcv.strip()}")
                    hasil = proses(rcv)
                    hasil = hasil + "\r\n\r\n"
                    connection.sendall(hasil.encode())
                    logging.info(f"📤 ke {address}: {hasil.strip()}")
                    break
            else:
                break
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
                conn, addr = my_socket.accept()
                logging.info(f"🔗 Koneksi dari {addr}")
                executor.submit(handle_client, conn, addr)

def main():
    run_server()

if __name__ == "__main__":
    main()
