"""
PPO (Proximal Policy Optimization) Module for Dutch Cabo

This module contains all PPO-related components:
- Training scripts and configurations
- Trained model player implementation  
- Model evaluation and testing tools
"""

try:
    from .ppo_player import PPOPlayer
    __all__ = ["PPOPlayer"]
except ImportError:
    # Handle case where dependencies are not available
    __all__ = [] 