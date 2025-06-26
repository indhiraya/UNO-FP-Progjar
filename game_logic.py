# game_logic.py
import random

COLORS = ["red", "green", "blue", "yellow"]
VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def matches(self, other_card):
        if self.color == "black": return True
        return self.color == other_card.color or self.value == other_card.value

    def __str__(self):
        color_str = self.color if self.color != "black" else "wild"
        return f"{color_str} {self.value}"

class Deck:
    def __init__(self):
        self.cards = []
        for color in COLORS:
            for value in VALUES:
                self.cards.append(Card(color, value))
                if value != "0": self.cards.append(Card(color, value))
        for _ in range(4):
            self.cards.append(Card("black", "wild"))
            self.cards.append(Card("black", "+4"))
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards: self.__init__()
        return self.cards.pop()

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.hand = []

    def draw_cards(self, deck, count=1):
        for _ in range(count):
            card = deck.draw()
            if card: self.hand.append(card)

    def play_card(self, card_index, top_card):
        if card_index >= len(self.hand): return None
        card = self.hand[card_index]
        if card.matches(top_card): return self.hand.pop(card_index)
        return None

    def get_hand_str(self):
        return [str(c) for c in self.hand]

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = {}
        self.turn_order = []
        self.current_turn_index = 0
        self.direction = 1
        self.winner = None
        self.top_card = self.deck.draw()
        while self.top_card.color == "black" or self.top_card.value in ["+2", "skip", "reverse"]:
            self.top_card = self.deck.draw()

        self.players_on_uno = set()
        self.safe_from_call_out = set()
        self.last_action_message = ""

    def _get_current_player_id(self):
        return self.turn_order[self.current_turn_index] if self.turn_order else None

    def _get_player_statuses(self):
        return {pid: {"count": len(p.hand), "on_uno": pid in self.players_on_uno and pid not in self.safe_from_call_out} for pid, p in self.players.items()}

    def get_full_game_state(self, for_player_id):
        player = self.players.get(for_player_id)
        if not player: return {"status": "ERROR", "message": "Player not found"}
        
        return {
            "status": "OK",
            "hand": player.get_hand_str(),
            "your_turn": for_player_id == self._get_current_player_id(),
            "top_card": str(self.top_card),
            "current_turn": self._get_current_player_id(),
            "winner": self.winner,
            "player_statuses": self._get_player_statuses(),
            "last_action_message": self.last_action_message
        }

    def add_player(self, player_id):
        if player_id not in self.players:
            player = Player(player_id)
            player.draw_cards(self.deck, 7)
            self.players[player_id] = player
            self.turn_order.append(player_id)
            self.last_action_message = f"{player_id} telah bergabung."

    def _update_player_uno_status(self, player_id):
        player_hand_size = len(self.players[player_id].hand)
        if player_hand_size == 1:
            if player_id not in self.players_on_uno:
                self.players_on_uno.add(player_id)
                self.safe_from_call_out.discard(player_id) # Player harus declare ulang
        elif player_id in self.players_on_uno:
            self.players_on_uno.remove(player_id)
            self.safe_from_call_out.discard(player_id)

    def declare_uno(self, player_id):
        if player_id in self.players_on_uno:
            self.safe_from_call_out.add(player_id)
            self.last_action_message = f"{player_id} menyatakan UNO!"
        else:
            # Pinalti untuk salah pencet UNO
            self.players[player_id].draw_cards(self.deck, 1)
            self.last_action_message = f"{player_id} salah menyatakan UNO dan menarik 1 kartu."
        self._update_player_uno_status(player_id)

    def call_out_player(self, caller_id, target_id):
        if target_id in self.players_on_uno and target_id not in self.safe_from_call_out:
            self.players[target_id].draw_cards(self.deck, 2)
            self.last_action_message = f"{caller_id} menantang {target_id}! {target_id} menarik 2 kartu."
            self._update_player_uno_status(target_id)
        else:
            self.last_action_message = f"Tantangan pada {target_id} gagal."

    def _move_to_next_player(self, skip=1):
        num_players = len(self.turn_order)
        if num_players == 0: return
        self.current_turn_index = (self.current_turn_index + self.direction * skip) % num_players
        # Reset pesan setelah giliran berpindah
        self.last_action_message = ""


    def _process_card_effects(self, played_card, new_color=None):
        value = played_card.value
        
        if value == "skip": self._move_to_next_player(skip=2)
        elif value == "reverse":
            self.direction *= -1
            self._move_to_next_player()
        elif value == "+2":
            next_player_idx = (self.current_turn_index + self.direction) % len(self.turn_order)
            next_player_id = self.turn_order[next_player_idx]
            self.players[next_player_id].draw_cards(self.deck, 2)
            self._update_player_uno_status(next_player_id)
            self._move_to_next_player()
        elif value == "+4":
            played_card.color = new_color
            next_player_idx = (self.current_turn_index + self.direction) % len(self.turn_order)
            next_player_id = self.turn_order[next_player_idx]
            self.players[next_player_id].draw_cards(self.deck, 4)
            self._update_player_uno_status(next_player_id)
            self._move_to_next_player(skip=2)
        elif value == "wild":
            played_card.color = new_color
            self._move_to_next_player()
        else:
            self._move_to_next_player()

    def play_card(self, player_id, card_index, new_color=None):
        if player_id != self._get_current_player_id(): return
        player = self.players[player_id]
        played_card = player.play_card(card_index, self.top_card)
        if not played_card: return
        
        self.top_card = played_card
        self.last_action_message = f"{player_id} memainkan {played_card.color} {played_card.value}."

        if len(player.hand) == 0:
            self.winner = player_id
            self.last_action_message = f"🎉 {player_id} MENANG! 🎉"
            return
        
        self._update_player_uno_status(player_id)
        self._process_card_effects(played_card, new_color)

    def draw_card(self, player_id):
        if player_id != self._get_current_player_id(): return
        player = self.players[player_id]
        player.draw_cards(self.deck, 1)
        self.last_action_message = f"{player_id} menarik 1 kartu."
        self._update_player_uno_status(player_id)
        self._move_to_next_player()