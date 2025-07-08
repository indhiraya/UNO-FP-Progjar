# logic.py
import random

class Game:
    def __init__(self):
        self.players = {}
        self.turn_order = []
        self.current_turn_index = 0
        self.direction = 1
        self.deck = self._create_deck()
        self.discard_pile = []
        self.winner = None
        self.last_action_message = ""
        self.players_on_uno = set()
        self.safe_from_call_out = set()
        self._start_game_setup()

    def _create_deck(self):
        colors = ["red", "green", "blue", "yellow"]
        values = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "Draw Two"]
        special = ["Wild", "Wild Draw Four"]
        deck = [f"{color} {value}" for color in colors for value in values]
        deck += [f"{color} {v}" for color in colors for v in values if v != '0']
        deck += [f"black {s}" for s in special for _ in range(4)]
        random.shuffle(deck)
        return deck

    def _draw_card_from_deck(self):
        if not self.deck:
            if len(self.discard_pile) > 1:
                self.deck = self.discard_pile[:-1]
                random.shuffle(self.deck)
                self.discard_pile = self.discard_pile[-1:]
            else:
                return "empty_deck"
        return self.deck.pop()

    def _start_game_setup(self):
        first_card = self._draw_card_from_deck()
        while "black" in first_card or any(action in first_card for action in ["Skip", "Reverse", "Draw"]):
            self.deck.append(first_card)
            random.shuffle(self.deck)
            first_card = self._draw_card_from_deck()
        self.discard_pile.append(first_card)

    def add_player(self, player_id):
        if player_id not in self.players:
            hand = [self._draw_card_from_deck() for _ in range(7)]
            self.players[player_id] = {"hand": hand, "uno_declared": False}
            self.turn_order.append(player_id)
            self.last_action_message = f"{player_id} telah bergabung."

    def has_player(self, player_id):
        return player_id in self.players

    def _get_current_player_id(self):
        return self.turn_order[self.current_turn_index] if self.turn_order else None

    def _get_player_statuses(self):
        statuses = {}
        for pid, data in self.players.items():
            is_on_uno_vulnerable = pid in self.players_on_uno and not self.players[pid].get("uno_declared", False)
            statuses[pid] = {"count": len(data["hand"]), "on_uno": is_on_uno_vulnerable}
        return statuses

    def get_full_game_state(self, player_id):
        if not self.has_player(player_id):
            return {"status": "ERROR", "message": "Player not found"}
        return {
            "status": "OK",
            "hand": self.players[player_id]["hand"],
            "top_card": self.discard_pile[-1] if self.discard_pile else "",
            "your_turn": self._get_current_player_id() == player_id,
            "current_turn": self._get_current_player_id(),
            "winner": self.winner,
            "last_action_message": self.last_action_message,
            "player_statuses": self._get_player_statuses()
        }

    def _update_player_uno_status(self, player_id):
        hand_size = len(self.players[player_id]["hand"])
        if hand_size == 1:
            self.players_on_uno.add(player_id)
        else:
            self.players_on_uno.discard(player_id)

    def declare_uno(self, player_id):
        if len(self.players[player_id]["hand"]) == 1:
            self.players[player_id]["uno_declared"] = True
            self.last_action_message = f"{player_id} menyatakan UNO!"
            return {"status": "OK"}
        else:
            self.players[player_id]["hand"].append(self._draw_card_from_deck())
            self.last_action_message = f"{player_id} salah menyatakan UNO, +1 kartu!"
            return {"status": "ERROR", "message": "Pinalti salah UNO!"}

    def call_out_player(self, caller_id, target_id):
        target_data = self.players.get(target_id)
        if target_data and len(target_data["hand"]) == 1 and not target_data["uno_declared"]:
            target_data["hand"] += [self._draw_card_from_deck() for _ in range(2)]
            self.last_action_message = f"{caller_id} menantang {target_id}! {target_id} menarik 2 kartu."
            self._update_player_uno_status(target_id)
        else:
            self.players[caller_id]["hand"].append(self._draw_card_from_deck())
            self.last_action_message = f"Tantangan {caller_id} pada {target_id} gagal, +1 kartu!"
            self._update_player_uno_status(caller_id)
        return {"status": "OK"}

    def _advance_turn(self):
        # Reset status uno_declared untuk pemain yang baru saja menyelesaikan gilirannya
        prev_player_id = self._get_current_player_id()
        if prev_player_id:
            self.players[prev_player_id]["uno_declared"] = False

        if not self.turn_order: return
        self.current_turn_index = (self.current_turn_index + self.direction) % len(self.turn_order)

    def _apply_card_effects(self, played_val, new_color=None):
        skip_turn = False
        if played_val == "Skip":
            skip_turn = True
        elif played_val == "Reverse":
            if len(self.players) == 2: skip_turn = True
            else: self.direction *= -1
        elif played_val == "Draw Two":
            next_player_idx = (self.current_turn_index + self.direction) % len(self.turn_order)
            next_player = self.turn_order[next_player_idx]
            self.players[next_player]["hand"] += [self._draw_card_from_deck() for _ in range(2)]
            self._update_player_uno_status(next_player)
            skip_turn = True
        elif played_val == "Wild Draw Four":
            next_player_idx = (self.current_turn_index + self.direction) % len(self.turn_order)
            next_player = self.turn_order[next_player_idx]
            self.players[next_player]["hand"] += [self._draw_card_from_deck() for _ in range(4)]
            self._update_player_uno_status(next_player)
            skip_turn = True
        
        self._advance_turn()
        if skip_turn:
            self._advance_turn()

    def play_card(self, player_id, index, new_color=None):
        if self.winner or self._get_current_player_id() != player_id: return {"status": "ERROR", "message":"Bukan giliranmu"}
        hand = self.players[player_id]["hand"]
        if index >= len(hand): return {"status": "ERROR", "message":"Index kartu tidak valid"}
        
        played_str, top_str = hand[index], self.discard_pile[-1]
        played_color, played_val = played_str.split(" ", 1)
        top_color, top_val = top_str.split(" ", 1)
        is_match = (played_color == "black") or (played_color == top_color) or (played_val == top_val)

        if not is_match: return {"status": "ERROR", "message":"Kartu tidak cocok"}
        
        del hand[index]
        card_to_discard = played_str
        if played_color == "black":
            if not new_color: return {"status": "ERROR", "message":"Harus pilih warna"}
            card_to_discard = f"{new_color} {played_val}"

        self.discard_pile.append(card_to_discard)
        self.last_action_message = f"{player_id} memainkan {played_str}."
        
        self._update_player_uno_status(player_id)

        if not hand:
            self.winner = player_id
            self.last_action_message = f"🎉 {player_id} MENANG! 🎉"
        else:
            self._apply_card_effects(played_val, new_color)

        return {"status": "OK"}

    def draw_card(self, player_id):
        if self.winner or self._get_current_player_id() != player_id: return {"status": "ERROR", "message":"Bukan giliranmu"}
        card = self._draw_card_from_deck()
        if card:
            self.players[player_id]["hand"].append(card)
            self.last_action_message = f"{player_id} menarik kartu."
            self._update_player_uno_status(player_id)
        self._advance_turn()
        return {"status": "OK"}