"""
Contextual Action Space for Dutch Cabo DQRN Multi-Head Agent

Each context has its own action space, handled by different network heads.
"""

from enum import Enum
from typing import Dict, List, Tuple
import torch


class ActionContext(Enum):
    """Different decision contexts in the game"""
    DRAW_SOURCE = "draw_source"
    MAIN_ACTION = "main_action"
    JACK_ABILITY = "jack_ability"
    QUEEN_ABILITY = "queen_ability"


class ContextualActionSpace:
    """
    Contextual action space where each context has its own action set.
    Used with multi-head DQRN architecture.
    """
    
    def __init__(self):
        self.context_actions = {}
        self.context_sizes = {}
        self._build_action_spaces()
    
    def _build_action_spaces(self):
        """Build action spaces for each context"""
        
        # DRAW_SOURCE: Choose where to draw from (2 actions)
        self.context_actions[ActionContext.DRAW_SOURCE] = {
            0: "draw_from_deck",
            1: "draw_from_discard"
        }
        self.context_sizes[ActionContext.DRAW_SOURCE] = 2
        
        # MAIN_ACTION: What to do with drawn card (7 actions)
        self.context_actions[ActionContext.MAIN_ACTION] = {
            0: "discard_drawn_card",
            1: "swap_position_0",
            2: "swap_position_1", 
            3: "swap_position_2",
            4: "swap_position_3",
            5: "use_special_ability",
            6: "call_dutch"
        }
        self.context_sizes[ActionContext.MAIN_ACTION] = 7
        
        # JACK_ABILITY: Swap my card with opponent's card (16 actions)
        # my_pos * 4 + opponent_pos = action_id
        self.context_actions[ActionContext.JACK_ABILITY] = {}
        for my_pos in range(4):
            for opp_pos in range(4):
                action_id = my_pos * 4 + opp_pos
                self.context_actions[ActionContext.JACK_ABILITY][action_id] = f"swap_my_{my_pos}_opponent_{opp_pos}"
        self.context_sizes[ActionContext.JACK_ABILITY] = 16
        
        # QUEEN_ABILITY: Peek at cards (8 actions)
        self.context_actions[ActionContext.QUEEN_ABILITY] = {}
        # Opponent positions 0-3
        for pos in range(4):
            self.context_actions[ActionContext.QUEEN_ABILITY][pos] = f"peek_opponent_pos_{pos}"
        # Own positions 0-3  
        for pos in range(4):
            self.context_actions[ActionContext.QUEEN_ABILITY][4 + pos] = f"peek_own_pos_{pos}"
        self.context_sizes[ActionContext.QUEEN_ABILITY] = 8
        
        print("Contextual Action Spaces:")
        for context, size in self.context_sizes.items():
            print(f"  {context.value}: {size} actions")
        print(f"Total contexts: {len(self.context_sizes)}")
    
    def get_action_size(self, context: ActionContext) -> int:
        """Get number of actions for a context"""
        return self.context_sizes[context]
    
    def get_max_action_size(self) -> int:
        """Get maximum action size across all contexts (for network design)"""
        return max(self.context_sizes.values())
    
    def get_valid_actions(self, context: ActionContext, game_state: Dict) -> List[int]:
        """
        Get valid action IDs for current context and game state.
        
        Args:
            context: Current decision context
            game_state: Current game state
            
        Returns:
            List of valid action IDs for this context
        """
        if context == ActionContext.DRAW_SOURCE:
            # Always can choose deck or discard
            return [0, 1]
        
        elif context == ActionContext.MAIN_ACTION:
            valid_actions = [0, 6]  # Always can discard or call dutch
            
            # Can swap with any non-None position
            own_hand = game_state.get("own_hand", [None] * 4)
            for i, card in enumerate(own_hand):
                if card is not None:
                    valid_actions.append(1 + i)  # swap_position_i
            
            # Can use ability if drawn card has one
            drawn_card = game_state.get("drawn_card", {})
            if drawn_card.get("has_ability", False):
                valid_actions.append(5)  # use_special_ability
            
            return sorted(valid_actions)
        
        elif context == ActionContext.JACK_ABILITY:
            valid_actions = []
            own_hand = game_state.get("own_hand", [None] * 4)
            opponent_hand = game_state.get("opponent_hand", [None] * 4)
            
            for my_pos in range(4):
                if own_hand[my_pos] is not None:
                    for opp_pos in range(4):
                        if opponent_hand[opp_pos] is not None:
                            action_id = my_pos * 4 + opp_pos
                            valid_actions.append(action_id)
            
            return valid_actions
        
        elif context == ActionContext.QUEEN_ABILITY:
            valid_actions = []
            own_hand = game_state.get("own_hand", [None] * 4)
            opponent_hand = game_state.get("opponent_hand", [None] * 4)
            
            # Opponent positions
            for pos in range(4):
                if opponent_hand[pos] is not None:
                    valid_actions.append(pos)
            
            # Own positions  
            for pos in range(4):
                if own_hand[pos] is not None:
                    valid_actions.append(4 + pos)
            
            return valid_actions
        
        return []
    
    def decode_action(self, context: ActionContext, action_id: int) -> Dict:
        """
        Decode action ID to game engine format.
        
        Args:
            context: Decision context
            action_id: Action ID within this context
            
        Returns:
            Action dictionary for game engine
        """
        if context not in self.context_actions:
            raise ValueError(f"Unknown context: {context}")
        
        if action_id not in self.context_actions[context]:
            raise ValueError(f"Invalid action {action_id} for context {context}")
        
        action_name = self.context_actions[context][action_id]
        
        if context == ActionContext.DRAW_SOURCE:
            source = "deck" if action_id == 0 else "discard"
            return {"action": "draw", "source": source}
        
        elif context == ActionContext.MAIN_ACTION:
            if action_id == 0:
                return {"action": "discard"}
            elif 1 <= action_id <= 4:
                return {"action": "swap", "position": action_id - 1}
            elif action_id == 5:
                return {"action": "use_ability"}
            elif action_id == 6:
                return {"action": "call_dutch"}
        
        elif context == ActionContext.JACK_ABILITY:
            my_pos = action_id // 4
            opp_pos = action_id % 4
            return {
                "action": "jack_swap",
                "my_position": my_pos,
                "opponent_position": opp_pos
            }
        
        elif context == ActionContext.QUEEN_ABILITY:
            if action_id < 4:
                return {
                    "action": "queen_peek", 
                    "target": "opponent",
                    "position": action_id
                }
            else:
                return {
                    "action": "queen_peek",
                    "target": "self", 
                    "position": action_id - 4
                }
        
        raise ValueError(f"Could not decode action {action_id} for context {context}")
    
    def create_action_mask(self, context: ActionContext, valid_actions: List[int], 
                          device: str = "cpu") -> torch.Tensor:
        """Create action mask for valid actions (1 for valid, 0 for invalid)"""
        context_size = self.get_action_size(context)
        mask = torch.zeros(context_size, device=device)
        for action_id in valid_actions:
            if 0 <= action_id < context_size:
                mask[action_id] = 1.0
        return mask


# Singleton instance
action_space = ContextualActionSpace() 