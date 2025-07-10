# Dutch Cabo Game - Test Suite

Bu test paketi Dutch Cabo oyununun game engine'i için kapsamlı testler içermektedir.

## Test Özellikleri

### Sabit Deck (Fixed Deck) Sistemi

Game engine'e test amaçlı sabit deck verme özelliği eklenmiştir:

```python
# Normal kullanım (rastgele deck)
engine = GameEngine([player1, player2])

# Test için sabit deck
test_deck = create_simple_test_deck()
engine = GameEngine([player1, player2], fixed_deck=test_deck)
```

### Test Modülleri

#### 1. `test_game_engine.py`
- **GameEngine temel işlevselliği**
- Oyun başlatma ve setup
- Kart dağıtımı
- Oyuncu sıra yönetimi
- Oyun durumu takibi

#### 2. `test_card_mechanics.py`
- **Kart değişimi ve temel mekanikler**
- Kart swap işlemleri
- Kart çekme/atma
- El boyutu takibi
- Skor hesaplama
- Discard pile matching logic

#### 3. `test_special_abilities.py`
- **Özel kart yetenekleri**
- Jack swap yeteneği (iki farklı pozisyon seçimi)
- Queen peek yeteneği
- Red King (0 puan) vs Black King (10 puan) 
- Discard pile matching özel kartlardan sonra

#### 4. `test_matching_logic.py`
- **Discard pile matching detaylı testleri**
- Sadece bilinen kartların eşleşme için sunulması
- Bilinmeyen kartların eşleşme dışı kalması
- Kart öğrendikten sonra eşleşme imkanı
- Edge case'ler

### Test Utilities

#### MockPlayer
Test amaçlı sahte oyuncu sınıfı:
- Önceden tanımlı eylemler yapabilir
- Action queues (eylem kuyrukları)
- Peek, swap, draw kararları için önceden ayarlanabilir

#### Test Deck Creation
Özel test deck'leri:
- `create_simple_test_deck()`: Bilinen kartlarla basit test deck'i
- `create_test_deck()`: Daha karmaşık senaryolar için

## Çalıştırma

### Tüm testleri çalıştır:
```bash
python test/run_tests.py
```

### Tek modül test et:
```bash
python -m unittest test.test_game_engine -v
```

### Tek test et:
```bash
python -m unittest test.test_game_engine.TestGameEngine.test_engine_initialization -v
```

### Debug testler:
```bash
python -m unittest test.test_debug -v
```

## Test Edilenler

### ✅ Kart Dağıtımı
- Fixed deck doğru sırayla dağıtılır
- Initial peek'ler doğru çalışır
- Discard pile doğru başlatılır

### ✅ Jack Swap Yeteneği
- İki farklı pozisyon seçimi (verilen vs alınan)
- Bilgi güncellemeleri (swap yapan oyuncu aldığını bilir)
- Opponent bilgi kaybı

### ✅ Queen Peek Yeteneği  
- Kendi kartına peek
- Opponent kartına peek
- Bilgi güncellemeleri

### ✅ Discard Pile Matching
- **SADECE BİLİNEN KARTLAR** eşleşme için sunulur
- Bilinmeyen kartlar aynı değerde olsa bile sunulmaz
- Kart öğrendikten sonra eşleşme imkanı doğar
- Edge case'ler (None, empty pile)

### ✅ Scoring Sistemi
- Red Kings (♥13, ♦13) = 0 puan
- Black Kings (♠13, ♣13) = 10 puan
- Jack, Queen = 10 puan
- Ace = 1 puan

### ✅ Kart Swap Mekanikleri
- Drawn card swap
- Hand size tracking
- Knowledge updates

## Önemli Test Bulguları

### Discard Pile Matching Logic ✅ DOĞRU
Kullanıcının endişe ettiği "bilinmeyen kartların matching'e sunulması" problemi **mevcut değil**. 

Test sonuçları:
- `get_discard_pile_matches()` metodu sadece `known_cards[i] == True` olan kartları döndürür
- Bilinmeyen kartlar asla eşleşme listesinde yer almaz
- Sistem tamamen doğru çalışıyor

### Deck Sıralaması
Kartlar deck'in **sonundan** çekiliyor (`deck.pop()`), bu nedenle:
- Test deck'leri ters sırada oluşturulmalı
- Dealing: son 8 kart + 1 discard
- Drawing: sondan başa doğru

## Geliştirici Notları

### Test Debug İçin
`test_debug.py` modülü game engine'in nasıl çalıştığını anlamak için console output verir.

### Test Data
- Predictable, deterministic test results
- Fixed deck usage prevents randomness
- Easy to verify expected behavior

### Linter Hatalar
Bazı linter hatalar mevcut (özellikle GameEngine'de BayesPlayer referansları) ama testler çalışıyor. 