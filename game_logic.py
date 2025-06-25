# import random

# COLORS = ["red", "green", "blue", "yellow"]
# VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]

# class Card:
#     def __init__(self, color, value):
#         self.color = color
#         self.value = value

#     def matches(self, other):
#         return self.color == other.color or self.value == other.value

#     def __str__(self):
#         return f"{self.color} {self.value}"

# class Deck:
#     def __init__(self):
#         self.cards = []
#         for color in COLORS:
#             for value in VALUES:
#                 self.cards.append(Card(color, value))
#                 self.cards.append(Card(color, value))  # two cards per combination
#         random.shuffle(self.cards)

#     def draw(self):
#         if not self.cards:
#             return None
#         return self.cards.pop()

# class Player:
#     def __init__(self, player_id):
#         self.id = player_id
#         self.hand = []

#     def draw_card(self, deck):
#         card = deck.draw()
#         if card:
#             self.hand.append(card)

#     def play_card(self, card_index, top_card):
#         if card_index >= len(self.hand):
#             return None
#         card = self.hand[card_index]
#         if card.matches(top_card):
#             return self.hand.pop(card_index)
#         return None

#     def get_hand(self):
#         return [str(c) for c in self.hand]

# class Game:
#     def __init__(self):
#         self.deck = Deck()
#         self.players = {}
#         self.turn_order = []
#         self.current_turn = 0
#         self.top_card = self.deck.draw()
#         self.drawn_this_turn = set()
#         self.direction = 1  # 1 = clockwise, -1 = counter-clockwise

#     def add_player(self, player_id):
#         if player_id not in self.players:
#             player = Player(player_id)
#             for _ in range(7):
#                 player.draw_card(self.deck)
#             self.players[player_id] = player
#             self.turn_order.append(player_id)

#     def get_player(self, player_id):
#         return self.players.get(player_id)

#     def get_current_player(self):
#         return self.turn_order[self.current_turn]

#     def next_turn(self):
#         self.current_turn = (self.current_turn + self.direction) % len(self.turn_order)
#         self.drawn_this_turn.clear()

#     def play_card(self, player_id, card_index):
#         if player_id != self.get_current_player():
#             return "Not your turn"

#         player = self.get_player(player_id)
#         card = player.play_card(card_index, self.top_card)

#         if not card:
#             return "Invalid card"

#         self.top_card = card

#         if card.value == "+2":
#             next_index = (self.current_turn + self.direction) % len(self.turn_order)
#             next_player_id = self.turn_order[next_index]
#             next_player = self.get_player(next_player_id)
#             for _ in range(2):
#                 next_player.draw_card(self.deck)
#             self.current_turn = (self.current_turn + 2 * self.direction) % len(self.turn_order)
#             self.drawn_this_turn.clear()
#             return f"Played {card}. {next_player_id} draws 2 cards and is skipped."

#         elif card.value == "skip":
#             if len(self.turn_order) == 2:
#                 self.drawn_this_turn.clear()
#                 return f"Played {card}. Next player is skipped, your turn again."
#             else:
#                 skipped_index = (self.current_turn + self.direction) % len(self.turn_order)
#                 skipped_player_id = self.turn_order[skipped_index]
#                 self.current_turn = (self.current_turn + 2 * self.direction) % len(self.turn_order)
#                 self.drawn_this_turn.clear()
#                 return f"Played {card}. {skipped_player_id} is skipped."

#         elif card.value == "reverse":
#             if len(self.turn_order) == 2:
#                 # treat reverse as skip if 2 players
#                 skipped_index = (self.current_turn + self.direction) % len(self.turn_order)
#                 skipped_player_id = self.turn_order[skipped_index]
#                 self.current_turn = (self.current_turn + 2 * self.direction) % len(self.turn_order)
#                 self.drawn_this_turn.clear()
#                 return f"Played {card}. (2-player reverse acts as skip) {skipped_player_id} is skipped."
#             else:
#                 self.direction *= -1
#                 self.next_turn()
#                 return f"Played {card}. Turn direction reversed."

