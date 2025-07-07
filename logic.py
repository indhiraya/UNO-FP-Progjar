import random

class Game:
    def __init__(self):
        self.players = {}
        self.turn_order = []
        self.current_turn_index = 0
        self.deck = self.create_deck()
        self.discard_pile = []
        self.started = False
        self.winner = None
        self.last_action_message = ""

    def create_deck(self):
        colors = ["red", "green", "blue", "yellow"]
        values = [str(n) for n in range(0, 10)] + ["Skip", "Reverse", "+2"]
        special = ["Wild", "+4"]
        deck = [f"{color} {value}" for color in colors for value in values for _ in range(2)]
        deck += [f"black {s}" for s in special for _ in range(4)]
        random.shuffle(deck)
        return deck

    def draw_card_from_deck(self):
        if not self.deck:
            if len(self.discard_pile) > 1:
                self.deck = self.discard_pile[:-1]
                random.shuffle(self.deck)
                self.discard_pile = self.discard_pile[-1:]
            else:
                return None  
        return self.deck.pop() if self.deck else None

    def add_player(self, player_id):
        if player_id not in self.players:
            hand = [self.draw_card_from_deck() for _ in range(7)]
            self.players[player_id] = {"hand": hand, "uno_declared": False}
            self.turn_order.append(player_id)
            if not self.discard_pile:
                first_card = self.draw_card_from_deck()
                attempts = 0
                while first_card.startswith("black") and attempts < 10:
                    self.deck.insert(0, first_card)
                    first_card = self.draw_card_from_deck()
                    attempts += 1
                self.discard_pile.append(first_card)
            if len(self.turn_order) >= 2 and self.current_turn_index == 0 and not self.started:
                self.started = True
                self.current_turn_index = 0
                self.last_action_message = f"Game started! Turn: {self.get_current_player()}"

    def has_player(self, player_id):
        return player_id in self.players

    def get_current_player(self):
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn_index % len(self.turn_order)]

    def get_full_game_state(self, player_id):
        if player_id not in self.players:
            return {"status": "ERROR", "message": "Player not found"}
        return {
            "status": "OK",
            "hand": self.players[player_id]["hand"],
            "top_card": self.discard_pile[-1] if self.discard_pile else "",
            "your_turn": self.get_current_player() == player_id,
            "current_turn": self.get_current_player(),
            "winner": self.winner,
            "last_action_message": self.last_action_message,
            "can_declare_uno": len(self.players[player_id]["hand"]) == 1 and self.get_current_player() == player_id,
            "can_press_uno": any(len(data["hand"]) == 1 for data in self.players.values()),
            "others": {
                pid: len(data["hand"])
                for pid, data in self.players.items()
                if pid != player_id
            }
        }
    
    def can_play_wild_draw_four(self, player_id, index):
        hand = self.players[player_id]["hand"]
        top = self.discard_pile[-1]
        top_color, top_val = top.split(" ", 1)
        for i, card in enumerate(hand):
            if i == index:
                continue
            color, val = card.split(" ", 1)
            if color == top_color or val == top_val:
                return False
        return True

    def play_card(self, player_id, index, new_color=None):
        if self.get_current_player() != player_id:
            return {"status": "ERROR", "message": "Not your turn"}

        hand = self.players[player_id]["hand"]
        if index >= len(hand):
            return {"status": "ERROR", "message": "Invalid card index"}

        played = hand[index]
        top = self.discard_pile[-1]
        played_color, played_val = played.split(" ", 1)
        top_color, top_val = top.split(" ", 1)

        if played_color == "black":
            if not new_color or new_color not in ["red", "yellow", "green", "blue"]:
                return {"status": "ERROR", "message": "You must choose a color for Wild"}

            if played_val == "+4":
                if not self.can_play_wild_draw_four(player_id, index):
                    return {
                        "status": "ERROR",
                        "message": "You cannot play Wild Draw Four if you have a matching color or value"
                    }
            played = f"{new_color} {played_val}"
            original_played = played 
        elif played_color != top_color and played_val != top_val:
            return {"status": "ERROR", "message": "Card does not match color or value"}
        else:
            original_played = played

        self.discard_pile.append(played)
        del hand[index]

        skip_extra = False
        if played_val == "Skip":
            skip_extra = True
        elif played_val == "Reverse":
            if len(self.turn_order) == 2:
                skip_extra = True  
            else:
                self.turn_order.reverse()
                self.current_turn_index = len(self.turn_order) - self.current_turn_index - 1
        elif played_val == "+2":
            next_player_index = (self.current_turn_index + 1) % len(self.turn_order)
            next_player = self.turn_order[next_player_index]
            new_cards = [self.draw_card_from_deck() for _ in range(2)]
            self.players[next_player]["hand"] += [card for card in new_cards if card]
            skip_extra = True
        elif played_val == "+4":
            next_player_index = (self.current_turn_index + 1) % len(self.turn_order)
            next_player = self.turn_order[next_player_index]
            self.players[next_player]["hand"] += [self.draw_card_from_deck() for _ in range(4)]
            skip_extra = True
        
        if not hand:
            if not self.players[player_id]["uno_declared"]:
                self.players[player_id]["hand"] += [self.draw_card_from_deck() for _ in range(2)]
                self.last_action_message = f"{player_id} did not declare UNO! +2 cards"
            else:
                self.winner = player_id

        self.last_action_message = f"{player_id} played {original_played}"

        self.advance_turn()
        if skip_extra:
            self.advance_turn()

        return {"status": "OK"}

    def draw_card(self, player_id):
        if self.get_current_player() != player_id:
            return {"status": "ERROR", "message": "Not your turn"}
        card = self.draw_card_from_deck()
        if card:
            self.players[player_id]["hand"].append(card)
        self.last_action_message = f"{player_id} drew a card"
        self.advance_turn()
        return {"status": "OK"}
    
    def press_uno_button(self, player_id):
        candidates = [pid for pid, data in self.players.items() if len(data["hand"]) == 1]

        if not candidates:
            return {"status": "ERROR", "message": "No player is eligible for UNO"}

        if player_id in candidates:
            self.players[player_id]["uno_declared"] = True
            self.last_action_message = f"{player_id} declared UNO!"
            return {"status": "OK", "message": "UNO declared!"}
        else:
            target = candidates[0]  
            self.players[target]["hand"] += [self.draw_card_from_deck() for _ in range(2)]
            self.last_action_message = f"{target} failed to declare UNO in time! +2 cards"
            return {"status": "OK", "message": f"{target} did not declare UNO in time! +2 cards"}

    def declare_uno(self, player_id):
        if len(self.players[player_id]["hand"]) == 1:
            self.players[player_id]["uno_declared"] = True
            return {"status": "OK", "message": "UNO declared!"}

    def advance_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        current_player = self.get_current_player()
        for pid in self.players:
            if pid != current_player:
                self.players[pid]["uno_declared"] = False
