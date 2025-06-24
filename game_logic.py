import random

COLORS = ["red", "green", "blue", "yellow"]
VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def matches(self, other):
        return self.color == other.color or self.value == other.value

    def __str__(self):
        return f"{self.color} {self.value}"

class Deck:
    def __init__(self):
        self.cards = []
        for color in COLORS:
            for value in VALUES:
                self.cards.append(Card(color, value))
                self.cards.append(Card(color, value))  # dua kartu setiap kombinasi
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            return None
        return self.cards.pop()

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.hand = []

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

    def add_player(self, player_id):
        if player_id not in self.players:
            player = Player(player_id)
            for _ in range(7):
                player.draw_card(self.deck)
            self.players[player_id] = player
            self.turn_order.append(player_id)

    def get_player(self, player_id):
        return self.players.get(player_id)

    def get_current_player(self):
        return self.turn_order[self.current_turn]

    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.turn_order)

    def play_card(self, player_id, card_index):
        if player_id != self.get_current_player():
            return "Not your turn"
        player = self.get_player(player_id)
        card = player.play_card(card_index, self.top_card)
        if card:
            self.top_card = card
            self.next_turn()
            return f"Played {card}"
        else:
            return "Invalid card"