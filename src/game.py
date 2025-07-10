from typing import List, Optional, Tuple
import random
from copy import deepcopy

from .card import Card, create_deck
from .player import Player, HumanPlayer, SimpleAI


class Game:
    """Main game engine for the Dutch/Cabo card game"""
    
    def __init__(self, players: List[Player], silent_mode: bool = False):
        """
        Initialize a new game.
        
        Args:
            players: List of Player objects (must be 2-4 players)
            silent_mode: If True, suppress all print statements for training
        """
        if not 2 <= len(players) <= 4:
            raise ValueError("Game must have 2-4 players")
        
        self.players = players
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []
        self.current_player_index = 0
        self.game_over = False
        self.winner: Optional[Player] = None
        self.turn_count = 0
        self.round_number = 1
        self.dutch_called = False
        self.dutch_caller: Optional[Player] = None
        self.final_round = False
        self.turns_after_dutch = 0
        self.silent_mode = silent_mode  # For training - suppress all prints
        
        # Game settings
        self.max_rounds = 1  # Can be expanded for multiple rounds
        
    def setup_new_game(self):
        """Set up a new game by shuffling deck and dealing cards"""
        if not self.silent_mode:
            print(f"\n{'='*50}")
            print(f"Starting Round {self.round_number}")
            print(f"{'='*50}")
        
        # Reset game state
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.discard_pile = []
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        self.dutch_called = False
        self.dutch_caller = None
        self.final_round = False
        self.turns_after_dutch = 0
        
        # Reset all players
        for player in self.players:
            player.reset_for_new_game()
        
        # Deal 4 cards to each player
        for player in self.players:
            for position in range(4):
                card = self.deck.pop()
                player.receive_card(card, position)
        
        # Start discard pile with one card
        self.discard_pile.append(self.deck.pop())
        
        # Each player peeks at one card initially
        for player in self.players:
            position = player.choose_initial_peek()
            peeked_card = player.peek_at_own_card(position)
            if not self.silent_mode:
                print(f"{player.name} peeked at position {position}: {peeked_card}")
        
        # Randomly choose starting player
        self.current_player_index = random.randint(0, len(self.players) - 1)
        if not self.silent_mode:
            print(f"\n{self.players[self.current_player_index].name} goes first!")
    
    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.players[self.current_player_index]
    
    def get_other_players(self, exclude_player: Player) -> List[Player]:
        """Get all players except the specified one"""
        return [p for p in self.players if p != exclude_player]
    
    def next_turn(self):
        """Move to the next player's turn"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_count += 1
        
        # Track turns after Dutch call (only count non-Dutch caller turns)
        if self.final_round:
            current_player = self.get_current_player()
            if current_player != self.dutch_caller:
                self.turns_after_dutch += 1
                remaining_turns = (len(self.players) - 1) - self.turns_after_dutch
                if remaining_turns > 0:
                    print(f"⏳ Final round: {remaining_turns} more turn(s) until game ends")
    
    def draw_card(self) -> Card:
        """Draw a card from the deck"""
        if not self.deck:
            # Reshuffle discard pile if deck is empty (keep top card)
            if len(self.discard_pile) <= 1:
                raise RuntimeError("No cards available to draw")
            
            top_card = self.discard_pile.pop()
            self.deck = self.discard_pile.copy()
            random.shuffle(self.deck)
            self.discard_pile = [top_card]
            print("Deck was empty - reshuffled discard pile!")
            
            # Update BayesPlayer deck composition after reshuffle
            for player in self.players:
                if hasattr(player, '_initialize_deck_tracking'):
                    # Reset deck tracking since deck was reshuffled
                    player.deck_composition = player._initialize_deck_tracking()
                    # Remove known discarded cards
                    for discarded_card in player.discarded_cards:
                        value = discarded_card.get_score_value()
                        if value in player.deck_composition and player.deck_composition[value] > 0:
                            player.deck_composition[value] -= 1
        
        drawn_card = self.deck.pop()
        
        # Notify BayesPlayer about drawn card (they can observe it)
        for player in self.players:
            if hasattr(player, 'observe_card'):
                player.observe_card(drawn_card)
        
        return drawn_card
    
    def discard_card(self, card: Card):
        """Add a card to the discard pile"""
        self.discard_pile.append(card)
        
        # Notify BayesPlayer about discarded card
        for player in self.players:
            if hasattr(player, 'observe_discard'):
                player.observe_discard(card)
    
    def get_game_state(self) -> dict:
        """Get current game state information (for AI decision making)"""
        return {
            "turn_count": self.turn_count,
            "current_player": self.get_current_player().name,
            "player_hand_sizes": {p.name: p.get_hand_size() for p in self.players},
            "top_discard": self.discard_pile[-1] if self.discard_pile else None,
            "deck_size": len(self.deck),
            "players": [{"name": p.name, "hand_size": p.get_hand_size(), "known_cards": sum(p.known_cards)} 
                       for p in self.players]
        }
    
    def display_game_state(self, current_player: Player):
        """Display the current game state"""
        from .player import HumanPlayer
        
        if self.silent_mode:
            return  # Skip all display in silent mode
        
        print(f"\n{'='*60}")
        print(f"Turn {self.turn_count + 1} - {current_player.name}'s Turn")
        print(f"{'='*60}")
        
        # Show players' hands (only show known cards for others)
        for player in self.players:
            if player == current_player:
                print(f"YOUR HAND: {player.display_hand()}")
            else:
                # For opponents, only show cards that are publicly known or empty slots
                hidden_hand = []
                for i, card in enumerate(player.hand):
                    if card is None:
                        hidden_hand.append("[ ]")
                    else:
                        hidden_hand.append("[?]")  # Always hidden unless publicly revealed
                hand_display = " ".join(hidden_hand)
                print(f"{player.name}: {hand_display} ({player.get_hand_size()} cards)")
        
        print(f"\nTop discard: {self.discard_pile[-1] if self.discard_pile else 'None'}")
        print(f"Cards left in deck: {len(self.deck)}")
        
        # Show Dutch call status
        if self.dutch_called:
            print(f"🚨 DUTCH CALLED by {self.dutch_caller.name}! Final round in progress.")
        elif self.final_round:
            print("🏁 Final round - game ending soon!")
    
    def handle_drawn_card_action(self, player: Player, drawn_card: Card, action: dict):
        """
        Handle the player's chosen action with the drawn card.
        
        Args:
            player: The current player
            drawn_card: The card that was drawn
            action: Dictionary describing the chosen action
        """
        action_type = action["action"]
        
        if action_type == "discard":
            # Simply discard the drawn card
            self.discard_card(drawn_card)
            print(f"{player.name} discarded {drawn_card}")
            
        elif action_type == "swap":
            # Swap drawn card with one in hand
            position = action["position"]
            old_card = player.swap_card(position, drawn_card)
            print(f"{player.name} swapped {drawn_card} for {old_card} at position {position}")
            
            # Update BayesPlayer knowledge about opponent actions
            for p in self.players:
                if hasattr(p, 'infer_from_opponent_action') and p != player:
                    p.infer_from_opponent_action(player.name, action)
            
            # Check if the swapped-out card has special abilities
            if old_card.has_special_ability():
                self.offer_special_ability_after_swap(player, old_card)
            else:
                self.discard_card(old_card)
            

        elif action_type == "use_ability":
            # Use special card ability
            if drawn_card.is_jack():
                self.handle_jack_ability(player, drawn_card)
            elif drawn_card.is_queen():
                self.handle_queen_ability(player, drawn_card)
            # Discard the special card after use
            self.discard_card(drawn_card)
            
        elif action_type == "call_dutch":
            # Player calls Dutch - finish the game after everyone else gets one more turn
            self.discard_card(drawn_card)
            self.dutch_called = True
            self.dutch_caller = player
            self.final_round = True
            self.turns_after_dutch = 0  # Reset counter
            remaining_players = len(self.players) - 1  # Everyone except Dutch caller
            print(f"\n🚨 {player.name} called DUTCH! Final round begins!")
            print(f"All other players ({remaining_players}) get one more turn.")
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def offer_special_ability_after_swap(self, player: Player, special_card: Card):
        """Offer to use special ability of a card that was swapped out"""
        from .player import HumanPlayer
        
        card_type = "Jack" if special_card.is_jack() else "Queen"
        ability = "swap cards with an opponent" if special_card.is_jack() else "peek at any card"
        
        if isinstance(player, HumanPlayer):
            print(f"\n✨ The card you swapped out was a {card_type}!")
            print(f"The {card_type} allows you to {ability}.")
            choice = input("Do you want to use this special ability? (y/n): ").lower().strip()
            
            if choice in ['y', 'yes']:
                print(f"Using {card_type}'s special ability...")
                if special_card.is_jack():
                    self.handle_jack_ability(player, special_card)
                elif special_card.is_queen():
                    self.handle_queen_ability(player, special_card)
            else:
                print(f"Skipping {card_type} ability.")
        else:
            # AI automatically uses special abilities
            print(f"✨ {player.name} swapped out a {card_type} and uses its ability!")
            if special_card.is_jack():
                self.handle_jack_ability(player, special_card)
            elif special_card.is_queen():
                self.handle_queen_ability(player, special_card)
        
        # Always discard the special card after potential use
        self.discard_card(special_card)
    
    def handle_jack_ability(self, player: Player, jack_card: Card):
        """Handle Jack's swap ability"""
        from .player import HumanPlayer
        
        opponents = self.get_other_players(player)
        if not opponents:
            print("No opponents to swap with!")
            return
        
        # Choose swap targets
        target_player, target_position = player.choose_swap_target(opponents, self.get_game_state())
        
        # Choose own card to swap
        valid_positions = player.get_valid_positions()
        if not valid_positions:
            print("No cards to swap!")
            return
        
        if isinstance(player, HumanPlayer):
            print("Choose your card to swap:")
            own_position = player._choose_swap_position()
        else:
            # AI chooses randomly for now
            own_position = random.choice(valid_positions)
        
        # Perform the swap
        player_card = player.hand[own_position]
        opponent_card = target_player.hand[target_position]
        
        player.hand[own_position] = opponent_card
        target_player.hand[target_position] = player_card
        
        # Update known cards properly:
        # - The active player (who used Jack) always knows what they received
        player.known_cards[own_position] = True
        
        # - The target player loses knowledge of both cards:
        #   1. They don't know what they received (it's face-down)
        #   2. They also don't know what they gave away anymore (it's now in opponent's hand)
        target_knew_given_card = target_player.known_cards[target_position]
        target_player.known_cards[target_position] = False  # Received card is unknown
        
        # CRITICAL: The card player received should NOT be automatically known if target knew it
        # Jack swap makes received cards face-down regardless of previous knowledge
        
        # Display results with proper visibility
        if isinstance(player, HumanPlayer):
            print(f"You used Jack to swap with {target_player.name}")
            print(f"You gave {player_card} and received {opponent_card}")
        elif isinstance(target_player, HumanPlayer):
            print(f"{player.name} used Jack to swap with you!")
            if target_knew_given_card:
                print(f"You gave away {opponent_card} from position {target_position}")
            else:
                print(f"You gave away a face-down card from position {target_position}")
            print(f"You received a face-down card at position {target_position}")
            print("(Use Queen to peek at what you received)")
        else:
            print(f"{player.name} swapped cards with {target_player.name}")
    
    def handle_queen_ability(self, player: Player, queen_card: Card):
        """Handle Queen's peek ability"""
        from .player import HumanPlayer
        
        opponents = self.get_other_players(player)
        target_player, target_position = player.choose_peek_target(opponents, self.get_game_state())
        
        if target_player is None:
            # Peek at own card
            peeked_card = player.peek_at_own_card(target_position)
            if isinstance(player, HumanPlayer):
                print(f"\n👁️ You secretly looked at your card at position {target_position}: {peeked_card}")
                input("Press Enter to continue (card is now hidden again)...")
            else:
                print(f"{player.name} peeked at their own card at position {target_position}")
            
            # Update BayesPlayer knowledge about opponent learning their own card
            for p in self.players:
                if hasattr(p, 'update_opponent_knowledge') and p != player:
                    p.update_opponent_knowledge(player.name, target_position, "peek")
        else:
            # Peek at opponent's card
            peeked_card = target_player.hand[target_position]
            if isinstance(player, HumanPlayer):
                print(f"\n👁️ You secretly looked at {target_player.name}'s card at position {target_position}: {peeked_card}")
                input("Press Enter to continue (only you saw this card)...")
            else:
                print(f"{player.name} peeked at {target_player.name}'s card at position {target_position}")
            
            # Update BayesPlayer knowledge - player now knows opponent's card at position
            for p in self.players:
                if hasattr(p, 'update_opponent_knowledge') and p != player:
                    p.update_opponent_knowledge(player.name, target_position, "peek_opponent")
    
    def check_win_condition(self) -> bool:
        """
        Check if any player has won (empty hand, Dutch call completed, or turn limit).
        Returns True if game should end.
        """
        # Immediate win: empty hand
        for player in self.players:
            if player.is_hand_empty():
                self.winner = player
                self.game_over = True
                print(f"\n🎉 {player.name} wins by emptying their hand!")
                return True
        
        # Dutch call win condition - this is called from play_turn when appropriate
        if self.dutch_called and self.final_round:
            # Find player with lowest score
            lowest_score = float('inf')
            for player in self.players:
                score = player.get_score()
                if score < lowest_score:
                    lowest_score = score
                    self.winner = player
            
            self.game_over = True
            print(f"\n🏁 Dutch called! All players have had their final turn.")
            print(f"🎉 {self.winner.name} wins with the lowest score: {lowest_score} points!")
            return True
        
        # Fallback: turn limit reached
        if self.turn_count >= len(self.players) * 20:  # Increased limit
            lowest_score = float('inf')
            for player in self.players:
                score = player.get_score()
                if score < lowest_score:
                    lowest_score = score
                    self.winner = player
            self.game_over = True
            print(f"\n⏰ Turn limit reached! Lowest score wins!")
            return True
        
        return False
    
    def play_turn(self):
        """Execute one player's turn"""
        current_player = self.get_current_player()
        
        # Check if final round is complete (everyone except Dutch caller played once more)
        if (self.dutch_called and self.final_round and 
            self.turns_after_dutch >= len(self.players) - 1):
            # End the game - everyone except Dutch caller has played their final turn
            self.check_win_condition()
            return
        
        # Skip Dutch caller's turn in final round (they already played when calling Dutch)
        if (self.dutch_called and self.final_round and current_player == self.dutch_caller):
            print(f"⏭️ Skipping {current_player.name}'s turn (Dutch caller doesn't get another turn)")
            self.next_turn()
            return
        
        # Display game state
        self.display_game_state(current_player)
        
        # FIRST OPPORTUNITY: Discard doubles before drawing
        self.handle_doubles_opportunity(current_player, "before_draw")
        
        # Choose where to draw from and draw a card
        drawn_card = self.handle_card_draw(current_player)
        
        # Player chooses action
        action = current_player.choose_action(drawn_card, self.get_game_state())
        
        # Handle the action
        self.handle_drawn_card_action(current_player, drawn_card, action)
        
        # SECOND OPPORTUNITY: Discard doubles after turn actions
        self.handle_doubles_opportunity(current_player, "after_turn")
        
        # Check other win conditions (empty hand, turn limit)
        if self.check_win_condition():
            return
        
        # Move to next turn
        self.next_turn()
    
    def handle_doubles_opportunity(self, player: Player, timing: str):
        """Handle the opportunity to discard doubles and matching cards"""
        # First check for hand doubles
        doubles_available = player.get_known_doubles()
        if doubles_available:
            choice = player.want_to_discard_doubles(doubles_available, timing, self.get_game_state())
            if choice is not None:
                pos1, pos2 = choice
                try:
                    card1, card2 = player.discard_doubles(pos1, pos2)
                    self.discard_card(card1)
                    self.discard_card(card2)
                    
                    timing_msg = "before drawing" if timing == "before_draw" else "after turn actions"
                    print(f"🎲 {player.name} discarded doubles {card1} {timing_msg}")
                    print(f"Cards eliminated: 2, Hand size now: {player.get_hand_size()}")
                    
                except ValueError as e:
                    print(f"Error discarding doubles: {e}")
        
        # Then check for discard pile matches
        if len(self.discard_pile) > 0:
            top_discard = self.discard_pile[-1]
            matches_available = player.get_discard_pile_matches(top_discard)
            
            if matches_available:
                positions_to_discard = player.want_to_discard_pile_matches(
                    matches_available, top_discard, timing, self.get_game_state()
                )
                
                if positions_to_discard:
                    discarded_cards = []
                    # Sort positions in reverse order to avoid index issues
                    for pos in sorted(positions_to_discard, reverse=True):
                        if pos < len(player.hand) and player.hand[pos] is not None:
                            card = player.hand[pos]
                            discarded_cards.append(card)
                            player.hand[pos] = None
                            player.known_cards[pos] = False
                            self.discard_card(card)
                    
                    if discarded_cards:
                        timing_msg = "before drawing" if timing == "before_draw" else "after turn actions"
                        card_names = [str(card) for card in discarded_cards]
                        print(f"🎯 {player.name} discarded matching cards {card_names} {timing_msg}")
                        print(f"Cards eliminated: {len(discarded_cards)}, Hand size now: {player.get_hand_size()}")
                        
                        # Update BayesPlayer knowledge if present
                        for p in self.players:
                            if hasattr(p, 'observe_discard'):
                                for card in discarded_cards:
                                    p.observe_discard(card)
    
    def handle_card_draw(self, player: Player) -> Card:
        """Handle the card drawing phase of a turn"""
        from .player import HumanPlayer
        
        # Check if drawing from discard is allowed
        can_draw_from_discard = (
            len(self.discard_pile) > 0 and 
            not self.discard_pile[-1].has_special_ability()
        )
        
        if isinstance(player, HumanPlayer) and can_draw_from_discard:
            # Human player gets to choose
            top_discard = self.discard_pile[-1]
            print(f"\nDraw options:")
            print(f"1. Draw from deck (unknown card)")
            print(f"2. Draw from discard pile: {top_discard} (value: {top_discard.get_score_value()})")
            
            while True:
                try:
                    choice = int(input("Choose where to draw from (1-2): "))
                    if choice == 1:
                        drawn_card = self.draw_card()
                        print(f"\n{player.name} draws from deck...")
                        break
                    elif choice == 2:
                        drawn_card = self.discard_pile.pop()
                        print(f"\n{player.name} draws {drawn_card} from discard pile")
                        break
                    else:
                        print("Please choose 1 or 2.")
                except ValueError:
                    print("Please enter a valid number.")
        else:
            # AI player or no discard option
            if can_draw_from_discard and hasattr(player, 'choose_draw_source'):
                # AI can choose if implemented
                draw_choice = player.choose_draw_source(self.discard_pile[-1], self.get_game_state())
                if draw_choice == "discard":
                    drawn_card = self.discard_pile.pop()
                    print(f"\n{player.name} draws {drawn_card} from discard pile")
                else:
                    drawn_card = self.draw_card()
                    print(f"\n{player.name} draws from deck...")
            else:
                # Default: draw from deck
                drawn_card = self.draw_card()
                print(f"\n{player.name} draws from deck...")
        
        return drawn_card
    
    def play_game(self):
        """Play a complete game"""
        self.setup_new_game()
        
        while not self.game_over:
            try:
                self.play_turn()
            except KeyboardInterrupt:
                print("\nGame interrupted by user.")
                return
            except Exception as e:
                print(f"Error during turn: {e}")
                return
        
        self.display_final_results()
    
    def display_final_results(self):
        """Display final game results"""
        print(f"\n{'='*60}")
        print("GAME OVER!")
        print(f"{'='*60}")
        
        if self.winner:
            print(f"🎉 {self.winner.name} wins!")
        
        print("\nFinal Scores:")
        scores = []
        for player in self.players:
            score = player.get_score()
            scores.append((player.name, score))
            print(f"{player.name}: {score} points")
            print(f"  Final hand: {player.display_hand(reveal_all=True)}")
        
        # Sort by score (lowest wins)
        scores.sort(key=lambda x: x[1])
        print(f"\nRanking:")
        for i, (name, score) in enumerate(scores, 1):
            print(f"{i}. {name} - {score} points")


