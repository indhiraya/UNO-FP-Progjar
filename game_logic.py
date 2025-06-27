# game_logic.py
import random

# --- Game Constants ---
COLORS = ["red", "green", "blue", "yellow"]
VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]

class Card:
    """Represents a single UNO card with a color and a value."""
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def matches(self, other_card):
        """Checks if this card can be played on top of another card."""
        # Wild cards can always be played.
        if self.color == "black":
            return True
        # A card can be played if its color or value matches the top card.
        return self.color == other_card.color or self.value == other_card.value

    def __str__(self):
        """Provides a user-friendly string representation of the card."""
        color_str = self.color if self.color != "black" else "wild"
        return f"{color_str} {self.value}"

class Deck:
    """Represents the deck of cards, including draw and shuffle operations."""
    def __init__(self):
        """Initializes and shuffles a standard 108-card UNO deck."""
        self.cards = []
        # Add colored number and action cards.
        for color in COLORS:
            self.cards.append(Card(color, "0"))
            for value in [v for v in VALUES if v != "0"]:
                self.cards.extend([Card(color, value), Card(color, value)])
        # Add Wild and Wild +4 cards.
        for _ in range(4):
            self.cards.extend([Card("black", "wild"), Card("black", "+4")])
        random.shuffle(self.cards)

    def draw(self):
        """Draws a card from the deck, reshuffling if it becomes empty."""
        if not self.cards:
            print("Deck is empty. Reshuffling...")
            self.__init__() # Re-initialize and re-shuffle the deck.
        return self.cards.pop()

class Player:
    """Represents a player in the game, managing their hand."""
    def __init__(self, player_id):
        self.id = player_id
        self.hand = []

    def draw_cards(self, deck, count=1):
        """Draws a specified number of cards from the deck into the player's hand."""
        for _ in range(count):
            card = deck.draw()
            if card:
                self.hand.append(card)

    def play_card(self, card_index, top_card):
        """
        Attempts to play a card from the hand. Returns the card if valid, else None.
        """
        if card_index < len(self.hand):
            card = self.hand[card_index]
            if card.matches(top_card):
                return self.hand.pop(card_index)
        return None

    def get_hand_str(self):
        """Returns a list of strings representing the cards in hand."""
        return [str(c) for c in self.hand]

