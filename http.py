import sys
import os.path
import uuid
import json
import random
from glob import glob
from datetime import datetime
from logic import Game

COLORS = ['Red', 'Green', 'Blue', 'Yellow']
NUMBERS = list(range(0, 10))

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.txt': 'text/plain',
            '.html': 'text/html'
        }
        self.game = Game()

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n".format(kode, message))
        resp.append("Date: {}\r\n".format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n".format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n".format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ''.join(resp)
        if (type(messagebody) is not bytes):
            messagebody = messagebody.encode()

        return response_headers.encode() + messagebody

    def proses(self, data):
        header_end = data.find('\r\n\r\n')
        if header_end == -1:
            return self.response(400, 'Bad Request', '', {})

        header_part = data[:header_end]
        body_part = data[header_end+4:].strip()

        requests = header_part.split('\r\n')
        baris = requests[0]
        all_headers = [n for n in requests[1:] if n != '']

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, all_headers)
            elif method == 'POST':
                return self.http_post(object_address, body_part)
            else:
                return self.response(400, 'Bad Request', '', {})
        except IndexError:
            return self.response(400, 'Bad Request', '', {})

    def http_get(self, object_address, headers):
        files = glob('./*')
        thedir = './'
        if object_address == '/':
            return self.response(200, 'OK', 'Ini Adalah web Server percobaan', {})

        if object_address == '/video':
            return self.response(302, 'Found', '', {'location': 'https://youtu.be/katoxpnTf04'})
        if object_address == '/santai':
            return self.response(200, 'OK', 'santai saja', {})

        object_address = object_address[1:]
        if thedir + object_address not in files:
            return self.response(404, 'Not Found', '', {})
        with open(thedir + object_address, 'rb') as fp:
            isi = fp.read()

        fext = os.path.splitext(thedir + object_address)[1]
        content_type = self.types.get(fext, 'application/octet-stream')

        return self.response(200, 'OK', isi, {'Content-type': content_type})

    def http_post(self, object_address, body):
        if object_address == "/uno":
            try:
                command_line = body.strip()
                parts = command_line.split()

                if len(parts) < 2:
                    return self.response(400, 'Bad Request', 'Invalid command format', {})

                command, player_id = parts[0], parts[1]

                if command != "join" and not self.game.has_player(player_id):
                    return self.response(400, 'Bad Request', 'Player not joined yet', {})

                if command == "state":
                    state = self.game.get_full_game_state(player_id)
                    return self.response(200, "OK", json.dumps(state), {'Content-type': 'application/json'})
                
                elif command == "join":
                    player_id = parts[1]
                    already_joined = self.game.has_player(player_id)
                    if not already_joined:
                        self.game.add_player(player_id)
                    return self.response(200, "OK", json.dumps({
                        "status": "OK",
                        "message": f"Player {player_id} {'already joined' if already_joined else 'joined'}",
                        "already_joined": already_joined
                    }), {'Content-type': 'application/json'})

                elif command == "play":
                    if len(parts) < 3:
                        return self.response(400, 'Bad Request', 'Index not specified', {})
                    index = int(parts[2])
                    new_color = parts[3] if len(parts) > 3 else None
                    result = self.game.play_card(player_id, index, new_color)
                    return self.response(200, "OK", json.dumps(result), {'Content-type': 'application/json'})

                elif command == "draw":
                    result = self.game.draw_card(player_id)
                    return self.response(200, "OK", json.dumps(result), {'Content-type': 'application/json'})

                elif command == "declare_uno":
                    result = self.game.declare_uno(player_id)
                    return self.response(200, "OK", json.dumps(result), {'Content-type': 'application/json'})
                
                elif command == "restart":
                    self.game = Game()
                    return self.response(200, "OK", json.dumps({"status": "OK", "message": "Game restarted"}), {'Content-type': 'application/json'})

                elif command == "list_players":
                    players = list(self.game.players.keys())
                    return self.response(200, "OK", json.dumps({"status": "OK", "players": players}), {'Content-type': 'application/json'})

                else:
                    return self.response(400, 'Bad Request', 'Unknown command', {})

            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e), {})
        else:
            return self.response(404, 'Not Found', 'Unknown endpoint', {})

if __name__ == "__main__":
    httpserver = HttpServer()
    print(httpserver.proses('POST /uno HTTP/1.0\r\n\r\njoin player1\r\n\r\n').decode())