def create_game_from_setup() -> Game:
    """Create a game with player setup"""
    print("Welcome to Dutch Cabo!")
    print("=" * 40)
    
    # Get number of players
    while True:
        try:
            num_players = int(input("Number of players (2-4): "))
            if 2 <= num_players <= 4:
                break
            else:
                print("Please enter a number between 2 and 4.")
        except ValueError:
            print("Please enter a valid number.")
    
    players = []
    
    # Set up players
    for i in range(num_players):
        print(f"\nPlayer {i+1}:")
        print("1. Human player")
        print("2. AI player")
        
        while True:
            try:
                player_type = int(input("Choose player type: "))
                if player_type in [1, 2]:
                    break
                else:
                    print("Please choose 1 or 2.")
            except ValueError:
                print("Please enter a valid number.")
        
        name = input(f"Enter name for player {i+1}: ").strip()
        if not name:
            name = f"Player {i+1}"
        
        if player_type == 1:
            players.append(HumanPlayer(name))
        else:
            # Choose AI type
            print("AI Type:")
            print("1. Simple AI (information-focused)")
            print("2. Bayes AI (advanced probability)")
            
            while True:
                try:
                    ai_type = int(input("Choose AI type: "))
                    if ai_type in [1, 2]:
                        break
                    else:
                        print("Please choose 1 or 2.")
                except ValueError:
                    print("Please enter a valid number.")
            
            if ai_type == 1:
                players.append(SimpleAI(name))
            else:
                from players import BayesPlayer
                players.append(BayesPlayer(name))
    
    return Game(players) 