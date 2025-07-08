"""
DQRN (Deep Q-Recurrent Network) Multi-Head Architecture for Dutch Cabo

Shared feature extraction + LSTM + Multiple action heads for different contexts.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, Any
import numpy as np

from .action_space import ActionContext, action_space
from .state_space import state_space


class DQRNMultiHead(nn.Module):
    """
    Deep Q-Recurrent Network with Multiple Heads for contextual actions.
    
    Architecture:
    1. Shared feature extraction layers
    2. LSTM layer for temporal memory
    3. Multiple action heads for different contexts
    4. Value head for state value estimation
    """
    
    def __init__(self, 
                 state_size: int,
                 hidden_size: int = 256,
                 lstm_hidden_size: int = 128,
                 num_lstm_layers: int = 1,
                 dropout: float = 0.1,
                 device: str = "cpu"):
        super(DQRNMultiHead, self).__init__()
        
        self.state_size = state_size
        self.hidden_size = hidden_size
        self.lstm_hidden_size = lstm_hidden_size
        self.num_lstm_layers = num_lstm_layers
        self.device = device
        
        # Shared feature extraction layers
        self.shared_layers = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, lstm_hidden_size),
            nn.ReLU()
        )
        
        # LSTM for temporal memory
        self.lstm = nn.LSTM(
            input_size=lstm_hidden_size,
            hidden_size=lstm_hidden_size,
            num_layers=num_lstm_layers,
            batch_first=True,
            dropout=dropout if num_lstm_layers > 1 else 0
        )
        
        # Action heads for different contexts
        self.action_heads = nn.ModuleDict({
            ActionContext.DRAW_SOURCE.value: nn.Sequential(
                nn.Linear(lstm_hidden_size, 64),
                nn.ReLU(),
                nn.Linear(64, action_space.get_action_size(ActionContext.DRAW_SOURCE))
            ),
            ActionContext.MAIN_ACTION.value: nn.Sequential(
                nn.Linear(lstm_hidden_size, 128),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, action_space.get_action_size(ActionContext.MAIN_ACTION))
            ),
            ActionContext.JACK_ABILITY.value: nn.Sequential(
                nn.Linear(lstm_hidden_size, 128),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, action_space.get_action_size(ActionContext.JACK_ABILITY))
            ),
            ActionContext.QUEEN_ABILITY.value: nn.Sequential(
                nn.Linear(lstm_hidden_size, 64),
                nn.ReLU(),
                nn.Linear(64, action_space.get_action_size(ActionContext.QUEEN_ABILITY))
            )
        })
        
        # Value head for state value estimation (used in some RL algorithms)
        self.value_head = nn.Sequential(
            nn.Linear(lstm_hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # Move to device
        self.to(device)
        
        # Initialize weights
        self.apply(self._init_weights)
        
        print(f"DQRN Multi-Head Network created:")
        print(f"  State size: {state_size}")
        print(f"  Hidden size: {hidden_size}")
        print(f"  LSTM hidden size: {lstm_hidden_size}")
        print(f"  LSTM layers: {num_lstm_layers}")
        print(f"  Device: {device}")
        print(f"  Action heads: {list(self.action_heads.keys())}")
        self._print_parameter_count()
    
    def _init_weights(self, module):
        """Initialize network weights"""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                torch.nn.init.constant_(module.bias, 0.0)
        elif isinstance(module, nn.LSTM):
            for name, param in module.named_parameters():
                if 'weight' in name:
                    torch.nn.init.xavier_uniform_(param)
                elif 'bias' in name:
                    torch.nn.init.constant_(param, 0.0)
    
    def _print_parameter_count(self):
        """Print number of parameters in each component"""
        total_params = 0
        print("  Parameter counts:")
        
        shared_params = sum(p.numel() for p in self.shared_layers.parameters())
        print(f"    Shared layers: {shared_params:,}")
        total_params += shared_params
        
        lstm_params = sum(p.numel() for p in self.lstm.parameters())
        print(f"    LSTM: {lstm_params:,}")
        total_params += lstm_params
        
        for name, head in self.action_heads.items():
            head_params = sum(p.numel() for p in head.parameters())
            print(f"    {name} head: {head_params:,}")
            total_params += head_params
        
        value_params = sum(p.numel() for p in self.value_head.parameters())
        print(f"    Value head: {value_params:,}")
        total_params += value_params
        
        print(f"  Total parameters: {total_params:,}")
    
    def init_hidden_state(self, batch_size: int = 1) -> Tuple[torch.Tensor, torch.Tensor]:
        """Initialize LSTM hidden state"""
        h0 = torch.zeros(self.num_lstm_layers, batch_size, self.lstm_hidden_size, device=self.device)
        c0 = torch.zeros(self.num_lstm_layers, batch_size, self.lstm_hidden_size, device=self.device)
        return h0, c0
    
    def forward(self, 
                state: torch.Tensor, 
                hidden_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
                context: Optional[ActionContext] = None) -> Dict[str, Any]:
        """
        Forward pass through the network.
        
        Args:
            state: State tensor of shape (batch_size, seq_len, state_size) or (batch_size, state_size)
            hidden_state: LSTM hidden state tuple (h, c)
            context: Specific action context to compute (if None, computes all)
            
        Returns:
            Dictionary containing:
            - q_values: Q-values for specified context(s)
            - value: State value estimate
            - hidden_state: Updated LSTM hidden state
        """
        batch_size = state.shape[0]
        
        # Handle different input shapes
        if len(state.shape) == 2:
            # Single timestep: (batch_size, state_size) -> (batch_size, 1, state_size)
            state = state.unsqueeze(1)
            single_step = True
        else:
            # Sequential: (batch_size, seq_len, state_size)
            single_step = False
        
        seq_len = state.shape[1]
        
        # Initialize hidden state if not provided
        if hidden_state is None:
            hidden_state = self.init_hidden_state(batch_size)
        
        # Shared feature extraction
        # Reshape for processing: (batch_size * seq_len, state_size)
        state_flat = state.reshape(-1, self.state_size)
        features = self.shared_layers(state_flat)
        
        # Reshape back: (batch_size, seq_len, lstm_hidden_size)
        features = features.reshape(batch_size, seq_len, self.lstm_hidden_size)
        
        # LSTM forward pass
        lstm_out, new_hidden_state = self.lstm(features, hidden_state)
        
        # Use last timestep output for Q-value computation
        if single_step:
            lstm_features = lstm_out.squeeze(1)  # (batch_size, lstm_hidden_size)
        else:
            lstm_features = lstm_out[:, -1, :]   # (batch_size, lstm_hidden_size)
        
        result = {
            "hidden_state": new_hidden_state,
            "lstm_features": lstm_features  # For debugging/visualization
        }
        
        # Compute Q-values for specified context(s)
        if context is not None:
            # Single context
            if context.value in self.action_heads:
                q_values = self.action_heads[context.value](lstm_features)
                result["q_values"] = q_values
            else:
                raise ValueError(f"Unknown context: {context}")
        else:
            # All contexts
            q_values = {}
            for ctx_name, head in self.action_heads.items():
                q_values[ctx_name] = head(lstm_features)
            result["q_values"] = q_values
        
        # Compute state value
        result["value"] = self.value_head(lstm_features)
        
        return result
    
    def get_action(self, 
                   state: torch.Tensor,
                   context: ActionContext,
                   hidden_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
                   valid_actions: Optional[torch.Tensor] = None,
                   epsilon: float = 0.0) -> Tuple[int, Tuple[torch.Tensor, torch.Tensor], Dict]:
        """
        Get action using epsilon-greedy policy.
        
        Args:
            state: Current state tensor
            context: Action context
            hidden_state: LSTM hidden state
            valid_actions: Mask of valid actions (1 for valid, 0 for invalid)
            epsilon: Exploration probability
            
        Returns:
            (action_id, new_hidden_state, debug_info)
        """
        self.eval()
        with torch.no_grad():
            # Forward pass
            output = self.forward(state, hidden_state, context)
            q_values = output["q_values"]
            new_hidden_state = output["hidden_state"]
            
            # Apply action mask if provided
            if valid_actions is not None:
                # Set invalid actions to very negative values
                masked_q_values = q_values.clone()
                # Handle batch dimension: expand valid_actions to match q_values shape
                if len(valid_actions.shape) == 1 and len(q_values.shape) == 2:
                    valid_actions = valid_actions.unsqueeze(0).expand_as(q_values)
                masked_q_values[valid_actions == 0] = -1e8
            else:
                masked_q_values = q_values
            
            # Epsilon-greedy action selection
            if torch.rand(1).item() < epsilon:
                # Random action from valid actions
                if valid_actions is not None:
                    valid_indices = torch.where(valid_actions == 1)[0]
                    if len(valid_indices) > 0:
                        action = valid_indices[torch.randint(len(valid_indices), (1,))].item()
                    else:
                        action = 0  # Fallback
                else:
                    action = torch.randint(q_values.shape[-1], (1,)).item()
            else:
                # Greedy action
                action = masked_q_values.argmax(dim=-1).item()
            
            debug_info = {
                "q_values": q_values.squeeze(0).cpu().numpy(),
                "selected_q_value": q_values[0, action].item(),
                "value": output["value"].item(),
                "epsilon": epsilon,
                "valid_actions": valid_actions.cpu().numpy() if valid_actions is not None else None
            }
            
            return action, new_hidden_state, debug_info
    
    def update_target_network(self, target_network: 'DQRNMultiHead', tau: float = 0.005):
        """Soft update of target network parameters"""
        for target_param, local_param in zip(target_network.parameters(), self.parameters()):
            target_param.data.copy_(tau * local_param.data + (1.0 - tau) * target_param.data)
    
    def save_checkpoint(self, filepath: str, episode: int = 0, optimizer_state: Optional[Dict] = None):
        """Save model checkpoint"""
        checkpoint = {
            'episode': episode,
            'model_state_dict': self.state_dict(),
            'model_config': {
                'state_size': self.state_size,
                'hidden_size': self.hidden_size,
                'lstm_hidden_size': self.lstm_hidden_size,
                'num_lstm_layers': self.num_lstm_layers,
                'device': self.device
            }
        }
        
        if optimizer_state is not None:
            checkpoint['optimizer_state_dict'] = optimizer_state
        
        torch.save(checkpoint, filepath)
        print(f"Model checkpoint saved: {filepath}")
    
    @classmethod
    def load_checkpoint(cls, filepath: str, device: str = "cpu") -> Tuple['DQRNMultiHead', Dict]:
        """Load model from checkpoint"""
        checkpoint = torch.load(filepath, map_location=device)
        
        # Create model with saved config
        config = checkpoint['model_config']
        model = cls(
            state_size=config['state_size'],
            hidden_size=config['hidden_size'],
            lstm_hidden_size=config['lstm_hidden_size'],
            num_lstm_layers=config['num_lstm_layers'],
            device=device
        )
        
        # Load weights
        model.load_state_dict(checkpoint['model_state_dict'])
        
        print(f"Model loaded from checkpoint: {filepath}")
        print(f"Episode: {checkpoint.get('episode', 'unknown')}")
        
        return model, checkpoint


def create_dqrn_network(device: str = "cpu", **kwargs) -> DQRNMultiHead:
    """
    Factory function to create DQRN network with default parameters.
    
    Args:
        device: Device to create network on
        **kwargs: Additional parameters for network creation
        
    Returns:
        Initialized DQRN network
    """
    default_params = {
        'hidden_size': 256,
        'lstm_hidden_size': 128,
        'num_lstm_layers': 1,
        'dropout': 0.1
    }
    
    # Override defaults with provided kwargs
    default_params.update(kwargs)
    
    return DQRNMultiHead(
        state_size=state_space.get_state_size(),
        device=device,
        **default_params
    ) 