# -*- coding: utf-8 -*-
"""Gomulu Rusca <-> Ingilizce / Turkce cekirdek sozluk (A1-B1, ~1000 madde).

Satir bicimi:  vurgulu_kelime|tur [ek]|ingilizce karsilik; karsilik 2[|turkce karsilik; karsilik 2]
Dorduncu alan (Turkce) ISTEGE BAGLIDIR: yoksa madde Turkce karsiliksiz yuklenir (Entry.tr = "")
ve sozluk sekmesi RU->TR aramasinda eksik glossu AI'dan tamamlayabilir. Turkce alanda
ç ğ ı ö ş ü harfleri oldugu gibi yazilir; anlamlar '; ' ile ayrilir.
Vurgu, vurgulu sesli harften hemen SONRA gelen tek tirnakla gosterilir (OpenRussian bicimi).
Tur: n v adj adv pron prep conj num part int phr - ek: m f n pl (cinsiyet) / ipf pf (gorunus).
"""

DATA = r"""
# ---- selamlasma / nezaket ----
приве'т|int|hi; hello (informal)|selam; merhaba
здра'вствуйте|int|hello (formal)|merhaba (resmî)
здра'вствуй|int|hello (informal, singular)|merhaba
до свида'ния|phr|goodbye|hoşça kalın; güle güle
пока'|int|bye (informal)|hoşça kal; görüşürüz
до'брое у'тро|phr|good morning|günaydın
до'брый день|phr|good afternoon|iyi günler
до'брый ве'чер|phr|good evening|iyi akşamlar
споко'йной но'чи|phr|good night|iyi geceler
спаси'бо|int|thank you; thanks|teşekkür ederim; sağ ol
пожа'луйста|int|please; you are welcome|lütfen; rica ederim
извини'те|int|excuse me; sorry (formal)|affedersiniz; özür dilerim
прости'те|int|forgive me; sorry|kusura bakmayın; özür dilerim
да|part|yes|evet
нет|part|no|hayır
хорошо'|adv|well; OK; fine|iyi; tamam; peki
ла'дно|part|all right; okay|tamam; peki
коне'чно|adv|of course|tabii; elbette
мо'жет быть|phr|maybe; perhaps|belki
как дела'|phr|how are you|nasılsın; nasıl gidiyor
ничего'|pron|nothing; not bad|hiçbir şey; fena değil
ниче'го стра'шного|phr|no problem; never mind|önemli değil; sorun değil
добро' пожа'ловать|phr|welcome|hoş geldiniz
всего' хоро'шего|phr|all the best|iyi günler; her şey gönlünce olsun
уда'чи|int|good luck|bol şans; kolay gelsin
поздравля'ю|int|congratulations|tebrikler; tebrik ederim
с днём рожде'ния|phr|happy birthday|doğum günün kutlu olsun
бу'дьте здоро'вы|phr|bless you; take care|çok yaşa; sağlıcakla kalın
прия'тного аппети'та|phr|enjoy your meal|afiyet olsun
# ---- soru kelimeleri ----
кто|pron|who|kim
что|pron|what|ne
где|adv|where|nerede
куда'|adv|where to|nereye
отку'да|adv|where from|nereden
когда'|adv|when|ne zaman
почему'|adv|why|neden; niçin
заче'м|adv|what for; why|ne için; niye
как|adv|how|nasıl
како'й|pron|which; what kind of|hangi; nasıl bir
чей|pron|whose|kimin
ско'лько|adv|how much; how many|ne kadar; kaç
# ---- zamirler ----
я|pron|I|ben
ты|pron|you (singular, informal)|sen
он|pron|he|o (erkek)
она'|pron|she|o (kadın)
оно'|pron|it|o (nesne)
мы|pron|we|biz
вы|pron|you (plural or formal)|siz
они'|pron|they|onlar
мой|pron|my; mine|benim
твой|pron|your; yours (informal)|senin
его'|pron|his; its|onun (erkek)
её|pron|her; hers|onun (kadın)
наш|pron|our; ours|bizim
ваш|pron|your; yours (formal or plural)|sizin
их|pron|their; theirs|onların
свой|pron|one's own|kendi
э'тот|pron|this|bu
тот|pron|that|o; şu
э'то|pron|this; this is|bu; bu ...
всё|pron|everything; all|her şey; hepsi
все|pron|everyone; all|herkes; hepsi
ка'ждый|pron|each; every|her; her bir
никто'|pron|nobody|hiç kimse
ничто'|pron|nothing|hiçbir şey
кто'-то|pron|someone|biri; birisi
что'-то|pron|something|bir şey
кто'-нибудь|pron|anyone; anybody|herhangi biri; kimse
что'-нибудь|pron|anything|herhangi bir şey; bir şey
сам|pron|oneself; myself; himself|kendi; kendisi
себя'|pron|oneself (reflexive)|kendini; kendi
друг дру'га|phr|each other|birbirini
# ---- sayilar ----
ноль|num|zero|sıfır
оди'н|num|one|bir
два|num|two|iki
три|num|three|üç
четы'ре|num|four|dört
пять|num|five|beş
шесть|num|six|altı
семь|num|seven|yedi
во'семь|num|eight|sekiz
де'вять|num|nine|dokuz
де'сять|num|ten|on
оди'ннадцать|num|eleven|on bir
двена'дцать|num|twelve|on iki
трина'дцать|num|thirteen|on üç
четы'рнадцать|num|fourteen|on dört
пятна'дцать|num|fifteen|on beş
шестна'дцать|num|sixteen|on altı
семна'дцать|num|seventeen|on yedi
восемна'дцать|num|eighteen|on sekiz
девятна'дцать|num|nineteen|on dokuz
два'дцать|num|twenty|yirmi
три'дцать|num|thirty|otuz
со'рок|num|forty|kırk
пятьдеся'т|num|fifty|elli
шестьдеся'т|num|sixty|altmış
се'мьдесят|num|seventy|yetmiş
во'семьдесят|num|eighty|seksen
девяно'сто|num|ninety|doksan
сто|num|hundred|yüz
ты'сяча|num|thousand|bin
миллио'н|num|million|milyon
пе'рвый|num|first|birinci; ilk
второ'й|num|second|ikinci
тре'тий|num|third|üçüncü
четвёртый|num|fourth|dördüncü
пя'тый|num|fifth|beşinci
после'дний|adj|last; latest|son; sonuncu
полови'на|n f|half|yarım; yarı
раз|n m|time; once|kez; defa; bir kere
мно'го|adv|much; many; a lot|çok
ма'ло|adv|little; few|az
не'сколько|num|several; a few|birkaç
немно'го|adv|a little; a bit|biraz
# ---- zaman ----
вре'мя|n n|time|zaman; vakit
час|n m|hour; o'clock|saat
мину'та|n f|minute|dakika
секу'нда|n f|second (time)|saniye
день|n m|day|gün
ночь|n f|night|gece
у'тро|n n|morning|sabah
ве'чер|n m|evening|akşam
неде'ля|n f|week|hafta
ме'сяц|n m|month; moon|ay
год|n m|year|yıl; sene
сего'дня|adv|today|bugün
за'втра|adv|tomorrow|yarın
вчера'|adv|yesterday|dün
послеза'втра|adv|the day after tomorrow|öbür gün
позавчера'|adv|the day before yesterday|evvelsi gün
сейча'с|adv|now; right now|şimdi; hemen
тепе'рь|adv|now (as opposed to before)|şimdi; artık
пото'м|adv|then; later|sonra; daha sonra
ра'ньше|adv|earlier; before|daha önce; eskiden
по'здно|adv|late|geç
ра'но|adv|early|erken
всегда'|adv|always|her zaman; daima
никогда'|adv|never|asla; hiçbir zaman
иногда'|adv|sometimes|bazen
ча'сто|adv|often|sık sık
ре'дко|adv|rarely; seldom|nadiren; seyrek
обы'чно|adv|usually|genellikle
уже'|adv|already|artık; çoktan; zaten
ещё|adv|still; yet; more|hâlâ; daha; henüz
давно'|adv|long ago; for a long time|uzun zaman önce; çoktandır
неда'вно|adv|recently|geçenlerde; yakın zamanda
ско'ро|adv|soon|yakında
до'лго|adv|for a long time|uzun süre
снача'ла|adv|at first; first|önce; ilk başta
зате'м|adv|then; after that|sonra; ardından
наконе'ц|adv|finally; at last|nihayet; sonunda
понеде'льник|n m|Monday|pazartesi
вто'рник|n m|Tuesday|salı
среда'|n f|Wednesday|çarşamba
четве'рг|n m|Thursday|perşembe
пя'тница|n f|Friday|cuma
суббо'та|n f|Saturday|cumartesi
воскресе'нье|n n|Sunday|pazar
янва'рь|n m|January|ocak
февра'ль|n m|February|şubat
март|n m|March|mart
апре'ль|n m|April|nisan
май|n m|May|mayıs
ию'нь|n m|June|haziran
ию'ль|n m|July|temmuz
а'вгуст|n m|August|ağustos
сентя'брь|n m|September|eylül
октя'брь|n m|October|ekim
ноя'брь|n m|November|kasım
дека'брь|n m|December|aralık
весна'|n f|spring|ilkbahar; bahar
ле'то|n n|summer|yaz
о'сень|n f|autumn; fall|sonbahar; güz
зима'|n f|winter|kış
пра'здник|n m|holiday; celebration|bayram; tatil; kutlama
выходно'й|n m|day off; weekend day|tatil günü; izin günü
кани'кулы|n pl|school holidays; vacation|okul tatili; tatil
о'тпуск|n m|vacation; leave|izin; yıllık izin; tatil
# ---- aile / insanlar ----
челове'к|n m|person; human|insan; kişi
лю'ди|n pl|people|insanlar; halk
мужчи'на|n m|man|erkek; adam
же'нщина|n f|woman|kadın
ма'льчик|n m|boy|oğlan; erkek çocuk
де'вочка|n f|girl (child)|kız çocuğu; kız
де'вушка|n f|girl; young woman|genç kız; kız
па'рень|n m|guy; young man; boyfriend|delikanlı; genç adam; erkek arkadaş
ребёнок|n m|child|çocuk
де'ти|n pl|children|çocuklar
семья'|n f|family|aile
роди'тели|n pl|parents|anne baba; ebeveynler
мать|n f|mother|anne; ana
ма'ма|n f|mom|anne; anneciğim
оте'ц|n m|father|baba
па'па|n m|dad|baba; babacığım
сын|n m|son|oğul
дочь|n f|daughter|kız (evlat)
брат|n m|brother|erkek kardeş; ağabey
сестра'|n f|sister|kız kardeş; abla
ба'бушка|n f|grandmother|büyükanne; nine
де'душка|n m|grandfather|dede; büyükbaba
внук|n m|grandson|torun (erkek)
вну'чка|n f|granddaughter|torun (kız)
дя'дя|n m|uncle|amca; dayı
тётя|n f|aunt|teyze; hala
муж|n m|husband|koca; eş
жена'|n f|wife|karı; eş
друг|n m|friend (male)|arkadaş (erkek); dost
подру'га|n f|friend (female)|arkadaş (kadın); kız arkadaş
сосе'д|n m|neighbour|komşu
гость|n m|guest|misafir; konuk
колле'га|n m|colleague|meslektaş; iş arkadaşı
знако'мый|n m|acquaintance|tanıdık
и'мя|n n|first name|ad; isim
фами'лия|n f|surname; last name|soyadı
во'зраст|n m|age|yaş
взро'слый|adj|adult; grown-up|yetişkin; ergin
ста'рый|adj|old|yaşlı; eski
молодо'й|adj|young|genç
# ---- meslekler ----
рабо'та|n f|work; job|iş; çalışma
профе'ссия|n f|profession|meslek
врач|n m|doctor; physician|doktor; hekim
учи'тель|n m|teacher|öğretmen
студе'нт|n m|student (university)|öğrenci (üniversite)
учени'к|n m|pupil; student (school)|öğrenci (okul); talebe
инжене'р|n m|engineer|mühendis
программи'ст|n m|programmer|programcı; yazılımcı
води'тель|n m|driver|sürücü; şoför
продаве'ц|n m|shop assistant; seller|satıcı; tezgâhtar
по'вар|n m|cook; chef|aşçı
официа'нт|n m|waiter|garson
полице'йский|n m|police officer|polis; polis memuru
журнали'ст|n m|journalist|gazeteci
худо'жник|n m|artist; painter|ressam; sanatçı
музыка'нт|n m|musician|müzisyen
актёр|n m|actor|aktör; oyuncu
писа'тель|n m|writer|yazar
юри'ст|n m|lawyer|hukukçu; avukat
бизнесме'н|n m|businessman|iş adamı
дире'ктор|n m|director; manager|müdür; yönetici
нача'льник|n m|boss; chief|patron; şef; amir
секрета'рь|n m|secretary|sekreter
рабо'чий|n m|worker|işçi
строи'тель|n m|builder|inşaatçı; yapı ustası
медсестра'|n f|nurse|hemşire
перево'дчик|n m|translator; interpreter|çevirmen; tercüman
учёный|n m|scientist; scholar|bilim insanı; âlim
солда'т|n m|soldier|asker
# ---- ev ----
дом|n m|house; home|ev
кварти'ра|n f|flat; apartment|daire; apartman dairesi
ко'мната|n f|room|oda
ку'хня|n f|kitchen|mutfak
спа'льня|n f|bedroom|yatak odası
ва'нная|n f|bathroom|banyo
туале'т|n m|toilet|tuvalet
коридо'р|n m|corridor; hallway|koridor
балко'н|n m|balcony|balkon
эта'ж|n m|floor; storey|kat
лифт|n m|lift; elevator|asansör
ле'стница|n f|stairs; ladder|merdiven
дверь|n f|door|kapı
окно'|n n|window|pencere
стена'|n f|wall|duvar
пол|n m|floor|zemin; yer; döşeme
потоло'к|n m|ceiling|tavan
кры'ша|n f|roof|çatı
ме'бель|n f|furniture|mobilya
стол|n m|table; desk|masa
стул|n m|chair|sandalye
кре'сло|n n|armchair|koltuk
дива'н|n m|sofa; couch|kanepe; divan
крова'ть|n f|bed|yatak
шкаф|n m|wardrobe; cupboard|dolap; gardırop
по'лка|n f|shelf|raf
зе'ркало|n n|mirror|ayna
ла'мпа|n f|lamp|lamba
свет|n m|light|ışık
ковёр|n m|carpet; rug|halı; kilim
карти'на|n f|picture; painting|tablo; resim
холоди'льник|n m|fridge; refrigerator|buzdolabı
плита'|n f|stove; cooker|ocak; fırın
духо'вка|n f|oven|fırın
микроволно'вка|n f|microwave|mikrodalga
стира'льная маши'на|phr|washing machine|çamaşır makinesi
телеви'зор|n m|television set|televizyon
ключ|n m|key|anahtar
замо'к|n m|lock|kilit
му'сор|n m|rubbish; garbage|çöp
убира'ть|v ipf|to clean; to tidy up|temizlemek; toplamak
убра'ть|v pf|to clean; to tidy up|temizlemek; toplamak
мыть|v ipf|to wash|yıkamak
помы'ть|v pf|to wash|yıkamak
гото'вить|v ipf|to cook; to prepare|pişirmek; hazırlamak
пригото'вить|v pf|to cook; to prepare|pişirmek; hazırlamak
# ---- gunluk esyalar ----
вещь|n f|thing; item|şey; eşya
су'мка|n f|bag; handbag|çanta; el çantası
рюкза'к|n m|backpack|sırt çantası
чемода'н|n m|suitcase|bavul; valiz
кошелёк|n m|wallet; purse|cüzdan
де'ньги|n pl|money|para
телефо'н|n m|phone|telefon
компью'тер|n m|computer|bilgisayar
ноутбу'к|n m|laptop|dizüstü bilgisayar; laptop
часы'|n pl|clock; watch|saat
очки'|n pl|glasses; spectacles|gözlük
зо'нт|n m|umbrella|şemsiye
кни'га|n f|book|kitap
тетра'дь|n f|notebook; exercise book|defter
ру'чка|n f|pen; handle|kalem; kulp; sap
каранда'ш|n m|pencil|kurşun kalem
бума'га|n f|paper|kâğıt
письмо'|n n|letter (mail)|mektup
газе'та|n f|newspaper|gazete
журна'л|n m|magazine|dergi
карти'нка|n f|small picture; image|küçük resim; görsel
фотогра'фия|n f|photograph|fotoğraf
пода'рок|n m|gift; present|hediye; armağan
игру'шка|n f|toy|oyuncak
мяч|n m|ball|top
сигаре'та|n f|cigarette|sigara
спи'чки|n pl|matches|kibrit
# ---- kiyafet ----
оде'жда|n f|clothes; clothing|giysi; kıyafet; elbise
руба'шка|n f|shirt|gömlek
футбо'лка|n f|T-shirt|tişört
брю'ки|n pl|trousers; pants|pantolon
джи'нсы|n pl|jeans|kot pantolon
ю'бка|n f|skirt|etek
пла'тье|n n|dress|elbise
пальто'|n n|coat|palto; manto
ку'ртка|n f|jacket|ceket; mont
костю'м|n m|suit; costume|takım elbise; kostüm
сви'тер|n m|sweater|kazak
ша'пка|n f|hat; cap (warm)|bere; şapka
шля'па|n f|hat (with brim)|şapka
шарф|n m|scarf|atkı; eşarp
перча'тки|n pl|gloves|eldiven
носки'|n pl|socks|çorap
о'бувь|n f|footwear|ayakkabı
боти'нки|n pl|boots; shoes|bot; ayakkabı
ту'фли|n pl|shoes (dress)|ayakkabı; iskarpin
кроссо'вки|n pl|sneakers; trainers|spor ayakkabı
разме'р|n m|size|beden; boyut; numara
надева'ть|v ipf|to put on (clothes)|giymek
наде'ть|v pf|to put on (clothes)|giymek
снима'ть|v ipf|to take off; to rent; to film|çıkarmak; kiralamak; çekmek (film)
снять|v pf|to take off; to rent; to film|çıkarmak; kiralamak; çekmek (film)
носи'ть|v ipf|to wear; to carry|giymek; taşımak
# ---- vucut / saglik ----
те'ло|n n|body|vücut; beden
голова'|n f|head|baş; kafa
лицо'|n n|face|yüz
глаз|n m|eye|göz
у'хо|n n|ear|kulak
нос|n m|nose|burun
рот|n m|mouth|ağız
зуб|n m|tooth|diş
губа'|n f|lip|dudak
во'лосы|n pl|hair|saç
ше'я|n f|neck|boyun
плечо'|n n|shoulder|omuz
рука'|n f|hand; arm|el; kol
па'лец|n m|finger; toe|parmak
нога'|n f|leg; foot|bacak; ayak
коле'но|n n|knee|diz
спина'|n f|back (body)|sırt
живо'т|n m|stomach; belly|karın; mide
се'рдце|n n|heart|kalp; yürek
кровь|n f|blood|kan
кость|n f|bone|kemik
ко'жа|n f|skin; leather|deri; cilt
здоро'вье|n n|health|sağlık
здоро'вый|adj|healthy|sağlıklı
больно'й|adj|sick; ill; patient|hasta
боле'знь|n f|illness; disease|hastalık
боль|n f|pain; ache|ağrı; acı
боле'ть|v ipf|to be ill; to hurt|hasta olmak; ağrımak
температу'ра|n f|temperature; fever|sıcaklık; ateş
просту'да|n f|cold (illness)|soğuk algınlığı; nezle
ка'шель|n m|cough|öksürük
лека'рство|n n|medicine; drug|ilaç
табле'тка|n f|pill; tablet|hap; tablet
апте'ка|n f|pharmacy; chemist|eczane
больни'ца|n f|hospital|hastane
поликли'ника|n f|clinic|poliklinik
ско'рая по'мощь|phr|ambulance|ambulans; acil yardım
уста'лый|adj|tired|yorgun
устава'ть|v ipf|to get tired|yorulmak
уста'ть|v pf|to get tired|yorulmak
спать|v ipf|to sleep|uyumak
засыпа'ть|v ipf|to fall asleep|uykuya dalmak
засну'ть|v pf|to fall asleep|uykuya dalmak
просыпа'ться|v ipf|to wake up|uyanmak
просну'ться|v pf|to wake up|uyanmak
отдыха'ть|v ipf|to rest; to relax|dinlenmek
отдохну'ть|v pf|to rest; to relax|dinlenmek
# ---- yiyecek / icecek ----
еда'|n f|food|yemek; yiyecek
за'втрак|n m|breakfast|kahvaltı
обе'д|n m|lunch; dinner (midday meal)|öğle yemeği
у'жин|n m|supper; dinner (evening)|akşam yemeği
хлеб|n m|bread|ekmek
ма'сло|n n|butter; oil|tereyağı; yağ
сыр|n m|cheese|peynir
молоко'|n n|milk|süt
яйцо'|n n|egg|yumurta
мя'со|n n|meat|et
ку'рица|n f|chicken; hen|tavuk
ры'ба|n f|fish|balık
колбаса'|n f|sausage|sucuk; sosis
суп|n m|soup|çorba
ка'ша|n f|porridge; kasha|lapa; kaşa
рис|n m|rice|pirinç
макаро'ны|n pl|pasta|makarna
карто'фель|n m|potatoes|patates
карто'шка|n f|potato (colloquial)|patates (konuşma dili)
о'вощи|n pl|vegetables|sebzeler
фру'кты|n pl|fruit|meyveler
я'блоко|n n|apple|elma
гру'ша|n f|pear|armut
бана'н|n m|banana|muz
апельси'н|n m|orange|portakal
лимо'н|n m|lemon|limon
виногра'д|n m|grapes|üzüm
я'года|n f|berry|meyve (küçük, yumuşak); yemiş
клубни'ка|n f|strawberry|çilek
помидо'р|n m|tomato|domates
огуре'ц|n m|cucumber|salatalık
лук|n m|onion|soğan
чесно'к|n m|garlic|sarımsak
капу'ста|n f|cabbage|lahana
морко'вь|n f|carrot|havuç
гриб|n m|mushroom|mantar
соль|n f|salt|tuz
са'хар|n m|sugar|şeker
пе'рец|n m|pepper|biber
мёд|n m|honey|bal
сла'дкий|adj|sweet|tatlı
солёный|adj|salty|tuzlu
о'стрый|adj|spicy; sharp|acı; keskin
вку'сный|adj|tasty; delicious|lezzetli
све'жий|adj|fresh|taze
торт|n m|cake|pasta
пиро'г|n m|pie|börek; turta
пече'нье|n n|cookies; biscuits|kurabiye; bisküvi
шокола'д|n m|chocolate|çikolata
конфе'та|n f|candy; sweet|şekerleme; bonbon
моро'женое|n n|ice cream|dondurma
вода'|n f|water|su
чай|n m|tea|çay
ко'фе|n m|coffee|kahve
сок|n m|juice|meyve suyu
пи'во|n n|beer|bira
вино'|n n|wine|şarap
во'дка|n f|vodka|votka
буты'лка|n f|bottle|şişe
стака'н|n m|glass (drinking)|bardak
ча'шка|n f|cup|fincan
таре'лка|n f|plate|tabak
ло'жка|n f|spoon|kaşık
ви'лка|n f|fork|çatal
нож|n m|knife|bıçak
кастрю'ля|n f|saucepan; pot|tencere
сковорода'|n f|frying pan|tava
магази'н|n m|shop; store|mağaza; dükkân
ры'нок|n m|market|pazar
рестора'н|n m|restaurant|restoran; lokanta
кафе'|n n|cafe|kafe
столо'вая|n f|canteen; dining room|yemekhane; yemek odası
меню'|n n|menu|menü
счёт|n m|bill; account; score|hesap; skor
есть|v ipf|to eat; there is|yemek; var
съесть|v pf|to eat (up)|yemek (bitirmek)
пить|v ipf|to drink|içmek
вы'пить|v pf|to drink (up)|içmek (bitirmek)
за'втракать|v ipf|to have breakfast|kahvaltı etmek
обе'дать|v ipf|to have lunch|öğle yemeği yemek
у'жинать|v ipf|to have dinner|akşam yemeği yemek
голо'дный|adj|hungry|aç
# ---- sehir / ulasim ----
го'род|n m|city; town|şehir; kent
дере'вня|n f|village; countryside|köy; kırsal
страна'|n f|country|ülke
столи'ца|n f|capital city|başkent
у'лица|n f|street|sokak; cadde
пло'щадь|n f|square; area|meydan; alan
доро'га|n f|road; way|yol
мост|n m|bridge|köprü
парк|n m|park|park
сад|n m|garden|bahçe
центр|n m|centre|merkez
райо'н|n m|district; area|semt; bölge; ilçe
зда'ние|n n|building|bina
це'рковь|n f|church|kilise
музе'й|n m|museum|müze
теа'тр|n m|theatre|tiyatro
кино'|n n|cinema; movies|sinema
библиоте'ка|n f|library|kütüphane
шко'ла|n f|school|okul
университе'т|n m|university|üniversite
банк|n m|bank|banka
по'чта|n f|post office; mail|postane; posta
гости'ница|n f|hotel|otel
вокза'л|n m|railway station|gar; tren istasyonu
ста'нция|n f|station|istasyon
остано'вка|n f|stop (bus, tram)|durak
аэропо'рт|n m|airport|havalimanı
метро'|n n|metro; underground|metro
авто'бус|n m|bus|otobüs
трамва'й|n m|tram|tramvay
тролле'йбус|n m|trolleybus|troleybüs
маши'на|n f|car; machine|araba; makine
такси'|n n|taxi|taksi
по'езд|n m|train|tren
самолёт|n m|plane|uçak
кора'бль|n m|ship|gemi
велосипе'д|n m|bicycle|bisiklet
биле'т|n m|ticket|bilet
па'спорт|n m|passport|pasaport
ви'за|n f|visa|vize
грани'ца|n f|border|sınır
путеше'ствие|n n|journey; travel|seyahat; yolculuk
пое'здка|n f|trip|gezi; yolculuk
тури'ст|n m|tourist|turist
ка'рта|n f|map; card|harita; kart
а'дрес|n m|address|adres
напра'во|adv|to the right|sağa
нале'во|adv|to the left|sola
пря'мо|adv|straight ahead; directly|dümdüz; doğrudan
далеко'|adv|far|uzak; uzakta
бли'зко|adv|near; close|yakın; yakında
здесь|adv|here|burada
тут|adv|here (colloquial)|burada (konuşma dili)
там|adv|there|orada
туда'|adv|to there|oraya
сюда'|adv|to here|buraya
до'ма|adv|at home|evde
домо'й|adv|homeward; (to) home|eve
сле'ва|adv|on the left|solda
спра'ва|adv|on the right|sağda
# ---- hareket fiilleri ----
идти'|v ipf|to go (on foot, one direction)|gitmek (yürüyerek, tek yön)
ходи'ть|v ipf|to go (on foot, habitually)|gitmek (yürüyerek, düzenli olarak)
пойти'|v pf|to go; to set off (on foot)|gitmek; yola çıkmak (yürüyerek)
е'хать|v ipf|to go (by vehicle, one direction)|gitmek (araçla, tek yön)
е'здить|v ipf|to go (by vehicle, habitually)|gitmek (araçla, düzenli olarak)
пое'хать|v pf|to go; to set off (by vehicle)|gitmek; yola çıkmak (araçla)
бежа'ть|v ipf|to run (one direction)|koşmak (tek yön)
бе'гать|v ipf|to run (habitually)|koşmak (düzenli olarak)
лете'ть|v ipf|to fly (one direction)|uçmak (tek yön)
лета'ть|v ipf|to fly (habitually)|uçmak (düzenli olarak)
плыть|v ipf|to swim; to sail (one direction)|yüzmek; gemiyle gitmek (tek yön)
пла'вать|v ipf|to swim (habitually)|yüzmek (düzenli olarak)
нести'|v ipf|to carry (on foot)|taşımak (yürüyerek)
везти'|v ipf|to carry (by vehicle); to be lucky|taşımak (araçla); şanslı olmak
вести'|v ipf|to lead; to drive|götürmek; yönetmek; sürmek
приходи'ть|v ipf|to come; to arrive (on foot)|gelmek; varmak (yürüyerek)
прийти'|v pf|to come; to arrive (on foot)|gelmek; varmak (yürüyerek)
уходи'ть|v ipf|to leave; to go away|ayrılmak; gitmek
уйти'|v pf|to leave; to go away|ayrılmak; gitmek
входи'ть|v ipf|to enter|girmek
войти'|v pf|to enter|girmek
выходи'ть|v ipf|to go out; to exit|çıkmak; dışarı çıkmak
вы'йти|v pf|to go out; to exit|çıkmak; dışarı çıkmak
приезжа'ть|v ipf|to arrive (by vehicle)|gelmek; varmak (araçla)
прие'хать|v pf|to arrive (by vehicle)|gelmek; varmak (araçla)
уезжа'ть|v ipf|to leave (by vehicle)|ayrılmak; gitmek (araçla)
уе'хать|v pf|to leave (by vehicle)|ayrılmak; gitmek (araçla)
переходи'ть|v ipf|to cross; to move over|karşıya geçmek; geçmek
перейти'|v pf|to cross; to move over|karşıya geçmek; geçmek
возвраща'ться|v ipf|to return; to come back|dönmek; geri dönmek
верну'ться|v pf|to return; to come back|dönmek; geri dönmek
подходи'ть|v ipf|to approach; to suit|yaklaşmak; uymak
подойти'|v pf|to approach; to suit|yaklaşmak; uymak
# ---- temel fiiller ----
быть|v ipf|to be|olmak
стать|v pf|to become; to start|olmak; başlamak
станови'ться|v ipf|to become|olmak; haline gelmek
де'лать|v ipf|to do; to make|yapmak
сде'лать|v pf|to do; to make|yapmak
говори'ть|v ipf|to speak; to say; to talk|konuşmak; söylemek
сказа'ть|v pf|to say; to tell|söylemek; demek
разгова'ривать|v ipf|to talk; to converse|konuşmak; sohbet etmek
знать|v ipf|to know|bilmek
узнава'ть|v ipf|to find out; to recognize|öğrenmek; tanımak
узна'ть|v pf|to find out; to recognize|öğrenmek; tanımak
ду'мать|v ipf|to think|düşünmek
поду'мать|v pf|to think (for a while)|düşünmek (bir süre)
понима'ть|v ipf|to understand|anlamak
поня'ть|v pf|to understand|anlamak
хоте'ть|v ipf|to want|istemek
мочь|v ipf|to be able; can|yapabilmek; -ebilmek
смочь|v pf|to be able; to manage|yapabilmek; başarmak
уме'ть|v ipf|to know how; to be able|yapmayı bilmek; -ebilmek
люби'ть|v ipf|to love; to like|sevmek
нра'виться|v ipf|to be liked; to please|hoşuna gitmek; beğenilmek
понра'виться|v pf|to be liked; to please|hoşuna gitmek; beğenilmek
ви'деть|v ipf|to see|görmek
уви'деть|v pf|to see; to catch sight of|görmek; fark etmek
смотре'ть|v ipf|to look; to watch|bakmak; izlemek
посмотре'ть|v pf|to look; to watch|bakmak; izlemek
слы'шать|v ipf|to hear|duymak
услы'шать|v pf|to hear|duymak
слу'шать|v ipf|to listen|dinlemek
послу'шать|v pf|to listen (for a while)|dinlemek (bir süre)
чита'ть|v ipf|to read|okumak
прочита'ть|v pf|to read (through)|okumak; okuyup bitirmek
писа'ть|v ipf|to write|yazmak
написа'ть|v pf|to write|yazmak
жить|v ipf|to live|yaşamak; oturmak
рабо'тать|v ipf|to work|çalışmak
учи'ться|v ipf|to study; to learn (at a school)|okumak; öğrenim görmek
учи'ть|v ipf|to learn; to teach|öğrenmek; öğretmek
вы'учить|v pf|to learn (by heart)|öğrenmek; ezberlemek
научи'ться|v pf|to learn (how to do)|öğrenmek
изуча'ть|v ipf|to study (a subject)|incelemek; öğrenmek
игра'ть|v ipf|to play|oynamak; çalmak
сыгра'ть|v pf|to play (once)|oynamak; çalmak
дава'ть|v ipf|to give|vermek
дать|v pf|to give|vermek
брать|v ipf|to take|almak
взять|v pf|to take|almak
получа'ть|v ipf|to receive; to get|almak; elde etmek
получи'ть|v pf|to receive; to get|almak; elde etmek
покупа'ть|v ipf|to buy|satın almak
купи'ть|v pf|to buy|satın almak
продава'ть|v ipf|to sell|satmak
прода'ть|v pf|to sell|satmak
плати'ть|v ipf|to pay|ödemek
заплати'ть|v pf|to pay|ödemek
сто'ить|v ipf|to cost; to be worth|etmek (fiyat); değmek
открыва'ть|v ipf|to open|açmak
откры'ть|v pf|to open|açmak
закрыва'ть|v ipf|to close|kapatmak
закры'ть|v pf|to close|kapatmak
начина'ть|v ipf|to begin; to start|başlamak
нача'ть|v pf|to begin; to start|başlamak
конча'ть|v ipf|to finish|bitirmek
ко'нчить|v pf|to finish|bitirmek
зака'нчивать|v ipf|to finish; to complete|bitirmek; tamamlamak
зако'нчить|v pf|to finish; to complete|bitirmek; tamamlamak
продолжа'ть|v ipf|to continue|devam etmek
продо'лжить|v pf|to continue|devam etmek
жда'ть|v ipf|to wait|beklemek
подожда'ть|v pf|to wait (a while)|beklemek; biraz beklemek
иска'ть|v ipf|to look for; to search|aramak
найти'|v pf|to find|bulmak
находи'ть|v ipf|to find|bulmak
теря'ть|v ipf|to lose|kaybetmek
потеря'ть|v pf|to lose|kaybetmek
по'мнить|v ipf|to remember|hatırlamak
запомина'ть|v ipf|to memorize|ezberlemek; aklında tutmak
запо'мнить|v pf|to memorize|ezberlemek; aklında tutmak
забыва'ть|v ipf|to forget|unutmak
забы'ть|v pf|to forget|unutmak
спра'шивать|v ipf|to ask (a question)|sormak
спроси'ть|v pf|to ask (a question)|sormak
проси'ть|v ipf|to ask for; to request|rica etmek; istemek
попроси'ть|v pf|to ask for; to request|rica etmek; istemek
отвеча'ть|v ipf|to answer; to reply|cevap vermek; yanıtlamak
отве'тить|v pf|to answer; to reply|cevap vermek; yanıtlamak
помога'ть|v ipf|to help|yardım etmek
помо'чь|v pf|to help|yardım etmek
звони'ть|v ipf|to call (phone); to ring|telefon etmek; aramak
позвони'ть|v pf|to call (phone); to ring|telefon etmek; aramak
встреча'ть|v ipf|to meet; to greet|karşılamak; buluşmak
встре'тить|v pf|to meet; to greet|karşılamak; buluşmak
встреча'ться|v ipf|to meet (each other); to date|buluşmak; görüşmek; çıkmak
пока'зывать|v ipf|to show|göstermek
показа'ть|v pf|to show|göstermek
расска'зывать|v ipf|to tell; to narrate|anlatmak
рассказа'ть|v pf|to tell; to narrate|anlatmak
объясня'ть|v ipf|to explain|açıklamak
объясни'ть|v pf|to explain|açıklamak
переводи'ть|v ipf|to translate; to transfer|çevirmek; tercüme etmek; aktarmak
перевести'|v pf|to translate; to transfer|çevirmek; tercüme etmek; aktarmak
повторя'ть|v ipf|to repeat|tekrarlamak
повтори'ть|v pf|to repeat|tekrarlamak
отправля'ть|v ipf|to send|göndermek
отпра'вить|v pf|to send|göndermek
посыла'ть|v ipf|to send|göndermek; yollamak
посла'ть|v pf|to send|göndermek; yollamak
приноси'ть|v ipf|to bring (on foot)|getirmek
принести'|v pf|to bring (on foot)|getirmek
класть|v ipf|to put (lying)|koymak (yatay)
положи'ть|v pf|to put (lying)|koymak (yatay)
ста'вить|v ipf|to put (standing); to set|koymak (dikey); yerleştirmek
поста'вить|v pf|to put (standing); to set|koymak (dikey); yerleştirmek
держа'ть|v ipf|to hold; to keep|tutmak
сиде'ть|v ipf|to sit; to be sitting|oturmak
сади'ться|v ipf|to sit down|oturmak (yerine)
сесть|v pf|to sit down|oturmak (yerine)
стоя'ть|v ipf|to stand|ayakta durmak
встава'ть|v ipf|to get up; to stand up|kalkmak; ayağa kalkmak
встать|v pf|to get up; to stand up|kalkmak; ayağa kalkmak
лежа'ть|v ipf|to lie; to be lying|yatmak; uzanmış olmak
ложи'ться|v ipf|to lie down; to go to bed|yatmak; uzanmak
лечь|v pf|to lie down; to go to bed|yatmak; uzanmak
висе'ть|v ipf|to hang; to be hanging|asılı olmak
чу'вствовать|v ipf|to feel|hissetmek
почу'вствовать|v pf|to feel|hissetmek
боя'ться|v ipf|to be afraid; to fear|korkmak
ве'рить|v ipf|to believe; to trust|inanmak; güvenmek
наде'яться|v ipf|to hope|ummak; umut etmek
реша'ть|v ipf|to decide; to solve|karar vermek; çözmek
реши'ть|v pf|to decide; to solve|karar vermek; çözmek
про'бовать|v ipf|to try; to taste|denemek; tatmak
попро'бовать|v pf|to try; to taste|denemek; tatmak
стара'ться|v ipf|to try hard; to make an effort|çabalamak; gayret etmek
мечта'ть|v ipf|to dream (of)|hayal etmek; hayal kurmak
смея'ться|v ipf|to laugh|gülmek
улыба'ться|v ipf|to smile|gülümsemek
пла'кать|v ipf|to cry; to weep|ağlamak
крича'ть|v ipf|to shout; to scream|bağırmak
петь|v ipf|to sing|şarkı söylemek
спеть|v pf|to sing|şarkı söylemek
танцева'ть|v ipf|to dance|dans etmek
рисова'ть|v ipf|to draw; to paint|çizmek; resim yapmak
нарисова'ть|v pf|to draw; to paint|çizmek; resim yapmak
гуля'ть|v ipf|to walk; to stroll|gezmek; dolaşmak
погуля'ть|v pf|to take a walk|gezmek; biraz dolaşmak
путеше'ствовать|v ipf|to travel|seyahat etmek
занима'ться|v ipf|to be engaged in; to study|uğraşmak; ders çalışmak
интересова'ться|v ipf|to be interested in|ilgilenmek
зва'ть|v ipf|to call (by name)|çağırmak; adı olmak
называ'ться|v ipf|to be called (thing)|adlandırılmak; adı olmak
жени'ться|v ipf|to marry (of a man)|evlenmek (erkek)
выходи'ть за'муж|phr|to marry (of a woman)|evlenmek (kadın); kocaya varmak
роди'ться|v pf|to be born|doğmak
умира'ть|v ipf|to die|ölmek
умере'ть|v pf|to die|ölmek
расти'|v ipf|to grow|büyümek; yetişmek
меня'ть|v ipf|to change; to exchange|değiştirmek; bozdurmak
измени'ть|v pf|to change|değiştirmek
изменя'ться|v ipf|to change (oneself)|değişmek
стро'ить|v ipf|to build|inşa etmek; yapmak
постро'ить|v pf|to build|inşa etmek; yapmak
лома'ть|v ipf|to break|kırmak; bozmak
слома'ть|v pf|to break|kırmak; bozmak
ремонти'ровать|v ipf|to repair|tamir etmek; onarmak
па'дать|v ipf|to fall|düşmek
упа'сть|v pf|to fall|düşmek
броса'ть|v ipf|to throw; to quit|atmak; bırakmak
бро'сить|v pf|to throw; to quit|atmak; bırakmak
поднима'ть|v ipf|to lift; to raise|kaldırmak; yükseltmek
подня'ть|v pf|to lift; to raise|kaldırmak; yükseltmek
дви'гаться|v ipf|to move|hareket etmek; kımıldamak
остана'вливаться|v ipf|to stop (oneself)|durmak; konaklamak
останови'ться|v pf|to stop (oneself)|durmak; konaklamak
опа'здывать|v ipf|to be late|geç kalmak
опозда'ть|v pf|to be late|geç kalmak
спеши'ть|v ipf|to hurry|acele etmek
успева'ть|v ipf|to have time; to manage|yetişmek; vakit bulmak
успе'ть|v pf|to have time; to manage|yetişmek; vakit bulmak
пригласи'ть|v pf|to invite|davet etmek
приглаша'ть|v ipf|to invite|davet etmek
предлага'ть|v ipf|to offer; to suggest|teklif etmek; önermek
предложи'ть|v pf|to offer; to suggest|teklif etmek; önermek
сове'товать|v ipf|to advise|tavsiye etmek; öğüt vermek
посове'товать|v pf|to advise|tavsiye etmek; öğüt vermek
обеща'ть|v ipf|to promise|söz vermek
разреша'ть|v ipf|to allow; to permit|izin vermek
разреши'ть|v pf|to allow; to permit|izin vermek
запреща'ть|v ipf|to forbid|yasaklamak
запрети'ть|v pf|to forbid|yasaklamak
проверя'ть|v ipf|to check|kontrol etmek; denetlemek
прове'рить|v pf|to check|kontrol etmek; denetlemek
выбира'ть|v ipf|to choose; to elect|seçmek
вы'брать|v pf|to choose; to elect|seçmek
сравни'вать|v ipf|to compare|karşılaştırmak
сравни'ть|v pf|to compare|karşılaştırmak
счита'ть|v ipf|to count; to consider|saymak; saymak (bir şey olarak); düşünmek
посчита'ть|v pf|to count; to calculate|saymak; hesaplamak
испо'льзовать|v ipf|to use|kullanmak
по'льзоваться|v ipf|to use; to make use of|kullanmak; yararlanmak
принима'ть|v ipf|to accept; to take (medicine)|kabul etmek; almak (ilaç)
приня'ть|v pf|to accept; to take (medicine)|kabul etmek; almak (ilaç)
пла'нировать|v ipf|to plan|planlamak
организо'вывать|v ipf|to organize|düzenlemek; organize etmek
уча'ствовать|v ipf|to take part; to participate|katılmak
побежда'ть|v ipf|to win; to defeat|kazanmak; yenmek
победи'ть|v pf|to win; to defeat|kazanmak; yenmek
прои'грывать|v ipf|to lose (a game)|kaybetmek (oyun); yenilmek
проигра'ть|v pf|to lose (a game)|kaybetmek (oyun); yenilmek
случа'ться|v ipf|to happen|olmak; meydana gelmek
случи'ться|v pf|to happen|olmak; meydana gelmek
происходи'ть|v ipf|to happen; to take place|olmak; gerçekleşmek
произойти'|v pf|to happen; to take place|olmak; gerçekleşmek
каза'ться|v ipf|to seem|görünmek; gibi gelmek
означа'ть|v ipf|to mean; to signify|anlamına gelmek; ifade etmek
зна'чить|v ipf|to mean|anlamına gelmek; demek olmak
существова'ть|v ipf|to exist|var olmak; mevcut olmak
хвата'ть|v ipf|to be enough; to grab|yetmek; kapmak
хвати'ть|v pf|to be enough|yetmek
явля'ться|v ipf|to be (formal); to appear|olmak (resmi); görünmek
называ'ть|v ipf|to call; to name|adlandırmak; ad vermek
назва'ть|v pf|to call; to name|adlandırmak; ad vermek
# ---- sifatlar ----
большо'й|adj|big; large|büyük
ма'ленький|adj|small; little|küçük
хоро'ший|adj|good|iyi
плохо'й|adj|bad|kötü
но'вый|adj|new|yeni
краси'вый|adj|beautiful; handsome|güzel; yakışıklı
у'мный|adj|clever; smart|akıllı; zeki
глу'пый|adj|stupid; silly|aptal; saçma
до'брый|adj|kind; good|iyi kalpli; iyi
злой|adj|angry; evil|kızgın; kötü
весёлый|adj|cheerful; merry|neşeli; şen
гру'стный|adj|sad|üzgün; hüzünlü
счастли'вый|adj|happy|mutlu
интере'сный|adj|interesting|ilginç
ску'чный|adj|boring|sıkıcı
ва'жный|adj|important|önemli
тру'дный|adj|difficult; hard|zor; güç
лёгкий|adj|easy; light (weight)|kolay; hafif
сло'жный|adj|complicated; complex|karmaşık; zor
просто'й|adj|simple; plain|basit; sade
дорого'й|adj|expensive; dear|pahalı; değerli
дешёвый|adj|cheap|ucuz
бога'тый|adj|rich|zengin
бе'дный|adj|poor|fakir; yoksul
си'льный|adj|strong|güçlü; kuvvetli
сла'бый|adj|weak|zayıf; güçsüz
высо'кий|adj|tall; high|yüksek; uzun boylu
ни'зкий|adj|low; short (height)|alçak; kısa boylu
дли'нный|adj|long|uzun
коро'ткий|adj|short|kısa
широ'кий|adj|wide; broad|geniş
у'зкий|adj|narrow|dar
то'лстый|adj|thick; fat|kalın; şişman
то'нкий|adj|thin; fine|ince
тяжёлый|adj|heavy; hard|ağır; zor
горя'чий|adj|hot (to the touch)|sıcak (dokunulan şey)
жа'ркий|adj|hot (weather)|sıcak (hava)
холо'дный|adj|cold|soğuk
тёплый|adj|warm|ılık; sıcak
прохла'дный|adj|cool|serin
бы'стрый|adj|fast; quick|hızlı; çabuk
ме'дленный|adj|slow|yavaş
гро'мкий|adj|loud|gürültülü; yüksek sesli
ти'хий|adj|quiet|sessiz; sakin
чи'стый|adj|clean; pure|temiz; saf
гря'зный|adj|dirty|kirli; pis
све'тлый|adj|light; bright|açık (renk); aydınlık
тёмный|adj|dark|karanlık; koyu
я'ркий|adj|bright; vivid|parlak; canlı
по'лный|adj|full; plump|dolu; tam; tombul
пусто'й|adj|empty|boş
откры'тый|adj|open|açık
закры'тый|adj|closed|kapalı
свобо'дный|adj|free; vacant|özgür; serbest; boş
за'нятый|adj|busy; occupied|meşgul; dolu
гото'вый|adj|ready|hazır
пра'вильный|adj|correct; right|doğru
непра'вильный|adj|wrong; incorrect|yanlış
настоя'щий|adj|real; genuine; present|gerçek; hakiki; şimdiki
глава'|n f|chapter; head (of)|bölüm; başkan
гла'вный|adj|main; chief|ana; baş; en önemli
о'бщий|adj|common; general|ortak; genel
осо'бенный|adj|special; particular|özel; olağandışı
обы'чный|adj|usual; ordinary|olağan; sıradan
стра'нный|adj|strange|garip; tuhaf
изве'стный|adj|famous; well-known|ünlü; tanınmış
популя'рный|adj|popular|popüler
совреме'нный|adj|modern|modern; çağdaş
дре'вний|adj|ancient|eski; antik
родно'й|adj|native; own (family)|öz; ana (dil); yakın akraba
иностра'нный|adj|foreign|yabancı
ру'сский|adj|Russian|Rus; Rusça
англи'йский|adj|English|İngiliz; İngilizce
туре'цкий|adj|Turkish|Türk; Türkçe
неме'цкий|adj|German|Alman; Almanca
францу'зский|adj|French|Fransız; Fransızca
похо'жий|adj|similar; alike|benzer
ра'зный|adj|different; various|farklı; çeşitli
одина'ковый|adj|identical; the same|aynı; özdeş
друго'й|adj|other; another|başka; diğer
сле'дующий|adj|next; following|sonraki; gelecek
про'шлый|adj|last; past|geçen; geçmiş
бу'дущий|adj|future; next|gelecek; gelecekteki
ли'чный|adj|personal; private|kişisel; özel
удо'бный|adj|comfortable; convenient|rahat; uygun
опа'сный|adj|dangerous|tehlikeli
безопа'сный|adj|safe|güvenli; emniyetli
ве'рный|adj|faithful; correct|sadık; doğru
че'стный|adj|honest|dürüst
ве'жливый|adj|polite|kibar; nazik
серьёзный|adj|serious|ciddi
смешно'й|adj|funny|komik; gülünç
мо'крый|adj|wet|ıslak
сухо'й|adj|dry|kuru
мя'гкий|adj|soft|yumuşak
твёрдый|adj|hard; firm|sert; katı
кру'глый|adj|round|yuvarlak
живо'й|adj|alive; lively|canlı; hayatta
мёртвый|adj|dead|ölü
уве'ренный|adj|confident; sure|emin; kendinden emin
дово'льный|adj|satisfied; pleased|memnun; hoşnut
# ---- renkler ----
цвет|n m|colour|renk
бе'лый|adj|white|beyaz
чёрный|adj|black|siyah; kara
кра'сный|adj|red|kırmızı
си'ний|adj|blue (dark)|mavi; lacivert
голубо'й|adj|light blue|açık mavi
зелёный|adj|green|yeşil
жёлтый|adj|yellow|sarı
ора'нжевый|adj|orange (colour)|turuncu
кори'чневый|adj|brown|kahverengi
се'рый|adj|grey|gri
ро'зовый|adj|pink|pembe
фиоле'товый|adj|purple; violet|mor
# ---- zarflar / baglaclar / edatlar ----
о'чень|adv|very|çok
сли'шком|adv|too (excessively)|fazla; aşırı
почти'|adv|almost|neredeyse; hemen hemen
то'лько|adv|only; just|sadece; yalnız; ancak
то'же|adv|also; too|de/da; ayrıca
та'кже|adv|also; as well|ayrıca; de/da
ещё раз|phr|once more; again|bir kez daha; tekrar
опя'ть|adv|again|yine; tekrar
сно'ва|adv|again; anew|yeniden; tekrar
вме'сте|adv|together|birlikte; beraber
отде'льно|adv|separately|ayrı ayrı; ayrı olarak
бы'стро|adv|quickly; fast|hızlı; çabuk
ме'дленно|adv|slowly|yavaş; yavaşça
гро'мко|adv|loudly|yüksek sesle; gürültülü
ти'хо|adv|quietly|sessizce; yavaşça
пло'хо|adv|badly|kötü
пра'вильно|adv|correctly|doğru; doğru bir şekilde
непра'вильно|adv|incorrectly|yanlış; yanlış bir şekilde
легко'|adv|easily|kolayca; kolay
тру'дно|adv|difficult; hard (to do)|zor; güç
интере'сно|adv|interesting; interestingly|ilginç; ilginç bir şekilde
ско'лько сто'ит|phr|how much does it cost|ne kadar; kaç para
наве'рное|adv|probably|herhalde; muhtemelen
обяза'тельно|adv|definitely; without fail|mutlaka; kesinlikle
вообще'|adv|in general; at all|genel olarak; hiç
осо'бенно|adv|especially|özellikle
совсе'м|adv|completely; quite|tamamen; büsbütün
совсе'м не|phr|not at all|hiç; hiç de
дово'льно|adv|rather; quite; enough|oldukça; epey; yeter
доста'точно|adv|enough; sufficiently|yeterince; yeter
приме'рно|adv|approximately|yaklaşık; aşağı yukarı
ро'вно|adv|exactly; evenly|tam; tam olarak; düzgün
вдруг|adv|suddenly|birden; aniden
сра'зу|adv|at once; immediately|hemen; derhal
пока'|conj|while; for now|-ken; şimdilik; hoşça kal
и|conj|and|ve
а|conj|and; but (contrast)|ve; ama; ise
но|conj|but|ama; fakat
и'ли|conj|or|veya; ya da
что|conj|that (conjunction)|ki; -diğini
что'бы|conj|in order to; so that|-mek için; diye
потому' что|conj|because|çünkü
поэ'тому|adv|therefore; that is why|bu yüzden; bundan dolayı
е'сли|conj|if|eğer; -se/-sa
хотя'|conj|although|gerçi; -e rağmen
когда'|conj|when|-diğinde; -ince
как то'лько|phr|as soon as|-ir -mez; hemen
не|part|not|değil; -me/-ma
ни|part|neither; nor; not a|ne; ne de; hiç
ли|part|whether; question particle|mı/mi (soru eki); acaba
же|part|emphatic particle|ise; ya (pekiştirme)
ведь|part|after all; you know|ya; ki; ne de olsa
да'же|part|even|bile; hatta
вот|part|here is; there|işte
в|prep|in; at; to|-de/-da; -e/-a
на|prep|on; at; to|üstünde; -de/-da; -e/-a
с|prep|with; from|ile; -den/-dan
у|prep|at; by; near; (have)|yanında; -de/-da; (-in var)
к|prep|to; towards|-e/-a doğru; -e/-a
о|prep|about|hakkında
от|prep|from|-den/-dan
до|prep|until; up to|-e kadar
для|prep|for|için
без|prep|without|-sız/-siz; olmadan
по|prep|along; by; according to|boyunca; -e göre
за|prep|behind; for; beyond|arkasında; için; ötesinde
под|prep|under|altında
над|prep|above; over|üstünde; üzerinde
пе'ред|prep|in front of; before|önünde; önce
ме'жду|prep|between|arasında
о'коло|prep|near; about|yakınında; yaklaşık
че'рез|prep|across; through; in (time)|karşıya; içinden; sonra (süre)
из|prep|from; out of|-den/-dan; içinden
про|prep|about (colloquial)|hakkında
по'сле|prep|after|sonra; -den sonra
во вре'мя|prep|during|sırasında; esnasında
вме'сто|prep|instead of|yerine
кро'ме|prep|except; besides|dışında; hariç; -den başka
благодаря'|prep|thanks to|sayesinde
и'з-за|prep|because of; from behind|yüzünden; arkasından
# ---- egitim / dil ----
язы'к|n m|language; tongue|dil
сло'во|n n|word|kelime; sözcük
предложе'ние|n n|sentence; offer; proposal|cümle; teklif; öneri
бу'ква|n f|letter (alphabet)|harf
звук|n m|sound|ses
алфави'т|n m|alphabet|alfabe
грамма'тика|n f|grammar|dil bilgisi; gramer
слова'рь|n m|dictionary; vocabulary|sözlük; kelime hazinesi
уро'к|n m|lesson|ders
кла'сс|n m|class; classroom; grade|sınıf
заня'тие|n n|class; lesson; occupation|ders; meşguliyet; uğraş
ле'кция|n f|lecture|konferans; ders (üniversite)
экза'мен|n m|exam|sınav
зачёт|n m|pass/fail test|geçti-kaldı sınavı; notsuz dönem sonu sınavı
оце'нка|n f|grade; mark; assessment|not; değerlendirme
оши'бка|n f|mistake; error|hata; yanlış
вопро'с|n m|question|soru
отве'т|n m|answer|cevap; yanıt
пра'вило|n n|rule|kural
приме'р|n m|example|örnek
зада'ние|n n|task; assignment|görev; ödev
дома'шнее зада'ние|phr|homework|ev ödevi
упражне'ние|n n|exercise|alıştırma
текст|n m|text|metin
расска'з|n m|story; short story|hikâye; öykü
исто'рия|n f|history; story|tarih; hikâye
литерату'ра|n f|literature|edebiyat
матема'тика|n f|mathematics|matematik
фи'зика|n f|physics|fizik
хи'мия|n f|chemistry|kimya
биоло'гия|n f|biology|biyoloji
геогра'фия|n f|geography|coğrafya
нау'ка|n f|science|bilim
учи'лище|n n|vocational school|meslek okulu
факульте'т|n m|faculty; department|fakülte; bölüm
курс|n m|course; year (of study)|kurs; sınıf (üniversite yılı)
гру'ппа|n f|group|grup
доска'|n f|board; blackboard|tahta; yazı tahtası
па'рта|n f|school desk|okul sırası
переме'на|n f|break (school); change|teneffüs; değişiklik
зна'ние|n n|knowledge|bilgi
о'пыт|n m|experience; experiment|deneyim; deney
зна'чение|n n|meaning; significance|anlam; önem
перево'д|n m|translation; transfer|çeviri; havale
произноше'ние|n n|pronunciation|telaffuz
ударе'ние|n n|stress (word)|vurgu
па'мять|n f|memory|hafıza; bellek
внима'ние|n n|attention|dikkat
понима'ть по-ру'сски|phr|to understand Russian|Rusça anlamak
говори'ть по-англи'йски|phr|to speak English|İngilizce konuşmak
# ---- is / para ----
де'ло|n n|matter; business; affair|iş; mesele
би'знес|n m|business|iş; ticaret
фи'рма|n f|firm; company|firma; şirket
компа'ния|n f|company|şirket
о'фис|n m|office|ofis
заво'д|n m|factory; plant|fabrika
фа'брика|n f|factory|fabrika
рабо'чий день|phr|working day|iş günü
зарпла'та|n f|salary; wages|maaş; ücret
цена'|n f|price|fiyat
сто'имость|n f|cost; value|maliyet; değer
рубль|n m|rouble|ruble
копе'йка|n f|kopeck|kopek
до'ллар|n m|dollar|dolar
е'вро|n n|euro|euro
креди'т|n m|credit; loan|kredi
ка'рточка|n f|card (bank)|kart (banka)
нали'чные|n pl|cash|nakit
сда'ча|n f|change (money)|para üstü
ски'дка|n f|discount|indirim
беспла'тно|adv|free of charge|ücretsiz; bedava
пода'ть|v pf|to submit; to serve|vermek; sunmak
догово'р|n m|contract; agreement|sözleşme; anlaşma
докуме'нт|n m|document|belge
по'дпись|n f|signature|imza
собра'ние|n n|meeting|toplantı
встре'ча|n f|meeting; encounter|buluşma; karşılaşma
клие'нт|n m|client; customer|müşteri
това'р|n m|goods; product|mal; ürün
проду'кт|n m|product; food item|ürün; gıda maddesi
услу'га|n f|service|hizmet
о'чередь|n f|queue; turn|sıra; kuyruk
рекла'ма|n f|advertising|reklam
успе'х|n m|success|başarı
неуда'ча|n f|failure; bad luck|başarısızlık; şanssızlık
пробле'ма|n f|problem|sorun; problem
план|n m|plan|plan
цель|n f|goal; aim|amaç; hedef
результа'т|n m|result|sonuç
прое'кт|n m|project|proje
# ---- iletisim / teknoloji ----
интерне'т|n m|internet|internet
сайт|n m|website|web sitesi
электро'нная по'чта|phr|e-mail|e-posta
сообще'ние|n n|message|mesaj; ileti
но'мер|n m|number; room (hotel)|numara; oda (otel)
звоно'к|n m|call; bell; ring|arama (telefon); zil
свя'зь|n f|connection; communication|bağlantı; iletişim
но'вости|n pl|news|haberler
информа'ция|n f|information|bilgi
програ'мма|n f|programme; program|program
приложе'ние|n n|application; app|uygulama
экра'н|n m|screen|ekran
кно'пка|n f|button|düğme; tuş
клавиату'ра|n f|keyboard|klavye
мы'шка|n f|mouse (computer)|fare (bilgisayar)
файл|n m|file|dosya
па'пка|n f|folder|klasör
паро'ль|n m|password|şifre; parola
ра'дио|n n|radio|radyo
му'зыка|n f|music|müzik
пе'сня|n f|song|şarkı
фильм|n m|film; movie|film
сериа'л|n m|TV series|dizi
игра'|n f|game; play|oyun
фо'то|n n|photo|fotoğraf
ка'мера|n f|camera|kamera
батаре'я|n f|battery; radiator|pil; batarya; kalorifer peteği
заряжа'ть|v ipf|to charge (battery)|şarj etmek
включа'ть|v ipf|to switch on; to include|açmak (cihaz); dahil etmek
включи'ть|v pf|to switch on; to include|açmak (cihaz); dahil etmek
выключа'ть|v ipf|to switch off|kapatmak (cihaz)
вы'ключить|v pf|to switch off|kapatmak (cihaz)
ска'чивать|v ipf|to download|indirmek
скача'ть|v pf|to download|indirmek
# ---- doga / hava ----
приро'да|n f|nature|doğa
пого'да|n f|weather|hava (durumu)
со'лнце|n n|sun|güneş
луна'|n f|moon|ay (gökcismi)
звезда'|n f|star|yıldız
не'бо|n n|sky; heaven|gökyüzü; gök
о'блако|n n|cloud|bulut
дождь|n m|rain|yağmur
снег|n m|snow|kar
ве'тер|n m|wind|rüzgâr
гроза'|n f|thunderstorm|fırtına; gök gürültülü fırtına
тума'н|n m|fog|sis
лёд|n m|ice|buz
моро'з|n m|frost|don; ayaz
жара'|n f|heat (weather)|sıcak (hava); sıcaklık
гра'дус|n m|degree|derece
земля'|n f|earth; land; ground|yer; toprak; dünya
мир|n m|world; peace|dünya; barış
во'здух|n m|air|hava
ого'нь|n m|fire|ateş
мо'ре|n n|sea|deniz
о'зеро|n n|lake|göl
река'|n f|river|nehir; ırmak
бе'рег|n m|shore; bank|kıyı; sahil
о'стров|n m|island|ada
гора'|n f|mountain|dağ
лес|n m|forest|orman
по'ле|n n|field|tarla; alan
де'рево|n n|tree; wood|ağaç; tahta
цвето'к|n m|flower|çiçek
трава'|n f|grass|ot; çimen
лист|n m|leaf; sheet|yaprak; sayfa
ка'мень|n m|stone|taş
песо'к|n m|sand|kum
живо'тное|n n|animal|hayvan
соба'ка|n f|dog|köpek
ко'шка|n f|cat|kedi
ло'шадь|n f|horse|at
коро'ва|n f|cow|inek
свинья'|n f|pig|domuz
пти'ца|n f|bird|kuş
медве'дь|n m|bear|ayı
волк|n m|wolf|kurt
лиса'|n f|fox|tilki
за'яц|n m|hare|tavşan (yabani)
мышь|n f|mouse|fare
змея'|n f|snake|yılan
насеко'мое|n n|insect|böcek
идёт дождь|phr|it is raining|yağmur yağıyor
идёт снег|phr|it is snowing|kar yağıyor
хо'лодно|adv|it is cold|soğuk; hava soğuk
жа'рко|adv|it is hot|sıcak; hava sıcak
тепло'|adv|it is warm|ılık; hava ılık
со'лнечно|adv|sunny|güneşli
# ---- spor / bos zaman ----
спорт|n m|sport|spor
футбо'л|n m|football; soccer|futbol
хокке'й|n m|hockey|hokey
те'ннис|n m|tennis|tenis
ша'хматы|n pl|chess|satranç
бассе'йн|n m|swimming pool|havuz; yüzme havuzu
стадио'н|n m|stadium|stadyum
кома'нда|n f|team; command|takım; komut
матч|n m|match (sport)|maç
трениро'вка|n f|training; workout|antrenman
чемпиона'т|n m|championship|şampiyona
побе'да|n f|victory|zafer; galibiyet
хо'бби|n n|hobby|hobi
увлече'ние|n n|hobby; passion|hobi; tutku
конце'рт|n m|concert|konser
вы'ставка|n f|exhibition|sergi
спекта'кль|n m|performance; play (theatre)|gösteri; tiyatro oyunu
вечери'нка|n f|party|parti
день рожде'ния|phr|birthday|doğum günü
пра'здновать|v ipf|to celebrate|kutlamak
отмеча'ть|v ipf|to celebrate; to note|kutlamak; not etmek
# ---- duygular / soyut ----
жизнь|n f|life|hayat; yaşam
смерть|n f|death|ölüm
любо'вь|n f|love|aşk; sevgi
дру'жба|n f|friendship|dostluk; arkadaşlık
сча'стье|n n|happiness|mutluluk
ра'дость|n f|joy|sevinç
го'ре|n n|grief; sorrow|keder; acı
страх|n m|fear|korku
наде'жда|n f|hope|umut
мечта'|n f|dream (aspiration)|hayal; ideal
сон|n m|sleep; dream|uyku; rüya
пра'вда|n f|truth|gerçek; doğru
ложь|n f|lie; falsehood|yalan
мысль|n f|thought|düşünce
иде'я|n f|idea|fikir
мне'ние|n n|opinion|görüş; kanaat
чу'вство|n n|feeling; sense|duygu; his
хара'ктер|n m|character; temper|karakter; huy
настрое'ние|n n|mood|ruh hali; keyif
жела'ние|n n|wish; desire|istek; arzu
интере'с|n m|interest|ilgi; merak
свобо'да|n f|freedom|özgürlük
пра'во|n n|right; law|hak; hukuk
зако'н|n m|law|kanun; yasa
поря'док|n m|order|düzen; sıra
вы'бор|n m|choice|seçim; seçenek
возмо'жность|n f|opportunity; possibility|olanak; imkân; fırsat
причи'на|n f|reason; cause|neden; sebep
сле'дствие|n n|consequence; investigation|sonuç; soruşturma
слу'чай|n m|case; occasion; incident|durum; olay; vaka
спо'соб|n m|way; method|yol; yöntem
усло'вие|n n|condition|koşul; şart
разни'ца|n f|difference|fark
часть|n f|part|parça; kısım
коне'ц|n m|end|son
нача'ло|n n|beginning|başlangıç
середи'на|n f|middle|orta
ме'сто|n n|place; seat|yer; koltuk
сторона'|n f|side|taraf; yan
фо'рма|n f|form; shape; uniform|biçim; şekil; üniforma
вид|n m|view; appearance; kind; aspect|görünüm; manzara; tür
тип|n m|type|tip; tür
ро'д|n m|gender; kind; family line|cins; tür; soy
число'|n n|number; date|sayı; tarih
коли'чество|n n|quantity; amount|miktar; nicelik
ка'чество|n n|quality|kalite; nitelik
вес|n m|weight|ağırlık
о'бщество|n n|society|toplum
госуда'рство|n n|state (country)|devlet
прави'тельство|n n|government|hükümet
наро'д|n m|people; nation|halk; millet
война'|n f|war|savaş
а'рмия|n f|army|ordu
поли'ция|n f|police|polis
культу'ра|n f|culture|kültür
иску'сство|n n|art|sanat
рели'гия|n f|religion|din
# ---- sik fiil kaliplari ----
меня' зову'т|phr|my name is|benim adım
как вас зову'т|phr|what is your name (formal)|adınız ne
мне ну'жно|phr|I need|bana lazım; ihtiyacım var
мне нра'вится|phr|I like|hoşuma gidiyor
у меня' есть|phr|I have|bende var
у меня' нет|phr|I don't have|bende yok
я не понима'ю|phr|I don't understand|anlamıyorum
повтори'те, пожа'луйста|phr|please repeat|lütfen tekrar edin
говори'те ме'дленнее|phr|speak more slowly|daha yavaş konuşun
я не зна'ю|phr|I don't know|bilmiyorum
ско'лько вам лет|phr|how old are you|kaç yaşındasınız
я из Ту'рции|phr|I am from Turkey|ben Türkiye'denim
где нахо'дится|phr|where is (located)|nerede bulunuyor
мо'жно|adv|it is possible; one may|mümkün; olur; -ebilir
нельзя'|adv|it is not allowed; one must not|yasak; olmaz
на'до|adv|it is necessary; must|gerek; lazım
ну'жно|adv|it is necessary; need|gerek; lazım
жаль|adv|it is a pity; sorry|yazık; ne yazık ki
пора'|adv|it is time (to)|vakit geldi; zamanı
ви'дно|adv|evidently; can be seen|görülüyor; belli
слы'шно|adv|can be heard|duyuluyor
поня'тно|adv|clear; understood|anlaşıldı; açık
# ---- ek isimler ----
но'вость|n f|piece of news|haber
откры'тка|n f|postcard|kartpostal
конве'рт|n m|envelope|zarf
посы'лка|n f|parcel|koli; paket
ма'рка|n f|stamp; brand|pul; marka
бага'ж|n m|luggage|bagaj
ке'мпинг|n m|camping|kamp
пляж|n m|beach|plaj
экску'рсия|n f|excursion; guided tour|gezi; tur
гид|n m|guide (person)|rehber
сувени'р|n m|souvenir|hediyelik eşya
фотоаппара'т|n m|camera (photo)|fotoğraf makinesi
про'бка|n f|traffic jam; cork|trafik sıkışıklığı; tıpa; mantar
парко'вка|n f|parking|otopark; park yeri
бензи'н|n m|petrol; gasoline|benzin
шофёр|n m|chauffeur; driver|şoför
пассажи'р|n m|passenger|yolcu
расписа'ние|n n|timetable; schedule|tarife; program
отправле'ние|n n|departure|kalkış; hareket
прибы'тие|n n|arrival|varış
платфо'рма|n f|platform|peron; platform
ваго'н|n m|carriage; wagon|vagon
ка'сса|n f|ticket office; cash desk|gişe; kasa
вход|n m|entrance|giriş
вы'ход|n m|exit|çıkış
у'гол|n m|corner; angle|köşe; açı
светофо'р|n m|traffic light|trafik ışığı
перехо'д|n m|crossing; transition|geçit; geçiş
тротуа'р|n m|pavement; sidewalk|kaldırım
ба'шня|n f|tower|kule
дворе'ц|n m|palace|saray
кре'пость|n f|fortress|kale
па'мятник|n m|monument|anıt
фонта'н|n m|fountain|çeşme; fıskiye
река' Москва'|phr|the Moskva River|Moskova Nehri
# ---- ek fiiller (B1) ----
добива'ться|v ipf|to achieve; to strive for|elde etmeye çalışmak; ulaşmak
дости'гнуть|v pf|to reach; to achieve|ulaşmak; erişmek
развива'ть|v ipf|to develop|geliştirmek
разви'ть|v pf|to develop|geliştirmek
создава'ть|v ipf|to create|yaratmak; oluşturmak
созда'ть|v pf|to create|yaratmak; oluşturmak
уничтожа'ть|v ipf|to destroy|yok etmek; imha etmek
защища'ть|v ipf|to defend; to protect|savunmak; korumak
защити'ть|v pf|to defend; to protect|savunmak; korumak
напада'ть|v ipf|to attack|saldırmak
обсужда'ть|v ipf|to discuss|tartışmak; görüşmek
обсуди'ть|v pf|to discuss|tartışmak; görüşmek
спо'рить|v ipf|to argue; to dispute|tartışmak; münakaşa etmek
соглаша'ться|v ipf|to agree|kabul etmek; razı olmak
согласи'ться|v pf|to agree|kabul etmek; razı olmak
отка'зываться|v ipf|to refuse; to give up|reddetmek; vazgeçmek
отказа'ться|v pf|to refuse; to give up|reddetmek; vazgeçmek
жа'ловаться|v ipf|to complain|şikâyet etmek
благодари'ть|v ipf|to thank|teşekkür etmek
поздравля'ть|v ipf|to congratulate|tebrik etmek; kutlamak
жела'ть|v ipf|to wish|dilemek; istemek
извиня'ться|v ipf|to apologize|özür dilemek
извини'ться|v pf|to apologize|özür dilemek
волнова'ться|v ipf|to worry; to be nervous|endişelenmek; heyecanlanmak
беспоко'иться|v ipf|to worry|endişelenmek; kaygılanmak
серди'ться|v ipf|to be angry|kızmak; sinirlenmek
ра'доваться|v ipf|to be glad; to rejoice|sevinmek
удивля'ться|v ipf|to be surprised|şaşırmak
удиви'ться|v pf|to be surprised|şaşırmak
скуча'ть|v ipf|to miss; to be bored|özlemek; sıkılmak
привыка'ть|v ipf|to get used to|alışmak
привы'кнуть|v pf|to get used to|alışmak
замеча'ть|v ipf|to notice|fark etmek
заме'тить|v pf|to notice|fark etmek
внима'тельно|adv|carefully; attentively|dikkatle; dikkatlice
представля'ть|v ipf|to imagine; to introduce; to present|hayal etmek; tanıtmak; sunmak
предста'вить|v pf|to imagine; to introduce; to present|hayal etmek; tanıtmak; sunmak
опи'сывать|v ipf|to describe|betimlemek; tasvir etmek
описа'ть|v pf|to describe|betimlemek; tasvir etmek
подчёркивать|v ipf|to underline; to emphasize|altını çizmek; vurgulamak
зави'сеть|v ipf|to depend|bağlı olmak
влия'ть|v ipf|to influence|etkilemek
отлича'ться|v ipf|to differ|farklı olmak; ayrılmak
соотве'тствовать|v ipf|to correspond; to match|uymak; karşılık gelmek
производи'ть|v ipf|to produce; to make (an impression)|üretmek; (izlenim) bırakmak
потребля'ть|v ipf|to consume|tüketmek
тра'тить|v ipf|to spend (money, time)|harcamak
потра'тить|v pf|to spend (money, time)|harcamak
эконо'мить|v ipf|to save; to economize|tasarruf etmek; idareli kullanmak
зараба'тывать|v ipf|to earn|kazanmak (para)
зарабо'тать|v pf|to earn|kazanmak (para)
увольня'ть|v ipf|to dismiss; to fire|işten çıkarmak; kovmak
нанима'ть|v ipf|to hire|işe almak; kiralamak
руководи'ть|v ipf|to manage; to lead|yönetmek; başında olmak
управля'ть|v ipf|to manage; to drive; to govern|yönetmek; idare etmek; kullanmak (araç)
слу'жить|v ipf|to serve|hizmet etmek
лечи'ть|v ipf|to treat (medically)|tedavi etmek
вы'лечить|v pf|to cure|iyileştirmek; tedavi etmek
выздора'вливать|v ipf|to recover (health)|iyileşmek
худе'ть|v ipf|to lose weight|zayıflamak; kilo vermek
толсте'ть|v ipf|to gain weight|şişmanlamak; kilo almak
кури'ть|v ipf|to smoke|sigara içmek
"""
