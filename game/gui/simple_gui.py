"""
Simple GUI for Dutch Cabo - No fancy graphics, just basic game state display
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, List
import threading
import time


class SimpleGameGUI:
    """En basit mümkün GUI - sadece oyun durumunu gösterir"""
    
    def __init__(self, title="Dutch Cabo Game"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")
        
        # Ana frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Oyun durumu
        self.setup_ui()
        
        # Güncelleme için
        self.is_running = False
        self.update_thread = None
        
    def setup_ui(self):
        """UI elemanlarını kur"""
        
        # Başlık
        title_label = tk.Label(self.main_frame, text="🎮 DUTCH CABO", 
                              font=("Arial", 20, "bold"), 
                              bg="#2c3e50", fg="#ecf0f1")
        title_label.pack(pady=10)
        
        # Oyun bilgileri frame
        info_frame = ttk.LabelFrame(self.main_frame, text="Game Info", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.turn_label = tk.Label(info_frame, text="Turn: 1", font=("Arial", 12))
        self.turn_label.pack(anchor=tk.W)
        
        self.current_player_label = tk.Label(info_frame, text="Current: -", 
                                           font=("Arial", 12, "bold"), fg="#e74c3c")
        self.current_player_label.pack(anchor=tk.W)
        
        self.dutch_label = tk.Label(info_frame, text="Dutch: No", font=("Arial", 12))
        self.dutch_label.pack(anchor=tk.W)
        
        # Deck ve Discard
        cards_frame = ttk.LabelFrame(self.main_frame, text="Cards", padding=10)
        cards_frame.pack(fill=tk.X, pady=5)
        
        deck_discard_frame = tk.Frame(cards_frame)
        deck_discard_frame.pack()
        
        # Deck
        deck_frame = tk.Frame(deck_discard_frame)
        deck_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(deck_frame, text="DECK", font=("Arial", 10, "bold")).pack()
        self.deck_label = tk.Label(deck_frame, text="[🂠]", 
                                  font=("Arial", 24), 
                                  bg="#27ae60", fg="white",
                                  width=4, height=2)
        self.deck_label.pack(pady=5)
        self.deck_size_label = tk.Label(deck_frame, text="52 cards", font=("Arial", 10))
        self.deck_size_label.pack()
        
        # Discard
        discard_frame = tk.Frame(deck_discard_frame)
        discard_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(discard_frame, text="DISCARD", font=("Arial", 10, "bold")).pack()
        self.discard_label = tk.Label(discard_frame, text="[?]", 
                                     font=("Arial", 24),
                                     bg="#e74c3c", fg="white", 
                                     width=4, height=2)
        self.discard_label.pack(pady=5)
        
        # Oyuncular frame
        players_frame = ttk.LabelFrame(self.main_frame, text="Players", padding=10)
        players_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollable frame for players
        canvas = tk.Canvas(players_frame)
        scrollbar = ttk.Scrollbar(players_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Oyuncu widget'ları
        self.player_widgets = {}
        
        # Status bar
        self.status_label = tk.Label(self.main_frame, text="Ready to start...", 
                                   font=("Arial", 10), 
                                   bg="#34495e", fg="#ecf0f1")
        self.status_label.pack(fill=tk.X, pady=5)
        
    def add_player(self, player_name: str, is_gym_player: bool = False):
        """Oyuncu ekle"""
        player_frame = ttk.LabelFrame(self.scrollable_frame, text=player_name, padding=5)
        player_frame.pack(fill=tk.X, pady=2)
        
        # Oyuncu bilgileri
        info_frame = tk.Frame(player_frame)
        info_frame.pack(fill=tk.X)
        
        # Sol taraf - Kartlar
        cards_frame = tk.Frame(info_frame)
        cards_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        hand_label = tk.Label(cards_frame, text="Hand:", font=("Arial", 10, "bold"))
        hand_label.pack(anchor=tk.W)
        
        # Kart representasyonları
        cards_display_frame = tk.Frame(cards_frame)
        cards_display_frame.pack(anchor=tk.W)
        
        card_widgets = []
        for i in range(4):
            card_btn = tk.Label(cards_display_frame, text="[?]", 
                               font=("Arial", 12), 
                               bg="#95a5a6", fg="white",
                               width=3, height=1, relief=tk.RAISED)
            card_btn.pack(side=tk.LEFT, padx=2)
            card_widgets.append(card_btn)
        
        # Sağ taraf - Skor ve durum
        status_frame = tk.Frame(info_frame)
        status_frame.pack(side=tk.RIGHT)
        
        score_label = tk.Label(status_frame, text="Score: ?", font=("Arial", 10))
        score_label.pack()
        
        hand_size_label = tk.Label(status_frame, text="Cards: 4", font=("Arial", 10))
        hand_size_label.pack()
        
        # Current player indicator
        current_indicator = tk.Label(status_frame, text="", 
                                   font=("Arial", 12, "bold"), fg="#e74c3c")
        current_indicator.pack()
        
        self.player_widgets[player_name] = {
            "frame": player_frame,
            "cards": card_widgets,
            "score": score_label,
            "hand_size": hand_size_label,
            "current_indicator": current_indicator,
            "is_gym": is_gym_player
        }
        
    def update_game_state(self, game_state: Dict[str, Any]):
        """Oyun durumunu güncelle"""
        try:
            # Turn info
            turn_count = game_state.get("turn_count", 0)
            self.turn_label.config(text=f"Turn: {turn_count}")
            
            # Current player
            current_player = game_state.get("current_player", "")
            self.current_player_label.config(text=f"Current: {current_player}")
            
            # Dutch status
            dutch_called = game_state.get("dutch_called", False)
            self.dutch_label.config(text=f"Dutch: {'YES!' if dutch_called else 'No'}")
            if dutch_called:
                self.dutch_label.config(fg="#e74c3c")
            else:
                self.dutch_label.config(fg="black")
            
            # Deck size
            deck_size = game_state.get("deck_size", 0)
            self.deck_size_label.config(text=f"{deck_size} cards")
            
            # Discard pile
            top_discard = game_state.get("top_discard")
            if top_discard:
                self.discard_label.config(text=f"[{top_discard}]")
            else:
                self.discard_label.config(text="[Empty]")
                
            # Update current player indicators
            for player_name, widgets in self.player_widgets.items():
                if player_name == current_player:
                    widgets["current_indicator"].config(text="← NOW", fg="#e74c3c")
                    widgets["frame"].config(style="Current.TLabelframe")
                else:
                    widgets["current_indicator"].config(text="")
                    widgets["frame"].config(style="TLabelframe")
                    
        except Exception as e:
            self.status_label.config(text=f"Update error: {e}")
    
    def update_player(self, player_name: str, player_data: Dict[str, Any]):
        """Oyuncu durumunu güncelle"""
        if player_name not in self.player_widgets:
            return
            
        widgets = self.player_widgets[player_name]
        
        try:
            # Hand cards
            hand = player_data.get("hand", [])
            known_cards = player_data.get("known_cards", [])
            
            for i, card_widget in enumerate(widgets["cards"]):
                if i < len(hand):
                    card = hand[i]
                    is_known = i < len(known_cards) and known_cards[i]
                    
                    if card is None:
                        # No card at this position
                        card_widget.config(text="[ ]", bg="#7f8c8d")
                    elif is_known:
                        # Known card - show it
                        if widgets["is_gym"]:
                            card_widget.config(text=f"[{card}]", bg="#2ecc71")
                        else:
                            card_widget.config(text="[K]", bg="#3498db")  # Known but hidden
                    else:
                        # Unknown card
                        card_widget.config(text="[?]", bg="#95a5a6")
                else:
                    card_widget.config(text="[ ]", bg="#7f8c8d")
            
            # Score
            score = player_data.get("score", 0)
            widgets["score"].config(text=f"Score: {score}")
            
            # Hand size
            hand_size = player_data.get("hand_size", 0)
            widgets["hand_size"].config(text=f"Cards: {hand_size}")
            
        except Exception as e:
            self.status_label.config(text=f"Player update error: {e}")
    
    def set_status(self, message: str):
        """Status mesajı"""
        self.status_label.config(text=message)
    
    def start_gui(self):
        """GUI'yi başlat"""
        self.is_running = True
        
        # Otomatik güncelleme thread'i
        def update_loop():
            while self.is_running:
                try:
                    self.root.update()
                    time.sleep(0.1)
                except:
                    break
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()
    
    def close(self):
        """GUI'yi kapat"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        self.root.quit()
        self.root.destroy()
    
    def show(self):
        """GUI'yi göster (non-blocking)"""
        self.root.deiconify()
        
    def hide(self):
        """GUI'yi gizle"""
        self.root.withdraw()


# Test için basit örnek
if __name__ == "__main__":
    gui = SimpleGameGUI()
    
    # Test oyuncuları ekle
    gui.add_player("GymAgent", is_gym_player=True)
    gui.add_player("SimpleAI_1")
    gui.add_player("SimpleAI_2")
    
    # Test güncellemesi
    gui.update_game_state({
        "turn_count": 5,
        "current_player": "GymAgent",
        "dutch_called": False,
        "deck_size": 30,
        "top_discard": "7♥"
    })
    
    # Test oyuncu güncellemesi
    gui.update_player("GymAgent", {
        "hand": ["7♥", "?", "K♠", None],
        "known_cards": [True, False, True, False],
        "score": 20,
        "hand_size": 3
    })
    
    gui.set_status("Game in progress...")
    gui.start_gui() 