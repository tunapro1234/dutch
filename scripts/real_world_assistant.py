#!/usr/bin/env python3
"""
Dutch Cabo Real World Assistant

Bu mode gerçek kartlarla oynarken AI'dan yardım almanızı sağlar.
- Elinizdeki kartları girin
- Rakiplerin hareketlerini kaydedin  
- AI'dan stratejik tavsiye alın
- Oyun durumunu takip edin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional, Dict, Any
from game.engine import Card, Suit
from players.bayes.smart_bayes import SmartBayesPlayer
from players.bayes_player import BayesPlayer


class RealWorldAssistant:
    """Gerçek dünya oyun asistanı"""
    
    def __init__(self):
        # AI advisor (en akıllı olanını kullan)
        self.ai_advisor = SmartBayesPlayer("AIAdvisor")
        
        # Oyun durumu
        self.my_hand = [None] * 4
        self.my_known_cards = [False] * 4
        self.opponents = {}  # name -> {"hand_size": int, "known_info": {}}
        self.discard_pile = []
        self.turn_count = 0
        self.dutch_called = False
        
        # Kart çevirme yardımcısı
        self.card_map = self._create_card_map()
        
    def _create_card_map(self) -> Dict[str, Card]:
        """Kart girişi için mapping oluştur"""
        card_map = {}
        
        suits = {"h": Suit.HEARTS, "d": Suit.DIAMONDS, "c": Suit.CLUBS, "s": Suit.SPADES}
        values = {"a": 1, "j": 11, "q": 12, "k": 13}
        
        for suit_char, suit in suits.items():
            for value in range(1, 14):
                if value == 1:
                    card_map[f"a{suit_char}"] = Card(suit, 1)
                elif value == 11:
                    card_map[f"j{suit_char}"] = Card(suit, 11)
                elif value == 12:
                    card_map[f"q{suit_char}"] = Card(suit, 12)
                elif value == 13:
                    card_map[f"k{suit_char}"] = Card(suit, 13)
                else:
                    card_map[f"{value}{suit_char}"] = Card(suit, value)
        
        return card_map
    
    def parse_card(self, card_input: str) -> Optional[Card]:
        """Kart girişini parse et (örn: 7h, kd, as)"""
        card_input = card_input.lower().strip()
        return self.card_map.get(card_input)
    
    def start_game(self):
        """Oyunu başlat"""
        print("🎮 Dutch Cabo Real World Assistant")
        print("=" * 50)
        print("Gerçek kartlarla oynarken AI'dan yardım alın!")
        print()
        print("📋 Kart giriş formatı:")
        print("  - Sayılar: 2h, 7d, 10c, 9s")
        print("  - Özel kartlar: ah, jd, qc, ks")
        print("  - Renkler: h=♥, d=♦, c=♣, s=♠")
        print()
        
        # Başlangıç setup'ı
        self._setup_game()
        
        # Ana oyun döngüsü
        self._game_loop()
    
    def _setup_game(self):
        """Oyun başlangıç kurulumu"""
        print("🎯 Oyun Kurulumu")
        print("-" * 30)
        
        # Rakip sayısı
        while True:
            try:
                num_opponents = int(input("Kaç rakip var? (1-3): "))
                if 1 <= num_opponents <= 3:
                    break
                print("1-3 arası bir sayı girin")
            except ValueError:
                print("Geçerli bir sayı girin")
        
        # Rakip isimleri
        for i in range(num_opponents):
            name = input(f"Rakip {i+1} ismi: ").strip()
            if not name:
                name = f"Opponent{i+1}"
            self.opponents[name] = {"hand_size": 4, "known_info": {}}
        
        # Kendi elimizi kurala
        print("\n🃏 Elinizi kurun (4 kart)")
        print("Başlangıçta 1 kartınızı görebilirsiniz")
        
        for i in range(4):
            self.my_hand[i] = None  # Başlangıçta bilinmeyen
            self.my_known_cards[i] = False
        
        # İlk peek kartı
        while True:
            try:
                peek_pos = int(input("Hangi pozisyona bakacaksınız? (0-3): "))
                if 0 <= peek_pos <= 3:
                    break
                print("0-3 arası bir pozisyon girin")
            except ValueError:
                print("Geçerli bir sayı girin")
        
        card_input = input(f"Pozisyon {peek_pos}'daki kart nedir? (örn: 7h): ")
        card = self.parse_card(card_input)
        if card:
            self.my_hand[peek_pos] = card
            self.my_known_cards[peek_pos] = True
            self.ai_advisor.hand[peek_pos] = card
            self.ai_advisor.known_cards[peek_pos] = True
        
        # Atık yığını başlangıcı
        discard_input = input("Atık yığını üstündeki kart nedir? (örn: 5d): ")
        discard_card = self.parse_card(discard_input)
        if discard_card:
            self.discard_pile.append(discard_card)
            self.ai_advisor.observe_card(discard_card)
        
        print("\n✅ Oyun kurulumu tamamlandı!")
        self._show_game_state()
    
    def _game_loop(self):
        """Ana oyun döngüsü"""
        while True:
            print("\n" + "=" * 50)
            print(f"🎯 Tur {self.turn_count + 1}")
            print("=" * 50)
            
            choice = self._get_turn_choice()
            
            if choice == "1":
                self._my_turn()
            elif choice == "2":
                self._opponent_turn()
            elif choice == "3":
                self._show_game_state()
            elif choice == "4":
                self._get_ai_advice()
            elif choice == "5":
                self._update_my_hand()
            elif choice == "6":
                print("👋 Oyunu sonlandırıyorum...")
                break
            
            self.turn_count += 1
    
    def _get_turn_choice(self) -> str:
        """Tur seçeneklerini göster"""
        print("\n📋 Ne yapmak istiyorsunuz?")
        print("1. 🎯 Benim sıram")
        print("2. 👥 Rakip oynadı")
        print("3. 📊 Oyun durumunu göster")
        print("4. 🤖 AI tavsiyesi al")
        print("5. 🃏 Elimi güncelle")
        print("6. 🚪 Çıkış")
        
        while True:
            choice = input("\nSeçiminiz (1-6): ").strip()
            if choice in ["1", "2", "3", "4", "5", "6"]:
                return choice
            print("1-6 arası bir seçenek girin")
    
    def _my_turn(self):
        """Kullanıcının sırası"""
        print("\n🎯 Sizin Sıranız")
        print("-" * 20)
        
        # Eşleşen kartları kontrol et
        if self.discard_pile:
            self._check_matching_cards("before_draw")
        
        # Kart çekme
        print("\n🎴 Kart Çekme")
        draw_choice = input("Nereden çekeceksiniz? (d)esk / (a)tık: ").lower()
        
        card_input = input("Çektiğiniz kart nedir? (örn: 9h): ")
        drawn_card = self.parse_card(card_input)
        
        if drawn_card:
            self.ai_advisor.observe_card(drawn_card)
            
            # AI'dan tavsiye al
            advice = self._get_action_advice(drawn_card)
            print(f"\n🤖 AI Tavsiyesi: {advice}")
            
            # Kullanıcı aksiyonunu al
            action = input("\nNe yaptınız? (d)iscard / (s)wap / (a)bility / dutch: ").lower()
            
            self._handle_my_action(action, drawn_card)
        
        # Eşleşen kartları tekrar kontrol et
        if self.discard_pile:
            self._check_matching_cards("after_turn")
        
        self._show_game_state()
    
    def _check_matching_cards(self, timing: str):
        """Eşleşen kartları kontrol et"""
        if not self.discard_pile:
            return
            
        top_card = self.discard_pile[-1]
        matches = []
        
        for i in range(4):
            if (self.my_hand[i] is not None and 
                self.my_known_cards[i] and 
                self.my_hand[i].value == top_card.value):
                matches.append((i, self.my_hand[i]))
        
        if matches:
            print(f"\n🎯 {timing.upper()}: Eşleşen kartlar bulundu!")
            for pos, card in matches:
                print(f"  Pozisyon {pos}: {card}")
            
            discard_input = input("Hangi pozisyonları atmak istiyorsuniz? (örn: 0,2 veya boş): ")
            if discard_input.strip():
                try:
                    positions = [int(x.strip()) for x in discard_input.split(",")]
                    for pos in positions:
                        if 0 <= pos <= 3 and self.my_hand[pos] is not None:
                            card = self.my_hand[pos]
                            print(f"  ✅ {card} atıldı (pozisyon {pos})")
                            self.my_hand[pos] = None
                            self.my_known_cards[pos] = False
                            self.discard_pile.append(card)
                            self.ai_advisor.hand[pos] = None
                            self.ai_advisor.known_cards[pos] = False
                except ValueError:
                    print("Geçersiz pozisyon girişi")
    
    def _get_action_advice(self, drawn_card: Card) -> str:
        """Çekilen kart için AI tavsiyesi al"""
        # AI'ın mevcut durumunu güncelle
        self._sync_ai_state()
        
        # Game state simüle et
        game_state = self._create_game_state()
        
        # AI'dan tavsiye al
        action = self.ai_advisor.choose_action(drawn_card, game_state)
        
        advice_text = ""
        if action["action"] == "discard":
            advice_text = f"🗑️ DISCARD - {drawn_card} kartını at (el değişmez)"
        elif action["action"] == "swap":
            pos = action["position"]
            current_card = self.my_hand[pos] if pos < len(self.my_hand) else None
            advice_text = f"🔄 SWAP - Pozisyon {pos}'daki kartla değiştir"
            if current_card and self.my_known_cards[pos]:
                advice_text += f" (mevcut: {current_card})"
        elif action["action"] == "use_ability":
            if drawn_card.is_jack():
                advice_text = f"👑 JACK - Rakiple kart değiştir ({drawn_card})"
            elif drawn_card.is_queen():
                advice_text = f"👸 QUEEN - Bir karta bak ({drawn_card})"
        elif action["action"] == "call_dutch":
            advice_text = f"🇳🇱 DUTCH - Oyunu bitir! (düşük puanın var)"
        
        return advice_text
    
    def _handle_my_action(self, action: str, drawn_card: Card):
        """Kullanıcının aksiyonunu işle"""
        if action in ["d", "discard"]:
            self.discard_pile.append(drawn_card)
            print(f"✅ {drawn_card} atıldı")
            
        elif action in ["s", "swap"]:
            while True:
                try:
                    pos = int(input("Hangi pozisyonla değiştirdiniz? (0-3): "))
                    if 0 <= pos <= 3:
                        break
                    print("0-3 arası bir pozisyon girin")
                except ValueError:
                    print("Geçerli bir sayı girin")
            
            old_card = self.my_hand[pos]
            self.my_hand[pos] = drawn_card
            self.my_known_cards[pos] = True
            
            # AI state'i güncelle
            self.ai_advisor.hand[pos] = drawn_card
            self.ai_advisor.known_cards[pos] = True
            
            if old_card:
                self.discard_pile.append(old_card)
                print(f"✅ Pozisyon {pos}: {old_card} → {drawn_card}")
            
        elif action in ["a", "ability"]:
            self._handle_special_ability(drawn_card)
            self.discard_pile.append(drawn_card)
            
        elif action == "dutch":
            self.dutch_called = True
            self.discard_pile.append(drawn_card)
            print("🇳🇱 DUTCH çağrıldı! Oyun bitecek!")
    
    def _handle_special_ability(self, card: Card):
        """Özel yetenek kullanımını işle"""
        if card.is_jack():
            print("👑 JACK: Rakiple kart değiştirme")
            opponent_name = input("Hangi rakiple değiştirdiniz?: ")
            if opponent_name in self.opponents:
                self.opponents[opponent_name]["hand_size"] = max(0, self.opponents[opponent_name]["hand_size"])
                print(f"✅ {opponent_name} ile kart değiştirildi")
            
        elif card.is_queen():
            print("👸 QUEEN: Karta bakma")
            target = input("Kime baktınız? (self/opponent name): ")
            if target == "self":
                while True:
                    try:
                        pos = int(input("Hangi pozisyonunuza baktınız? (0-3): "))
                        if 0 <= pos <= 3:
                            break
                    except ValueError:
                        continue
                
                card_input = input(f"Pozisyon {pos}'daki kart nedir?: ")
                card = self.parse_card(card_input)
                if card:
                    self.my_hand[pos] = card
                    self.my_known_cards[pos] = True
                    self.ai_advisor.hand[pos] = card
                    self.ai_advisor.known_cards[pos] = True
                    print(f"✅ Pozisyon {pos}: {card} öğrenildi")
    
    def _opponent_turn(self):
        """Rakip sırası"""
        print("\n👥 Rakip Sırası")
        print("-" * 20)
        
        # Rakip seç
        print("Rakipler:")
        for i, name in enumerate(self.opponents.keys()):
            print(f"{i+1}. {name}")
        
        while True:
            try:
                choice = int(input("Hangi rakip oynadı? (numara): ")) - 1
                opponent_names = list(self.opponents.keys())
                if 0 <= choice < len(opponent_names):
                    opponent_name = opponent_names[choice]
                    break
            except ValueError:
                continue
        
        print(f"\n🎯 {opponent_name} sırası")
        
        # Rakibin aksiyonu
        action = input("Ne yaptı? (d)raw/(s)wap/(a)bility/dutch: ").lower()
        
        if action in ["d", "draw"]:
            card_input = input("Hangi kartı çekti/attı? (örn: 8h): ")
            card = self.parse_card(card_input)
            if card:
                self.discard_pile.append(card)
                self.ai_advisor.observe_card(card)
                print(f"✅ {opponent_name} {card} attı")
                
        elif action in ["s", "swap"]:
            print(f"✅ {opponent_name} kart değiştirdi")
            
        elif action in ["a", "ability"]:
            ability_type = input("Hangi yetenek? (j)ack/(q)ueen: ").lower()
            if ability_type == "j":
                print(f"✅ {opponent_name} Jack kullandı (kart değişimi)")
            elif ability_type == "q":
                print(f"✅ {opponent_name} Queen kullandı (karta bakma)")
                
        elif action == "dutch":
            print(f"🇳🇱 {opponent_name} DUTCH çağırdı!")
            self.dutch_called = True
    
    def _show_game_state(self):
        """Oyun durumunu göster"""
        print("\n📊 Oyun Durumu")
        print("=" * 30)
        
        # Kendi elim
        print("🃏 Elim:")
        hand_display = []
        total_known_score = 0
        
        for i in range(4):
            if self.my_hand[i] is None:
                hand_display.append("[ ]")
            elif self.my_known_cards[i]:
                card = self.my_hand[i]
                hand_display.append(f"[{card}]")
                total_known_score += card.get_score_value()
            else:
                hand_display.append("[?]")
        
        print(f"  Pozisyonlar: {' '.join(hand_display)}")
        print(f"  Bilinen puan: {total_known_score}")
        print(f"  El boyutu: {sum(1 for card in self.my_hand if card is not None)}")
        
        # Rakipler
        print("\n👥 Rakipler:")
        for name, info in self.opponents.items():
            print(f"  {name}: {info['hand_size']} kart")
        
        # Atık yığını
        if self.discard_pile:
            print(f"\n🗑️ Atık yığını üstü: {self.discard_pile[-1]}")
        
        # Oyun durumu
        if self.dutch_called:
            print("\n🇳🇱 DUTCH çağrıldı - Oyun bitme aşamasında!")
    
    def _get_ai_advice(self):
        """Genel AI tavsiyesi al"""
        print("\n🤖 AI Stratejik Tavsiye")
        print("-" * 30)
        
        self._sync_ai_state()
        
        # Mevcut durum analizi
        known_score = sum(card.get_score_value() for i, card in enumerate(self.my_hand) 
                         if card is not None and self.my_known_cards[i])
        unknown_count = sum(1 for i in range(4) if self.my_hand[i] is not None and not self.my_known_cards[i])
        
        print(f"📊 Durum Analizi:")
        print(f"  Bilinen puan: {known_score}")
        print(f"  Bilinmeyen kart: {unknown_count}")
        
        # AI tavsiyesi
        if unknown_count > 0:
            print(f"💡 Tavsiye: Bilinmeyen kartları öğrenmeye odaklan")
        elif known_score <= 5:
            print(f"💡 Tavsiye: Çok iyi durumdасın! Dutch çağırmayı düşün")
        elif known_score <= 10:
            print(f"💡 Tavsiye: İyi durumdасın, yüksek kartları değiştir")
        else:
            print(f"💡 Tavsiye: Yüksek kartları acilen değiştirmen gerekiyor")
    
    def _update_my_hand(self):
        """El durumunu güncelle"""
        print("\n🃏 El Güncelleme")
        print("-" * 20)
        
        for i in range(4):
            current = self.my_hand[i]
            known = self.my_known_cards[i]
            
            if current is None:
                status = "Boş"
            elif known:
                status = f"Bilinen: {current}"
            else:
                status = "Bilinmeyen"
            
            print(f"Pozisyon {i}: {status}")
            
            update = input(f"Pozisyon {i}'ı güncellemek ister misiniz? (y/n): ").lower()
            if update == "y":
                card_input = input("Yeni kart (boş için 'none'): ")
                if card_input.lower() == "none":
                    self.my_hand[i] = None
                    self.my_known_cards[i] = False
                    self.ai_advisor.hand[i] = None
                    self.ai_advisor.known_cards[i] = False
                else:
                    card = self.parse_card(card_input)
                    if card:
                        self.my_hand[i] = card
                        self.my_known_cards[i] = True
                        self.ai_advisor.hand[i] = card
                        self.ai_advisor.known_cards[i] = True
    
    def _sync_ai_state(self):
        """AI durumunu senkronize et"""
        for i in range(4):
            self.ai_advisor.hand[i] = self.my_hand[i]
            self.ai_advisor.known_cards[i] = self.my_known_cards[i]
    
    def _create_game_state(self) -> Dict[str, Any]:
        """Game state simüle et"""
        players_info = []
        for name, info in self.opponents.items():
            players_info.append({
                "name": name,
                "hand_size": info["hand_size"],
                "known_cards": 0
            })
        
        return {
            "turn_count": self.turn_count,
            "current_player": "AIAdvisor",
            "player_hand_sizes": {name: info["hand_size"] for name, info in self.opponents.items()},
            "top_discard": self.discard_pile[-1] if self.discard_pile else None,
            "deck_size": 40,  # Tahmini
            "players": players_info,
            "dutch_called": self.dutch_called,
            "dutch_caller": None,
            "final_round": self.dutch_called
        }


def main():
    """Ana fonksiyon"""
    assistant = RealWorldAssistant()
    try:
        assistant.start_game()
    except KeyboardInterrupt:
        print("\n\n👋 Oyun sonlandırıldı!")
    except Exception as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    main() 