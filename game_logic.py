# game_logic.py
import random

# DIUBAH: Menambahkan 'wild' dan '+4' ke VALUES untuk pembuatan Deck yang lebih akurat
COLORS = ["red", "green", "blue", "yellow"]
VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]
SPECIAL_VALUES = ["wild", "+4"]


class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def matches(self, other_card):
        # Kartu Wild atau +4 selalu bisa dimainkan
        if self.color == "black":
            return True
        # Mencocokkan berdasarkan warna atau nilai
        return self.color == other_card.color or self.value == other_card.value

    def __str__(self):
        # Nilai 'wild' dan '+4' seringkali tidak memiliki warna (diwakili 'black')
        color_str = self.color if self.color != "black" else "wild"
        return f"{color_str} {self.value}"


class Deck:
    def __init__(self):
        self.cards = []
        # Kartu biasa dan aksi berwarna
        for color in COLORS:
            for value in VALUES:
                self.cards.append(Card(color, value))
                if value != "0": # Hanya ada satu '0' per warna
                    self.cards.append(Card(color, value))
        # Kartu Wild dan Wild +4
        for _ in range(4):
            self.cards.append(Card("black", "wild"))
            self.cards.append(Card("black", "+4"))
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            self.__init__() # Jika kartu habis, buat & kocok dek baru
        return self.cards.pop()


class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.hand = []

    def draw_card(self, deck, count=1):
        for _ in range(count):
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
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.winner = None
        self.top_card = self.deck.draw()
        # Pastikan kartu pertama bukan kartu aksi spesial
        while self.top_card.value in SPECIAL_VALUES or self.top_card.value in ["+2", "skip", "reverse"]:
            self.top_card = self.deck.draw()

        # BARU: Logika untuk mekanik "UNO!"
        self.needs_to_declare_uno = None
        self.last_status_message = ""

    def add_player(self, player_id):
        if player_id not in self.players:
            player = Player(player_id)
            player.draw_card(self.deck, 7)
            self.players[player_id] = player
            self.turn_order.append(player_id)
            return True
        return False

    def get_player(self, player_id):
        return self.players.get(player_id)

    def get_current_player_id(self):
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn]

    def get_all_player_status(self):
        return {pid: len(p.hand) for pid, p in self.players.items()}

    def next_turn(self, skip=1):
        # BARU: Cek pinalti UNO sebelum giliran berpindah
        if self.needs_to_declare_uno:
            player_to_penalize = self.players[self.needs_to_declare_uno]
            player_to_penalize.draw_card(self.deck, 2)
            self.last_status_message = f"Pinalti! {self.needs_to_declare_uno} tidak menyatakan UNO! dan menarik 2 kartu."
            self.needs_to_declare_uno = None # Reset status

        num_players = len(self.turn_order)
        self.current_turn = (self.current_turn + self.direction * skip) % num_players

    # BARU: Fungsi untuk menyatakan UNO
    def declare_uno(self, player_id):
        if player_id == self.needs_to_declare_uno:
            self.last_status_message = f"{player_id} menyatakan UNO!"
            self.needs_to_declare_uno = None # Pemain aman dari pinalti
            return {"status": "OK", "message": "Berhasil menyatakan UNO!"}
        return {"status": "ERROR", "message": "Tidak perlu menyatakan UNO."}

    def play_card(self, player_id, card_index, new_color=None):
        if player_id != self.get_current_player_id():
            return "Bukan giliranmu"
        
        player = self.get_player(player_id)
        
        # Logika untuk memaksa pemain draw (+2 atau +4)
        if self.top_card.value in ["+2", "+4"] and self.top_card.matches(player.hand[card_index]) == False:
             return f"Anda harus mengambil kartu atau memainkan kartu {self.top_card.value} lain."

        played_card = player.play_card(card_index, self.top_card)

        if not played_card:
            return "Kartu tidak valid"

        self.last_status_message = "" # Reset pesan status
        self.top_card = played_card
        
        # BARU: Cek jika pemain masuk ke state UNO
        if len(player.hand) == 1:
            self.needs_to_declare_uno = player_id
        
        if len(player.hand) == 0:
            self.winner = player_id
            return f"🎉 {player_id} MENANG! 🎉"

        # Proses efek kartu
        value = self.top_card.value
        if value == "skip":
            self.next_turn(skip=2)
            return f"Giliran {self.turn_order[(self.current_turn - self.direction) % len(self.turn_order)]} dilewati."
        elif value == "reverse":
            self.direction *= -1
            self.next_turn()
            return "Arah permainan dibalik."
        elif value == "+2":
            player_to_draw_index = (self.current_turn + self.direction) % len(self.turn_order)
            player_to_draw_id = self.turn_order[player_to_draw_index]
            self.players[player_to_draw_id].draw_card(self.deck, 2)
            self.next_turn()
            return f"{player_to_draw_id} menarik 2 kartu."
        elif value == "+4":
            if not new_color: return "Harus pilih warna untuk Wild +4."
            self.top_card.color = new_color
            player_to_draw_index = (self.current_turn + self.direction) % len(self.turn_order)
            player_to_draw_id = self.turn_order[player_to_draw_index]
            self.players[player_to_draw_id].draw_card(self.deck, 4)
            self.next_turn(skip=2)
            return f"Warna jadi {new_color}. {player_to_draw_id} menarik 4 kartu dan gilirannya dilewati."
        elif value == "wild":
            if not new_color: return "Harus pilih warna untuk Wild."
            self.top_card.color = new_color
            self.next_turn()
            return f"Warna diubah menjadi {new_color}."
        else: # Kartu angka biasa
            self.next_turn()
            return f"Memainkan {self.top_card.color} {self.top_card.value}"

    def draw_card_action(self, player_id):
        if player_id != self.get_current_player_id():
            return "Bukan giliranmu"
        
        player = self.get_player(player_id)
        player.draw_card(self.deck, 1)
        self.next_turn()
        return f"{player_id} menarik 1 kartu."