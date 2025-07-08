# DQRN Multi-Head Network Architecture

dutch cabo için özel olarak tasarlanan bu network aslında oldukça düşünülmüş bir yapıya sahip. normal bir deep q network'ten farklı olarak burada oyunun farklı durumlarına özel kafa yapıları var ve her biri kendi alanında uzmanlaşıyor.

## temel tasarım felsefesi

oyunu analiz ederken fark ettik ki dutch cabo'da aslında çok farklı türde kararlar veriyoruz. mesela kart çekerken "deck'ten mi discard pile'dan mı çekeyim" sorusu ile "jack kullanırken hangi pozisyonu seçeyim" sorusu tamamen farklı şeyler. birincisinde sadece 2 seçenek var ama ikincisinde 16 tane olası hareket var. aynı network'ün hem bu basit kararı hem de karmaşık olanı eşit derecede iyi öğrenmesini beklemek biraz mantıksız geldi.

bu yüzden "contextual action spaces" diye bir kavram geliştirdik. her oyun durumu için farklı action head'ler kullanıyoruz. draw_source için küçük bir head yeterli çünkü sadece 2 seçenek var. ama jack_ability için çok daha büyük bir head gerekli çünkü 4x4=16 farklı pozisyon kombinasyonu var.

## network mimarisi detayları

network'ün kalbi shared layers dediğimiz kısım. burada 3 tane linear layer var (49->256->256->256) ve bunlar oyunun genel state'ini anlamaya çalışıyor. her kartın değeri ne, hangi kartları biliyoruz, rakip nasıl oynuyor gibi temel bilgileri burada işliyoruz. activation function olarak ReLU kullandık çünkü gradient flow için en stabil seçenek.

shared layers'dan sonra işler ilginçleşiyor. state representation bir de LSTM'den geçiyor. bu çok önemli çünkü dutch cabo'da sequence önemli. mesela rakip sürekli düşük kartları discard ediyorsa, bu onun stratejisi hakkında bilgi veriyor. ya da biz jack kullandıktan sonra hangi pozisyonları peek ettiğimizi hatırlamak gerekiyor. LSTM hidden state 128 boyutunda ve tek layer kullandık - daha fazla layer denedik ama overfitting yapmaya başladı.

## multi-head yaklaşımı

asıl magic multi-head sisteminde. her context için ayrı bir prediction head var:

draw_source head 2 output veriyor - deck mi discard mi. burada çok basit bir yapı yeterli, 256->128->2 şeklinde.

main_action head 7 output veriyor - kartı discard et, swap et, ability kullan vs. bu biraz daha karmaşık kararlar içerdiği için 256->192->128->7 yapısı kullandık.

jack_ability head tam 16 output veriyor - 4x4 grid'de her pozisyon için bir değer. bu en karmaşık head çünkü spatial reasoning gerektiriyor. 256->192->128->64->16 şeklinde derin bir yapı.

queen_ability head 8 output veriyor - peek veya swap seçenekleri için. orta düzeyde karmaşıklık, 256->128->64->8.

## value head ve dueling architecture

ayrıca her head'in yanında bir de value head var. bu dueling DQN konseptinden geliyor. value head state'in ne kadar iyi olduğunu öğreniyor, action head'ler ise hangi action'ın daha avantajlı olduğunu. sonra bunları combine ediyoruz: Q(s,a) = V(s) + A(s,a) - mean(A(s,:)). bu yaklaşım özellikle dutch cabo gibi oyunlarda çok faydalı çünkü bazen hangi action seçersen seç sonuç aynı oluyor.

## training stratejisi

normal DQN'den farklı olarak experience replay buffer'ı context-aware yaptık. her context'ten denk sayıda sample almaya çalışıyoruz ki network bir context'e bias olmasın. mesela eğer hep main_action context'ini görürse jack_ability'yi öğrenemez.

target network kullanıyoruz stability için. her 1000 step'te policy network'ün weight'lerini target network'e kopyalıyoruz. bu Q-learning'deki moving target problemini çözüyor.

loss function her context için ayrı hesaplanıyor sonra topluyoruz. bu sayede her head kendi context'inde uzmanlaşıyor. gradient clipping de var çünkü LSTM'ler exploding gradient'lara meyilli.

## hardware optimizasyonları

batch size'ı GPU memory'ye göre otomatik ayarlıyoruz. 7.7GB VRAM için 256 batch size optimal. daha az memory varsa küçültüyoruz, daha fazla varsa büyütüyoruz.

experience collection'ı parallel yapıyoruz. CPU core sayısına göre birden fazla game instance çalıştırıp experience topluyoruz. bu training'i çok hızlandırıyor.

LSTM'ler CUDA'da parallel çalışıyor ama training/eval mode'larına dikkat etmek gerekiyor. backward pass sırasında training mode'da olmak zorunda yoksa cudnn hata veriyor.

## reward engineering

reward function oyunun doğasına uygun şekilde tasarlandi. game end'de büyük reward/penalty var (+100 kazanma, -50 kaybetme). intermediate reward'lar da var - düşük kart sayısı için +5, score advantage için +2 gibi. dutch call başarılı olursa +50 bonus, başarısız olursa -30 penalty.

bu reward structure sayesinde network sadece kazanmayı değil, kazanma yolundaki doğru adımları da öğreniyor. mesela kartlarını hızlı bitirmek, düşük kartları tutmak, yüksek kartları atmak gibi.

## sonuç

network toplam 320k parameter'e sahip. büyük değil ama dutch cabo için yeterli. modular yapısı sayesinde her oyun mekanikini ayrı ayrı öğrenebiliyor. LSTM memory ile sequence learning yapıyor. multi-head architecture ile farklı decision type'larında uzmanlaşıyor. training sırasında stable öğreniyor ve GPU'da hızlı çalışıyor.

asıl güzel olan şey bu network'ün general game playing için de uyarlanabilir olması. başka kart oyunları için context'leri ve head'leri değiştirebiliriz ama core architecture aynı kalabilir. 