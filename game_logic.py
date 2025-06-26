import random

COLORS = ["red", "green", "blue", "yellow"]
VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2", "+4", "wild"]

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def matches(self, other):
        return (
            self.color == other.color or 
            self.value == other.value or 
            self.value in ["+4", "wild"]
        )

    def __str__(self):
        return f"{self.color} {self.value}"

class Deck:
    def __init__(self):
        self.cards = []
        for color in COLORS:
            for value in VALUES:
                if value == ["+4", "wild"]:
                    continue  # +4 tidak tergantung warna di deck awal
                self.cards.append(Card(color, value))
                self.cards.append(Card(color, value))
        for _ in range(4):  # Tambahkan +4 sebagai wildcard tanpa warna awal
            self.cards.append(Card("black", "+4"))
            self.cards.append(Card("black", "wild"))
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            return None
        return self.cards.pop()

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.hand = []
        self.has_won = False

    def draw_card(self, deck):
        card = deck.draw()
        if card:
            self.hand.append(card)

    def play_card(self, card_index, top_card):
        if card_index >= len(self.hand):
            return None
        card = self.hand[card_index]
        if card.matches(top_card):
            return self.hand.pop(card_index)
        return None

    def get_hand(self):
        return [str(c) for c in self.hand]

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = {}
        self.turn_order = []
        self.current_turn = 0
        self.top_card = self.deck.draw()
        self.drawn_this_turn = set()
        self.direction = 1  # 1 = searah, -1 = berbalik
        self.force_draw_map = {}
        self.winner = None

    def add_player(self, player_id):
        if player_id not in self.players:
            player = Player(player_id)
            for _ in range(7):
                player.draw_card(self.deck)
            self.players[player_id] = player
            self.turn_order.append(player_id)

    def get_player(self, player_id):
        player = self.players.get(player_id)
        if player and player_id in self.force_draw_map:
            count = self.force_draw_map.pop(player_id)
            for _ in range(count):
                player.draw_card(self.deck)
        return player

    def get_current_player(self):
        return self.turn_order[self.current_turn]

    def next_turn(self, skip=1):
        for _ in range(len(self.turn_order)):
            self.current_turn = (self.current_turn + self.direction * skip) % len(self.turn_order)
            current_player_id = self.get_current_player()
            if not self.players[current_player_id].has_won:
                break
        self.drawn_this_turn.clear()

    def play_card(self, player_id, card_index, new_color=None):
        if self.players[player_id].has_won:
            return "You have already won and can't play anymore"

        if player_id != self.get_current_player():
            return "Not your turn"

        player = self.get_player(player_id)
        card = player.play_card(card_index, self.top_card)

        if not card:
            return "Invalid card"

        self.top_card = card

        if len(player.hand) == 0:
            player.has_won = True  # ✅ tandai pemain menang
            result = f"🎉 {player_id} wins the game!"
            self.next_turn()
            return result

        if card.value == "+2":
            next_index = (self.current_turn + self.direction) % len(self.turn_order)
            next_player_id = self.turn_order[next_index]
            self.force_draw_map[next_player_id] = self.force_draw_map.get(next_player_id, 0) + 2
            self.next_turn(skip=2)
            return f"Played {card}. {next_player_id} will draw 2 cards and be skipped."

        elif card.value == "+4":
            if not new_color or new_color not in COLORS:
                return "You must choose a valid color for +4"
            card.color = new_color
            self.top_card = card
            next_index = (self.current_turn + self.direction) % len(self.turn_order)
            next_player_id = self.turn_order[next_index]
            self.force_draw_map[next_player_id] = self.force_draw_map.get(next_player_id, 0) + 4
            self.next_turn(skip=2)
            return f"Played {card}. Color changed to {new_color}. {next_player_id} will draw 4 cards and be skipped."

        elif card.value == "wild":
            if not new_color or new_color not in COLORS:
                return "You must choose a valid color for wild"
            card.color = new_color
            self.top_card = card
            self.next_turn()
            return f"Played {card}. Color changed to {new_color}."

        elif card.value == "skip":
            skipped_index = (self.current_turn + self.direction) % len(self.turn_order)
            skipped_player_id = self.turn_order[skipped_index]
            self.next_turn(skip=2)
            return f"Played {card}. {skipped_player_id} is skipped."

        elif card.value == "reverse":
            self.direction *= -1
            if len(self.turn_order) == 2:
                self.next_turn(skip=2)  # reverse acts like skip in 2-player game
            else:
                self.next_turn()
            return f"Played {card}. Turn direction reversed."

        else:
            self.next_turn()
            return f"Played {card}"



    def draw_or_pass(self, player_id):
        if self.players[player_id].has_won:
            return "You have already won and can't play anymore"
        if player_id != self.get_current_player():
            return "Not your turn"
        if player_id in self.drawn_this_turn:
            return "You have already drawn a card this turn"
        player = self.get_player(player_id)
        player.draw_card(self.deck)
        if len(player.hand) == 0:
            self.winner = player_id
        self.drawn_this_turn.add(player_id)
        self.next_turn()
        return "Drew a card and turn passed"