class Game:
    """
    Manages the entire game state, including players, turns, and rules.
    This class is the single source of truth for the game's logic.
    """
    def __init__(self):
        # --- Core Game State ---
        self.deck = Deck()
        self.players = {}
        self.turn_order = []
        self.current_turn_index = 0
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise.
        self.winner = None
        self.last_action_message = ""
        
        # --- UNO Callout State ---
        self.players_on_uno = set() # Players with 1 card left.
        self.safe_from_call_out = set() # Players who have correctly declared "UNO!".

        # --- Initial Card Setup ---
        # Draw the first card for the discard pile, ensuring it's not a special action card.
        self.top_card = self.deck.draw()
        while self.top_card.color == "black" or self.top_card.value in ["+2", "skip", "reverse"]:
            self.deck.cards.insert(0, self.top_card)
            random.shuffle(self.deck.cards)
            self.top_card = self.deck.draw()

    def _get_current_player_id(self):
        """Helper to get the ID of the player whose turn it is."""
        return self.turn_order[self.current_turn_index] if self.turn_order else None

    def _get_player_statuses(self):
        """Returns a dictionary of statuses for all players (card count, UNO status)."""
        return {
            pid: {"count": len(p.hand), "on_uno": pid in self.players_on_uno, "safe": pid in self.safe_from_call_out}
            for pid, p in self.players.items()
        }

    def get_full_game_state(self, for_player_id):
        """Compiles and returns the complete game state from a specific player's perspective."""
        player = self.players.get(for_player_id)
        if not player:
            return {"status": "ERROR", "message": "Player not found"}
        
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
        """Adds a new player to the game, deals their initial hand."""
        if player_id not in self.players:
            player = Player(player_id)
            player.draw_cards(self.deck, 7)
            self.players[player_id] = player
            self.turn_order.append(player_id)
            self.last_action_message = f"{player_id} has joined the game."
            self._update_player_uno_status(player_id)

    def _update_player_uno_status(self, player_id):
        """Updates a player's status regarding the UNO rule (1 card left)."""
        player_hand_size = len(self.players[player_id].hand)
        if player_hand_size == 1:
            self.players_on_uno.add(player_id)
        else:
            # If a player no longer has one card, remove them from all UNO sets.
            self.players_on_uno.discard(player_id)
            self.safe_from_call_out.discard(player_id)

    def declare_uno(self, player_id):
        """Handles a player declaring 'UNO!'."""
        if len(self.players[player_id].hand) == 1:
            self.safe_from_call_out.add(player_id)
            self.last_action_message = f"{player_id} declared UNO!"
        else:
            # Penalty for falsely declaring UNO.
            self.players[player_id].draw_cards(self.deck, 1)
            self.last_action_message = f"{player_id} falsely declared UNO and drew a card."
            self._update_player_uno_status(player_id)

    def call_out_player(self, caller_id, target_id):
        """Handles a player calling out another for not declaring 'UNO!'."""
        # Check if the target has 1 card but is not safe (hasn't declared UNO).
        if target_id in self.players_on_uno and target_id not in self.safe_from_call_out:
            self.players[target_id].draw_cards(self.deck, 2)
            self.last_action_message = f"{caller_id} called out {target_id}! {target_id} draws 2 cards."
            self._update_player_uno_status(target_id)
        else:
            # Penalty for a false call-out.
            self.players[caller_id].draw_cards(self.deck, 1)
            self.last_action_message = f"{caller_id}'s call-out failed. {caller_id} draws a card."
            self._update_player_uno_status(caller_id)

    def _move_to_next_player(self, skip=1):
        """Advances the turn to the next player based on game direction and skips."""
        if not self.turn_order: return
        num_players = len(self.turn_order)
        self.current_turn_index = (self.current_turn_index + self.direction * skip) % num_players
        # Reset the action message unless it's a game-ending message.
        if not self.last_action_message.startswith(("🎉", "Error")):
            self.last_action_message = ""

    def _process_card_effects(self, played_card, player_id, new_color=None):
        """Applies the special effects of an action or wild card."""
        value = played_card.value
        num_players = len(self.turn_order)
        next_player_idx = (self.current_turn_index + self.direction) % num_players
        next_player_id = self.turn_order[next_player_idx]
        
        if value == "skip":
            self.last_action_message += f" {next_player_id}'s turn is skipped."
            self._move_to_next_player(skip=2)
        elif value == "reverse":
            if num_players == 2: # In a 2-player game, reverse acts like a skip.
                self.last_action_message += " Direction reversed (acts as Skip)."
                self._move_to_next_player(skip=2)
            else:
                self.direction *= -1
                self.last_action_message += " Direction of play reversed."
                self._move_to_next_player()
        elif value == "+2":
            self.players[next_player_id].draw_cards(self.deck, 2)
            self._update_player_uno_status(next_player_id)
            self.last_action_message += f" {next_player_id} draws 2 cards."
            self._move_to_next_player(skip=2)
        elif value == "+4":
            played_card.color = new_color
            self.players[next_player_id].draw_cards(self.deck, 4)
            self._update_player_uno_status(next_player_id)
            self.last_action_message += f" Color changed to {new_color}. {next_player_id} draws 4 cards."
            self._move_to_next_player(skip=2)
        elif value == "wild":
            played_card.color = new_color
            self.last_action_message += f" Color changed to {new_color}."
            self._move_to_next_player()
        else: # Regular number card
            self._move_to_next_player()

    def play_card(self, player_id, card_index, new_color=None):
        """Main logic for a player playing a card."""
        if self.winner: return {"status": "ERROR", "message": "The game has already ended."}
        if player_id != self._get_current_player_id():
            return {"status": "ERROR", "message": "It's not your turn."}
            
        player = self.players[player_id]
        played_card = player.play_card(card_index, self.top_card)
        
        if not played_card:
            return {"status": "ERROR", "message": "That card cannot be played."}
        
        self.top_card = played_card
        self.last_action_message = f"{player_id} played a {played_card}."
        
        # Check for a winner.
        if not player.hand:
            self.winner = player_id
            self.last_action_message = f"🎉 {player_id} IS THE WINNER! 🎉"
            return {"status": "OK"}
        
        self._update_player_uno_status(player_id)
        self._process_card_effects(played_card, player_id, new_color)

        return {"status": "OK"}

    def draw_card(self, player_id):
        """Main logic for a player drawing a card."""
        if self.winner: return {"status": "ERROR", "message": "The game has already ended."}
        if player_id != self._get_current_player_id():
            return {"status": "ERROR", "message": "It's not your turn."}
        
        player = self.players[player_id]
        player.draw_cards(self.deck, 1)
        self.last_action_message = f"{player_id} drew a card."
        self._update_player_uno_status(player_id)
        
        # After drawing, the player's turn ends.
        self._move_to_next_player()
        return {"status": "OK"}