#         else:
#             self.next_turn()
#             return f"Played {card}"

#     def draw_or_pass(self, player_id):
#         if player_id != self.get_current_player():
#             return "Not your turn"
#         if player_id in self.drawn_this_turn:
#             return "You have already drawn a card this turn"
#         player = self.get_player(player_id)
#         player.draw_card(self.deck)
#         self.drawn_this_turn.add(player_id)
#         self.next_turn()
#         return "Drew a card and turn passed"

import random

COLORS = ["red", "green", "blue", "yellow"]
VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]
WILD_CARDS = ["wild", "+4"]


class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def matches(self, other):
        return self.color == other.color or self.value == other.value or self.color == "wild"

    def __str__(self):
        return f"{self.color} {self.value}"


class Deck:
    def __init__(self):
        self.cards = []
        for color in COLORS:
            for value in VALUES:
                self.cards.append(Card(color, value))
                self.cards.append(Card(color, value))  # Dua kartu per kombinasi
        for _ in range(4):  # 4 kartu wild dan +4
            self.cards.append(Card("wild", "wild"))
            self.cards.append(Card("wild", "+4"))
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
        self.direction = 1  # 1 = searah jarum jam, -1 = berlawanan
        self.top_card = self.deck.draw()
        self.drawn_this_turn = set()

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

    def next_turn(self, skip_count=1):
        self.current_turn = (self.current_turn + self.direction * skip_count) % len(self.turn_order)
        self.drawn_this_turn.clear()

    def play_card(self, player_id, card_index, new_color=None):
        if player_id != self.get_current_player():
            return "Not your turn"

        player = self.get_player(player_id)
        card = player.play_card(card_index, self.top_card)

        if not card:
            return "Invalid card"

        # Ubah warna kartu wild sebelum jadi top_card
        if card.color == "wild" and new_color in COLORS:
            card.color = new_color

        self.top_card = card

        # Efek kartu spesial
        if card.value == "+2":
            next_id = self._get_next_player()
            for _ in range(2):
                self.players[next_id].draw_card(self.deck)
            self.next_turn(2)
            return f"Played {card}. {next_id} draws 2 cards and is skipped."

        elif card.value == "skip":
            skipped_id = self._get_next_player()
            if len(self.turn_order) == 2:
                self.next_turn(1)
                return f"Played {card}. Next player is skipped, your turn again."
            else:
                self.next_turn(2)
                return f"Played {card}. {skipped_id} is skipped."

        elif card.value == "reverse":
            if len(self.turn_order) == 2:
                # Reverse dianggap sebagai skip
                self.next_turn(2)
                return f"Played {card}. Acts as skip with 2 players."
            else:
                self.direction *= -1
                self.next_turn(1)
                return f"Played {card}. Turn order reversed."

        elif card.value == "+4":
            if new_color not in COLORS:
                return "You must choose a color for +4"
            next_id = self._get_next_player()
            for _ in range(4):
                self.players[next_id].draw_card(self.deck)
            self.next_turn(2)
            return f"Played {card}. {next_id} draws 4 cards and is skipped. Color changed to {new_color}."

        elif card.value == "wild":
            if new_color not in COLORS:
                return "You must choose a color for wild"
            self.next_turn(1)
            return f"Played {card}. Color changed to {new_color}."

        else:
            self.next_turn(1)
            return f"Played {card}"

    def draw_or_pass(self, player_id):
        if player_id != self.get_current_player():
            return "Not your turn"
        if player_id in self.drawn_this_turn:
            return "You have already drawn a card this turn"

        player = self.get_player(player_id)
        player.draw_card(self.deck)
        self.drawn_this_turn.add(player_id)
        self.next_turn()
        return "Drew a card and turn passed"

    def _get_next_player(self):
        return self.turn_order[(self.current_turn + self.direction) % len(self.turn_order)]
