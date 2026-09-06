# -*- coding: utf-8 -*-
"""Gomulu Rusca <-> Ingilizce cekirdek sozluk (A1-B1, ~1000 madde).

Satir bicimi:  vurgulu_kelime|tur [ek]|ingilizce karsilik; karsilik 2
Vurgu, vurgulu sesli harften hemen SONRA gelen tek tirnakla gosterilir (OpenRussian bicimi).
Tur: n v adj adv pron prep conj num part int phr - ek: m f n pl (cinsiyet) / ipf pf (gorunus).
"""

DATA = r"""
# ---- selamlasma / nezaket ----
приве'т|int|hi; hello (informal)
здра'вствуйте|int|hello (formal)
здра'вствуй|int|hello (informal, singular)
до свида'ния|phr|goodbye
пока'|int|bye (informal)
до'брое у'тро|phr|good morning
до'брый день|phr|good afternoon
до'брый ве'чер|phr|good evening
споко'йной но'чи|phr|good night
спаси'бо|int|thank you; thanks
пожа'луйста|int|please; you are welcome
извини'те|int|excuse me; sorry (formal)
прости'те|int|forgive me; sorry
да|part|yes
нет|part|no
хорошо'|adv|well; OK; fine
ла'дно|part|all right; okay
коне'чно|adv|of course
мо'жет быть|phr|maybe; perhaps
как дела'|phr|how are you
ничего'|pron|nothing; not bad
ниче'го стра'шного|phr|no problem; never mind
добро' пожа'ловать|phr|welcome
всего' хоро'шего|phr|all the best
уда'чи|int|good luck
поздравля'ю|int|congratulations
с днём рожде'ния|phr|happy birthday
бу'дьте здоро'вы|phr|bless you; take care
прия'тного аппети'та|phr|enjoy your meal
# ---- soru kelimeleri ----
кто|pron|who
что|pron|what
где|adv|where
куда'|adv|where to
отку'да|adv|where from
когда'|adv|when
почему'|adv|why
заче'м|adv|what for; why
как|adv|how
како'й|pron|which; what kind of
чей|pron|whose
ско'лько|adv|how much; how many
# ---- zamirler ----
я|pron|I
ты|pron|you (singular, informal)
он|pron|he
она'|pron|she
оно'|pron|it
мы|pron|we
вы|pron|you (plural or formal)
они'|pron|they
мой|pron|my; mine
твой|pron|your; yours (informal)
его'|pron|his; its
её|pron|her; hers
наш|pron|our; ours
ваш|pron|your; yours (formal or plural)
их|pron|their; theirs
свой|pron|one's own
э'тот|pron|this
тот|pron|that
э'то|pron|this; this is
всё|pron|everything; all
все|pron|everyone; all
ка'ждый|pron|each; every
никто'|pron|nobody
ничто'|pron|nothing
кто'-то|pron|someone
что'-то|pron|something
кто'-нибудь|pron|anyone; anybody
что'-нибудь|pron|anything
сам|pron|oneself; myself; himself
себя'|pron|oneself (reflexive)
друг дру'га|phr|each other
# ---- sayilar ----
ноль|num|zero
оди'н|num|one
два|num|two
три|num|three
четы'ре|num|four
пять|num|five
шесть|num|six
семь|num|seven
во'семь|num|eight
де'вять|num|nine
де'сять|num|ten
оди'ннадцать|num|eleven
двена'дцать|num|twelve
трина'дцать|num|thirteen
четы'рнадцать|num|fourteen
пятна'дцать|num|fifteen
шестна'дцать|num|sixteen
семна'дцать|num|seventeen
восемна'дцать|num|eighteen
девятна'дцать|num|nineteen
два'дцать|num|twenty
три'дцать|num|thirty
со'рок|num|forty
пятьдеся'т|num|fifty
шестьдеся'т|num|sixty
се'мьдесят|num|seventy
во'семьдесят|num|eighty
девяно'сто|num|ninety
сто|num|hundred
ты'сяча|num|thousand
миллио'н|num|million
пе'рвый|num|first
второ'й|num|second
тре'тий|num|third
четвёртый|num|fourth
пя'тый|num|fifth
после'дний|adj|last; latest
полови'на|n f|half
раз|n m|time; once
мно'го|adv|much; many; a lot
ма'ло|adv|little; few
не'сколько|num|several; a few
немно'го|adv|a little; a bit
# ---- zaman ----
вре'мя|n n|time
час|n m|hour; o'clock
мину'та|n f|minute
секу'нда|n f|second (time)
день|n m|day
ночь|n f|night
у'тро|n n|morning
ве'чер|n m|evening
неде'ля|n f|week
ме'сяц|n m|month; moon
год|n m|year
сего'дня|adv|today
за'втра|adv|tomorrow
вчера'|adv|yesterday
послеза'втра|adv|the day after tomorrow
позавчера'|adv|the day before yesterday
сейча'с|adv|now; right now
тепе'рь|adv|now (as opposed to before)
пото'м|adv|then; later
ра'ньше|adv|earlier; before
по'здно|adv|late
ра'но|adv|early
всегда'|adv|always
никогда'|adv|never
иногда'|adv|sometimes
ча'сто|adv|often
ре'дко|adv|rarely; seldom
обы'чно|adv|usually
уже'|adv|already
ещё|adv|still; yet; more
давно'|adv|long ago; for a long time
неда'вно|adv|recently
ско'ро|adv|soon
до'лго|adv|for a long time
снача'ла|adv|at first; first
зате'м|adv|then; after that
наконе'ц|adv|finally; at last
понеде'льник|n m|Monday
вто'рник|n m|Tuesday
среда'|n f|Wednesday
четве'рг|n m|Thursday
пя'тница|n f|Friday
суббо'та|n f|Saturday
воскресе'нье|n n|Sunday
янва'рь|n m|January
февра'ль|n m|February
март|n m|March
апре'ль|n m|April
май|n m|May
ию'нь|n m|June
ию'ль|n m|July
а'вгуст|n m|August
сентя'брь|n m|September
октя'брь|n m|October
ноя'брь|n m|November
дека'брь|n m|December
весна'|n f|spring
ле'то|n n|summer
о'сень|n f|autumn; fall
зима'|n f|winter
пра'здник|n m|holiday; celebration
выходно'й|n m|day off; weekend day
кани'кулы|n pl|school holidays; vacation
о'тпуск|n m|vacation; leave
# ---- aile / insanlar ----
челове'к|n m|person; human
лю'ди|n pl|people
мужчи'на|n m|man
же'нщина|n f|woman
ма'льчик|n m|boy
де'вочка|n f|girl (child)
де'вушка|n f|girl; young woman
па'рень|n m|guy; young man; boyfriend
ребёнок|n m|child
де'ти|n pl|children
семья'|n f|family
роди'тели|n pl|parents
мать|n f|mother
ма'ма|n f|mom
оте'ц|n m|father
па'па|n m|dad
сын|n m|son
дочь|n f|daughter
брат|n m|brother
сестра'|n f|sister
ба'бушка|n f|grandmother
де'душка|n m|grandfather
внук|n m|grandson
вну'чка|n f|granddaughter
дя'дя|n m|uncle
тётя|n f|aunt
муж|n m|husband
жена'|n f|wife
друг|n m|friend (male)
подру'га|n f|friend (female)
сосе'д|n m|neighbour
гость|n m|guest
колле'га|n m|colleague
знако'мый|n m|acquaintance
и'мя|n n|first name
фами'лия|n f|surname; last name
во'зраст|n m|age
взро'слый|adj|adult; grown-up
ста'рый|adj|old
молодо'й|adj|young
# ---- meslekler ----
рабо'та|n f|work; job
профе'ссия|n f|profession
врач|n m|doctor; physician
учи'тель|n m|teacher
студе'нт|n m|student (university)
учени'к|n m|pupil; student (school)
инжене'р|n m|engineer
программи'ст|n m|programmer
води'тель|n m|driver
продаве'ц|n m|shop assistant; seller
по'вар|n m|cook; chef
официа'нт|n m|waiter
полице'йский|n m|police officer
журнали'ст|n m|journalist
худо'жник|n m|artist; painter
музыка'нт|n m|musician
актёр|n m|actor
писа'тель|n m|writer
юри'ст|n m|lawyer
бизнесме'н|n m|businessman
дире'ктор|n m|director; manager
нача'льник|n m|boss; chief
секрета'рь|n m|secretary
рабо'чий|n m|worker
строи'тель|n m|builder
медсестра'|n f|nurse
перево'дчик|n m|translator; interpreter
учёный|n m|scientist; scholar
солда'т|n m|soldier
# ---- ev ----
дом|n m|house; home
кварти'ра|n f|flat; apartment
ко'мната|n f|room
ку'хня|n f|kitchen
спа'льня|n f|bedroom
ва'нная|n f|bathroom
туале'т|n m|toilet
коридо'р|n m|corridor; hallway
балко'н|n m|balcony
эта'ж|n m|floor; storey
лифт|n m|lift; elevator
ле'стница|n f|stairs; ladder
дверь|n f|door
окно'|n n|window
стена'|n f|wall
пол|n m|floor
потоло'к|n m|ceiling
кры'ша|n f|roof
ме'бель|n f|furniture
стол|n m|table; desk
стул|n m|chair
кре'сло|n n|armchair
дива'н|n m|sofa; couch
крова'ть|n f|bed
шкаф|n m|wardrobe; cupboard
по'лка|n f|shelf
зе'ркало|n n|mirror
ла'мпа|n f|lamp
свет|n m|light
ковёр|n m|carpet; rug
карти'на|n f|picture; painting
холоди'льник|n m|fridge; refrigerator
плита'|n f|stove; cooker
духо'вка|n f|oven
микроволно'вка|n f|microwave
стира'льная маши'на|phr|washing machine
телеви'зор|n m|television set
ключ|n m|key
замо'к|n m|lock
му'сор|n m|rubbish; garbage
убира'ть|v ipf|to clean; to tidy up
убра'ть|v pf|to clean; to tidy up
мыть|v ipf|to wash
помы'ть|v pf|to wash
гото'вить|v ipf|to cook; to prepare
пригото'вить|v pf|to cook; to prepare
# ---- gunluk esyalar ----
вещь|n f|thing; item
су'мка|n f|bag; handbag
рюкза'к|n m|backpack
чемода'н|n m|suitcase
кошелёк|n m|wallet; purse
де'ньги|n pl|money
телефо'н|n m|phone
компью'тер|n m|computer
ноутбу'к|n m|laptop
часы'|n pl|clock; watch
очки'|n pl|glasses; spectacles
зо'нт|n m|umbrella
кни'га|n f|book
тетра'дь|n f|notebook; exercise book
ру'чка|n f|pen; handle
каранда'ш|n m|pencil
бума'га|n f|paper
письмо'|n n|letter (mail)
газе'та|n f|newspaper
журна'л|n m|magazine
карти'нка|n f|small picture; image
фотогра'фия|n f|photograph
пода'рок|n m|gift; present
игру'шка|n f|toy
мяч|n m|ball
сигаре'та|n f|cigarette
спи'чки|n pl|matches
# ---- kiyafet ----
оде'жда|n f|clothes; clothing
руба'шка|n f|shirt
футбо'лка|n f|T-shirt
брю'ки|n pl|trousers; pants
джи'нсы|n pl|jeans
ю'бка|n f|skirt
пла'тье|n n|dress
пальто'|n n|coat
ку'ртка|n f|jacket
костю'м|n m|suit; costume
сви'тер|n m|sweater
ша'пка|n f|hat; cap (warm)
шля'па|n f|hat (with brim)
шарф|n m|scarf
перча'тки|n pl|gloves
носки'|n pl|socks
о'бувь|n f|footwear
боти'нки|n pl|boots; shoes
ту'фли|n pl|shoes (dress)
кроссо'вки|n pl|sneakers; trainers
разме'р|n m|size
надева'ть|v ipf|to put on (clothes)
наде'ть|v pf|to put on (clothes)
снима'ть|v ipf|to take off; to rent; to film
снять|v pf|to take off; to rent; to film
носи'ть|v ipf|to wear; to carry
# ---- vucut / saglik ----
те'ло|n n|body
голова'|n f|head
лицо'|n n|face
глаз|n m|eye
у'хо|n n|ear
нос|n m|nose
рот|n m|mouth
зуб|n m|tooth
губа'|n f|lip
во'лосы|n pl|hair
ше'я|n f|neck
плечо'|n n|shoulder
рука'|n f|hand; arm
па'лец|n m|finger; toe
нога'|n f|leg; foot
коле'но|n n|knee
спина'|n f|back (body)
живо'т|n m|stomach; belly
се'рдце|n n|heart
кровь|n f|blood
кость|n f|bone
ко'жа|n f|skin; leather
здоро'вье|n n|health
здоро'вый|adj|healthy
больно'й|adj|sick; ill; patient
боле'знь|n f|illness; disease
боль|n f|pain; ache
боле'ть|v ipf|to be ill; to hurt
температу'ра|n f|temperature; fever
просту'да|n f|cold (illness)
ка'шель|n m|cough
лека'рство|n n|medicine; drug
табле'тка|n f|pill; tablet
апте'ка|n f|pharmacy; chemist
больни'ца|n f|hospital
поликли'ника|n f|clinic
ско'рая по'мощь|phr|ambulance
уста'лый|adj|tired
устава'ть|v ipf|to get tired
уста'ть|v pf|to get tired
спать|v ipf|to sleep
засыпа'ть|v ipf|to fall asleep
засну'ть|v pf|to fall asleep
просыпа'ться|v ipf|to wake up
просну'ться|v pf|to wake up
отдыха'ть|v ipf|to rest; to relax
отдохну'ть|v pf|to rest; to relax
# ---- yiyecek / icecek ----
еда'|n f|food
за'втрак|n m|breakfast
обе'д|n m|lunch; dinner (midday meal)
у'жин|n m|supper; dinner (evening)
хлеб|n m|bread
ма'сло|n n|butter; oil
сыр|n m|cheese
молоко'|n n|milk
яйцо'|n n|egg
мя'со|n n|meat
ку'рица|n f|chicken; hen
ры'ба|n f|fish
колбаса'|n f|sausage
суп|n m|soup
ка'ша|n f|porridge; kasha
рис|n m|rice
макаро'ны|n pl|pasta
карто'фель|n m|potatoes
карто'шка|n f|potato (colloquial)
о'вощи|n pl|vegetables
фру'кты|n pl|fruit
я'блоко|n n|apple
гру'ша|n f|pear
бана'н|n m|banana
апельси'н|n m|orange
лимо'н|n m|lemon
виногра'д|n m|grapes
я'года|n f|berry
клубни'ка|n f|strawberry
помидо'р|n m|tomato
огуре'ц|n m|cucumber
лук|n m|onion
чесно'к|n m|garlic
капу'ста|n f|cabbage
морко'вь|n f|carrot
гриб|n m|mushroom
соль|n f|salt
са'хар|n m|sugar
пе'рец|n m|pepper
мёд|n m|honey
сла'дкий|adj|sweet
солёный|adj|salty
о'стрый|adj|spicy; sharp
вку'сный|adj|tasty; delicious
све'жий|adj|fresh
торт|n m|cake
пиро'г|n m|pie
пече'нье|n n|cookies; biscuits
шокола'д|n m|chocolate
конфе'та|n f|candy; sweet
моро'женое|n n|ice cream
вода'|n f|water
чай|n m|tea
ко'фе|n m|coffee
сок|n m|juice
пи'во|n n|beer
вино'|n n|wine
во'дка|n f|vodka
буты'лка|n f|bottle
стака'н|n m|glass (drinking)
ча'шка|n f|cup
таре'лка|n f|plate
ло'жка|n f|spoon
ви'лка|n f|fork
нож|n m|knife
кастрю'ля|n f|saucepan; pot
сковорода'|n f|frying pan
магази'н|n m|shop; store
ры'нок|n m|market
рестора'н|n m|restaurant
кафе'|n n|cafe
столо'вая|n f|canteen; dining room
меню'|n n|menu
счёт|n m|bill; account; score
есть|v ipf|to eat; there is
съесть|v pf|to eat (up)
пить|v ipf|to drink
вы'пить|v pf|to drink (up)
за'втракать|v ipf|to have breakfast
обе'дать|v ipf|to have lunch
у'жинать|v ipf|to have dinner
голо'дный|adj|hungry
# ---- sehir / ulasim ----
го'род|n m|city; town
дере'вня|n f|village; countryside
страна'|n f|country
столи'ца|n f|capital city
у'лица|n f|street
пло'щадь|n f|square; area
доро'га|n f|road; way
мост|n m|bridge
парк|n m|park
сад|n m|garden
центр|n m|centre
райо'н|n m|district; area
зда'ние|n n|building
це'рковь|n f|church
музе'й|n m|museum
теа'тр|n m|theatre
кино'|n n|cinema; movies
библиоте'ка|n f|library
шко'ла|n f|school
университе'т|n m|university
банк|n m|bank
по'чта|n f|post office; mail
гости'ница|n f|hotel
вокза'л|n m|railway station
ста'нция|n f|station
остано'вка|n f|stop (bus, tram)
аэропо'рт|n m|airport
метро'|n n|metro; underground
авто'бус|n m|bus
трамва'й|n m|tram
тролле'йбус|n m|trolleybus
маши'на|n f|car; machine
такси'|n n|taxi
по'езд|n m|train
самолёт|n m|plane
кора'бль|n m|ship
велосипе'д|n m|bicycle
биле'т|n m|ticket
па'спорт|n m|passport
ви'за|n f|visa
грани'ца|n f|border
путеше'ствие|n n|journey; travel
пое'здка|n f|trip
тури'ст|n m|tourist
ка'рта|n f|map; card
а'дрес|n m|address
напра'во|adv|to the right
нале'во|adv|to the left
пря'мо|adv|straight ahead; directly
далеко'|adv|far
бли'зко|adv|near; close
здесь|adv|here
тут|adv|here (colloquial)
там|adv|there
туда'|adv|to there
сюда'|adv|to here
до'ма|adv|at home
домо'й|adv|homeward; (to) home
сле'ва|adv|on the left
спра'ва|adv|on the right
# ---- hareket fiilleri ----
идти'|v ipf|to go (on foot, one direction)
ходи'ть|v ipf|to go (on foot, habitually)
пойти'|v pf|to go; to set off (on foot)
е'хать|v ipf|to go (by vehicle, one direction)
е'здить|v ipf|to go (by vehicle, habitually)
пое'хать|v pf|to go; to set off (by vehicle)
бежа'ть|v ipf|to run (one direction)
бе'гать|v ipf|to run (habitually)
лете'ть|v ipf|to fly (one direction)
лета'ть|v ipf|to fly (habitually)
плыть|v ipf|to swim; to sail (one direction)
пла'вать|v ipf|to swim (habitually)
нести'|v ipf|to carry (on foot)
везти'|v ipf|to carry (by vehicle); to be lucky
вести'|v ipf|to lead; to drive
приходи'ть|v ipf|to come; to arrive (on foot)
прийти'|v pf|to come; to arrive (on foot)
уходи'ть|v ipf|to leave; to go away
уйти'|v pf|to leave; to go away
входи'ть|v ipf|to enter
войти'|v pf|to enter
выходи'ть|v ipf|to go out; to exit
вы'йти|v pf|to go out; to exit
приезжа'ть|v ipf|to arrive (by vehicle)
прие'хать|v pf|to arrive (by vehicle)
уезжа'ть|v ipf|to leave (by vehicle)
уе'хать|v pf|to leave (by vehicle)
переходи'ть|v ipf|to cross; to move over
перейти'|v pf|to cross; to move over
возвраща'ться|v ipf|to return; to come back
верну'ться|v pf|to return; to come back
подходи'ть|v ipf|to approach; to suit
подойти'|v pf|to approach; to suit
# ---- temel fiiller ----
быть|v ipf|to be
стать|v pf|to become; to start
станови'ться|v ipf|to become
де'лать|v ipf|to do; to make
сде'лать|v pf|to do; to make
говори'ть|v ipf|to speak; to say; to talk
сказа'ть|v pf|to say; to tell
разгова'ривать|v ipf|to talk; to converse
знать|v ipf|to know
узнава'ть|v ipf|to find out; to recognize
узна'ть|v pf|to find out; to recognize
ду'мать|v ipf|to think
поду'мать|v pf|to think (for a while)
понима'ть|v ipf|to understand
поня'ть|v pf|to understand
хоте'ть|v ipf|to want
мочь|v ipf|to be able; can
смочь|v pf|to be able; to manage
уме'ть|v ipf|to know how; to be able
люби'ть|v ipf|to love; to like
нра'виться|v ipf|to be liked; to please
понра'виться|v pf|to be liked; to please
ви'деть|v ipf|to see
уви'деть|v pf|to see; to catch sight of
смотре'ть|v ipf|to look; to watch
посмотре'ть|v pf|to look; to watch
слы'шать|v ipf|to hear
услы'шать|v pf|to hear
слу'шать|v ipf|to listen
послу'шать|v pf|to listen (for a while)
чита'ть|v ipf|to read
прочита'ть|v pf|to read (through)
писа'ть|v ipf|to write
написа'ть|v pf|to write
жить|v ipf|to live
рабо'тать|v ipf|to work
учи'ться|v ipf|to study; to learn (at a school)
учи'ть|v ipf|to learn; to teach
вы'учить|v pf|to learn (by heart)
научи'ться|v pf|to learn (how to do)
изуча'ть|v ipf|to study (a subject)
игра'ть|v ipf|to play
сыгра'ть|v pf|to play (once)
дава'ть|v ipf|to give
дать|v pf|to give
брать|v ipf|to take
взять|v pf|to take
получа'ть|v ipf|to receive; to get
получи'ть|v pf|to receive; to get
покупа'ть|v ipf|to buy
купи'ть|v pf|to buy
продава'ть|v ipf|to sell
прода'ть|v pf|to sell
плати'ть|v ipf|to pay
заплати'ть|v pf|to pay
сто'ить|v ipf|to cost; to be worth
открыва'ть|v ipf|to open
откры'ть|v pf|to open
закрыва'ть|v ipf|to close
закры'ть|v pf|to close
начина'ть|v ipf|to begin; to start
нача'ть|v pf|to begin; to start
конча'ть|v ipf|to finish
ко'нчить|v pf|to finish
зака'нчивать|v ipf|to finish; to complete
зако'нчить|v pf|to finish; to complete
продолжа'ть|v ipf|to continue
продо'лжить|v pf|to continue
жда'ть|v ipf|to wait
подожда'ть|v pf|to wait (a while)
иска'ть|v ipf|to look for; to search
найти'|v pf|to find
находи'ть|v ipf|to find
теря'ть|v ipf|to lose
потеря'ть|v pf|to lose
по'мнить|v ipf|to remember
запомина'ть|v ipf|to memorize
запо'мнить|v pf|to memorize
забыва'ть|v ipf|to forget
забы'ть|v pf|to forget
спра'шивать|v ipf|to ask (a question)
спроси'ть|v pf|to ask (a question)
проси'ть|v ipf|to ask for; to request
попроси'ть|v pf|to ask for; to request
отвеча'ть|v ipf|to answer; to reply
отве'тить|v pf|to answer; to reply
помога'ть|v ipf|to help
помо'чь|v pf|to help
звони'ть|v ipf|to call (phone); to ring
позвони'ть|v pf|to call (phone); to ring
встреча'ть|v ipf|to meet; to greet
встре'тить|v pf|to meet; to greet
встреча'ться|v ipf|to meet (each other); to date
пока'зывать|v ipf|to show
показа'ть|v pf|to show
расска'зывать|v ipf|to tell; to narrate
рассказа'ть|v pf|to tell; to narrate
объясня'ть|v ipf|to explain
объясни'ть|v pf|to explain
переводи'ть|v ipf|to translate; to transfer
перевести'|v pf|to translate; to transfer
повторя'ть|v ipf|to repeat
повтори'ть|v pf|to repeat
отправля'ть|v ipf|to send
отпра'вить|v pf|to send
посыла'ть|v ipf|to send
посла'ть|v pf|to send
приноси'ть|v ipf|to bring (on foot)
принести'|v pf|to bring (on foot)
класть|v ipf|to put (lying)
положи'ть|v pf|to put (lying)
ста'вить|v ipf|to put (standing); to set
поста'вить|v pf|to put (standing); to set
держа'ть|v ipf|to hold; to keep
сиде'ть|v ipf|to sit; to be sitting
сади'ться|v ipf|to sit down
сесть|v pf|to sit down
стоя'ть|v ipf|to stand
встава'ть|v ipf|to get up; to stand up
встать|v pf|to get up; to stand up
лежа'ть|v ipf|to lie; to be lying
ложи'ться|v ipf|to lie down; to go to bed
лечь|v pf|to lie down; to go to bed
висе'ть|v ipf|to hang; to be hanging
чу'вствовать|v ipf|to feel
почу'вствовать|v pf|to feel
боя'ться|v ipf|to be afraid; to fear
ве'рить|v ipf|to believe; to trust
наде'яться|v ipf|to hope
реша'ть|v ipf|to decide; to solve
реши'ть|v pf|to decide; to solve
про'бовать|v ipf|to try; to taste
попро'бовать|v pf|to try; to taste
стара'ться|v ipf|to try hard; to make an effort
мечта'ть|v ipf|to dream (of)
смея'ться|v ipf|to laugh
улыба'ться|v ipf|to smile
пла'кать|v ipf|to cry; to weep
крича'ть|v ipf|to shout; to scream
петь|v ipf|to sing
спеть|v pf|to sing
танцева'ть|v ipf|to dance
рисова'ть|v ipf|to draw; to paint
нарисова'ть|v pf|to draw; to paint
гуля'ть|v ipf|to walk; to stroll
погуля'ть|v pf|to take a walk
путеше'ствовать|v ipf|to travel
занима'ться|v ipf|to be engaged in; to study
интересова'ться|v ipf|to be interested in
зва'ть|v ipf|to call (by name)
называ'ться|v ipf|to be called (thing)
жени'ться|v ipf|to marry (of a man)
выходи'ть за'муж|phr|to marry (of a woman)
роди'ться|v pf|to be born
умира'ть|v ipf|to die
умере'ть|v pf|to die
расти'|v ipf|to grow
меня'ть|v ipf|to change; to exchange
измени'ть|v pf|to change
изменя'ться|v ipf|to change (oneself)
стро'ить|v ipf|to build
постро'ить|v pf|to build
лома'ть|v ipf|to break
слома'ть|v pf|to break
ремонти'ровать|v ipf|to repair
па'дать|v ipf|to fall
упа'сть|v pf|to fall
броса'ть|v ipf|to throw; to quit
бро'сить|v pf|to throw; to quit
поднима'ть|v ipf|to lift; to raise
подня'ть|v pf|to lift; to raise
дви'гаться|v ipf|to move
остана'вливаться|v ipf|to stop (oneself)
останови'ться|v pf|to stop (oneself)
опа'здывать|v ipf|to be late
опозда'ть|v pf|to be late
спеши'ть|v ipf|to hurry
успева'ть|v ipf|to have time; to manage
успе'ть|v pf|to have time; to manage
пригласи'ть|v pf|to invite
приглаша'ть|v ipf|to invite
предлага'ть|v ipf|to offer; to suggest
предложи'ть|v pf|to offer; to suggest
сове'товать|v ipf|to advise
посове'товать|v pf|to advise
обеща'ть|v ipf|to promise
разреша'ть|v ipf|to allow; to permit
разреши'ть|v pf|to allow; to permit
запреща'ть|v ipf|to forbid
запрети'ть|v pf|to forbid
проверя'ть|v ipf|to check
прове'рить|v pf|to check
выбира'ть|v ipf|to choose; to elect
вы'брать|v pf|to choose; to elect
сравни'вать|v ipf|to compare
сравни'ть|v pf|to compare
счита'ть|v ipf|to count; to consider
посчита'ть|v pf|to count; to calculate
испо'льзовать|v ipf|to use
по'льзоваться|v ipf|to use; to make use of
принима'ть|v ipf|to accept; to take (medicine)
приня'ть|v pf|to accept; to take (medicine)
пла'нировать|v ipf|to plan
организо'вывать|v ipf|to organize
уча'ствовать|v ipf|to take part; to participate
побежда'ть|v ipf|to win; to defeat
победи'ть|v pf|to win; to defeat
прои'грывать|v ipf|to lose (a game)
проигра'ть|v pf|to lose (a game)
случа'ться|v ipf|to happen
случи'ться|v pf|to happen
происходи'ть|v ipf|to happen; to take place
произойти'|v pf|to happen; to take place
каза'ться|v ipf|to seem
означа'ть|v ipf|to mean; to signify
зна'чить|v ipf|to mean
существова'ть|v ipf|to exist
хвата'ть|v ipf|to be enough; to grab
хвати'ть|v pf|to be enough
явля'ться|v ipf|to be (formal); to appear
называ'ть|v ipf|to call; to name
назва'ть|v pf|to call; to name
# ---- sifatlar ----
большо'й|adj|big; large
ма'ленький|adj|small; little
хоро'ший|adj|good
плохо'й|adj|bad
но'вый|adj|new
краси'вый|adj|beautiful; handsome
у'мный|adj|clever; smart
глу'пый|adj|stupid; silly
до'брый|adj|kind; good
злой|adj|angry; evil
весёлый|adj|cheerful; merry
гру'стный|adj|sad
счастли'вый|adj|happy
интере'сный|adj|interesting
ску'чный|adj|boring
ва'жный|adj|important
тру'дный|adj|difficult; hard
лёгкий|adj|easy; light (weight)
сло'жный|adj|complicated; complex
просто'й|adj|simple; plain
дорого'й|adj|expensive; dear
дешёвый|adj|cheap
бога'тый|adj|rich
бе'дный|adj|poor
си'льный|adj|strong
сла'бый|adj|weak
высо'кий|adj|tall; high
ни'зкий|adj|low; short (height)
дли'нный|adj|long
коро'ткий|adj|short
широ'кий|adj|wide; broad
у'зкий|adj|narrow
то'лстый|adj|thick; fat
то'нкий|adj|thin; fine
тяжёлый|adj|heavy; hard
горя'чий|adj|hot (to the touch)
жа'ркий|adj|hot (weather)
холо'дный|adj|cold
тёплый|adj|warm
прохла'дный|adj|cool
бы'стрый|adj|fast; quick
ме'дленный|adj|slow
гро'мкий|adj|loud
ти'хий|adj|quiet
чи'стый|adj|clean; pure
гря'зный|adj|dirty
све'тлый|adj|light; bright
тёмный|adj|dark
я'ркий|adj|bright; vivid
по'лный|adj|full; plump
пусто'й|adj|empty
откры'тый|adj|open
закры'тый|adj|closed
свобо'дный|adj|free; vacant
за'нятый|adj|busy; occupied
гото'вый|adj|ready
пра'вильный|adj|correct; right
непра'вильный|adj|wrong; incorrect
настоя'щий|adj|real; genuine; present
глава'|n f|chapter; head (of)
гла'вный|adj|main; chief
о'бщий|adj|common; general
осо'бенный|adj|special; particular
обы'чный|adj|usual; ordinary
стра'нный|adj|strange
изве'стный|adj|famous; well-known
популя'рный|adj|popular
совреме'нный|adj|modern
дре'вний|adj|ancient
родно'й|adj|native; own (family)
иностра'нный|adj|foreign
ру'сский|adj|Russian
англи'йский|adj|English
туре'цкий|adj|Turkish
неме'цкий|adj|German
францу'зский|adj|French
похо'жий|adj|similar; alike
ра'зный|adj|different; various
одина'ковый|adj|identical; the same
друго'й|adj|other; another
сле'дующий|adj|next; following
про'шлый|adj|last; past
бу'дущий|adj|future; next
ли'чный|adj|personal; private
удо'бный|adj|comfortable; convenient
опа'сный|adj|dangerous
безопа'сный|adj|safe
ве'рный|adj|faithful; correct
че'стный|adj|honest
ве'жливый|adj|polite
серьёзный|adj|serious
смешно'й|adj|funny
мо'крый|adj|wet
сухо'й|adj|dry
мя'гкий|adj|soft
твёрдый|adj|hard; firm
кру'глый|adj|round
живо'й|adj|alive; lively
мёртвый|adj|dead
уве'ренный|adj|confident; sure
дово'льный|adj|satisfied; pleased
# ---- renkler ----
цвет|n m|colour
бе'лый|adj|white
чёрный|adj|black
кра'сный|adj|red
си'ний|adj|blue (dark)
голубо'й|adj|light blue
зелёный|adj|green
жёлтый|adj|yellow
ора'нжевый|adj|orange (colour)
кори'чневый|adj|brown
се'рый|adj|grey
ро'зовый|adj|pink
фиоле'товый|adj|purple; violet
# ---- zarflar / baglaclar / edatlar ----
о'чень|adv|very
сли'шком|adv|too (excessively)
почти'|adv|almost
то'лько|adv|only; just
то'же|adv|also; too
та'кже|adv|also; as well
ещё раз|phr|once more; again
опя'ть|adv|again
сно'ва|adv|again; anew
вме'сте|adv|together
отде'льно|adv|separately
бы'стро|adv|quickly; fast
ме'дленно|adv|slowly
гро'мко|adv|loudly
ти'хо|adv|quietly
пло'хо|adv|badly
пра'вильно|adv|correctly
непра'вильно|adv|incorrectly
легко'|adv|easily
тру'дно|adv|difficult; hard (to do)
интере'сно|adv|interesting; interestingly
ско'лько сто'ит|phr|how much does it cost
наве'рное|adv|probably
обяза'тельно|adv|definitely; without fail
вообще'|adv|in general; at all
осо'бенно|adv|especially
совсе'м|adv|completely; quite
совсе'м не|phr|not at all
дово'льно|adv|rather; quite; enough
доста'точно|adv|enough; sufficiently
приме'рно|adv|approximately
ро'вно|adv|exactly; evenly
вдруг|adv|suddenly
сра'зу|adv|at once; immediately
пока'|conj|while; for now
и|conj|and
а|conj|and; but (contrast)
но|conj|but
и'ли|conj|or
что|conj|that (conjunction)
что'бы|conj|in order to; so that
потому' что|conj|because
поэ'тому|adv|therefore; that is why
е'сли|conj|if
хотя'|conj|although
когда'|conj|when
как то'лько|phr|as soon as
не|part|not
ни|part|neither; nor; not a
ли|part|whether; question particle
же|part|emphatic particle
ведь|part|after all; you know
да'же|part|even
вот|part|here is; there
в|prep|in; at; to
на|prep|on; at; to
с|prep|with; from
у|prep|at; by; near; (have)
к|prep|to; towards
о|prep|about
от|prep|from
до|prep|until; up to
для|prep|for
без|prep|without
по|prep|along; by; according to
за|prep|behind; for; beyond
под|prep|under
над|prep|above; over
пе'ред|prep|in front of; before
ме'жду|prep|between
о'коло|prep|near; about
че'рез|prep|across; through; in (time)
из|prep|from; out of
про|prep|about (colloquial)
по'сле|prep|after
во вре'мя|prep|during
вме'сто|prep|instead of
кро'ме|prep|except; besides
благодаря'|prep|thanks to
и'з-за|prep|because of; from behind
# ---- egitim / dil ----
язы'к|n m|language; tongue
сло'во|n n|word
предложе'ние|n n|sentence; offer; proposal
бу'ква|n f|letter (alphabet)
звук|n m|sound
алфави'т|n m|alphabet
грамма'тика|n f|grammar
слова'рь|n m|dictionary; vocabulary
уро'к|n m|lesson
кла'сс|n m|class; classroom; grade
заня'тие|n n|class; lesson; occupation
ле'кция|n f|lecture
экза'мен|n m|exam
зачёт|n m|pass/fail test
оце'нка|n f|grade; mark; assessment
оши'бка|n f|mistake; error
вопро'с|n m|question
отве'т|n m|answer
пра'вило|n n|rule
приме'р|n m|example
зада'ние|n n|task; assignment
дома'шнее зада'ние|phr|homework
упражне'ние|n n|exercise
текст|n m|text
расска'з|n m|story; short story
исто'рия|n f|history; story
литерату'ра|n f|literature
матема'тика|n f|mathematics
фи'зика|n f|physics
хи'мия|n f|chemistry
биоло'гия|n f|biology
геогра'фия|n f|geography
нау'ка|n f|science
учи'лище|n n|vocational school
факульте'т|n m|faculty; department
курс|n m|course; year (of study)
гру'ппа|n f|group
доска'|n f|board; blackboard
па'рта|n f|school desk
переме'на|n f|break (school); change
зна'ние|n n|knowledge
о'пыт|n m|experience; experiment
зна'чение|n n|meaning; significance
перево'д|n m|translation; transfer
произноше'ние|n n|pronunciation
ударе'ние|n n|stress (word)
па'мять|n f|memory
внима'ние|n n|attention
понима'ть по-ру'сски|phr|to understand Russian
говори'ть по-англи'йски|phr|to speak English
# ---- is / para ----
де'ло|n n|matter; business; affair
би'знес|n m|business
фи'рма|n f|firm; company
компа'ния|n f|company
о'фис|n m|office
заво'д|n m|factory; plant
фа'брика|n f|factory
рабо'чий день|phr|working day
зарпла'та|n f|salary; wages
цена'|n f|price
сто'имость|n f|cost; value
рубль|n m|rouble
копе'йка|n f|kopeck
до'ллар|n m|dollar
е'вро|n n|euro
креди'т|n m|credit; loan
ка'рточка|n f|card (bank)
нали'чные|n pl|cash
сда'ча|n f|change (money)
ски'дка|n f|discount
беспла'тно|adv|free of charge
пода'ть|v pf|to submit; to serve
догово'р|n m|contract; agreement
докуме'нт|n m|document
по'дпись|n f|signature
собра'ние|n n|meeting
встре'ча|n f|meeting; encounter
клие'нт|n m|client; customer
това'р|n m|goods; product
проду'кт|n m|product; food item
услу'га|n f|service
о'чередь|n f|queue; turn
рекла'ма|n f|advertising
успе'х|n m|success
неуда'ча|n f|failure; bad luck
пробле'ма|n f|problem
план|n m|plan
цель|n f|goal; aim
результа'т|n m|result
прое'кт|n m|project
# ---- iletisim / teknoloji ----
интерне'т|n m|internet
сайт|n m|website
электро'нная по'чта|phr|e-mail
сообще'ние|n n|message
но'мер|n m|number; room (hotel)
звоно'к|n m|call; bell; ring
свя'зь|n f|connection; communication
но'вости|n pl|news
информа'ция|n f|information
програ'мма|n f|programme; program
приложе'ние|n n|application; app
экра'н|n m|screen
кно'пка|n f|button
клавиату'ра|n f|keyboard
мы'шка|n f|mouse (computer)
файл|n m|file
па'пка|n f|folder
паро'ль|n m|password
ра'дио|n n|radio
му'зыка|n f|music
пе'сня|n f|song
фильм|n m|film; movie
сериа'л|n m|TV series
игра'|n f|game; play
фо'то|n n|photo
ка'мера|n f|camera
батаре'я|n f|battery; radiator
заряжа'ть|v ipf|to charge (battery)
включа'ть|v ipf|to switch on; to include
включи'ть|v pf|to switch on; to include
выключа'ть|v ipf|to switch off
вы'ключить|v pf|to switch off
ска'чивать|v ipf|to download
скача'ть|v pf|to download
# ---- doga / hava ----
приро'да|n f|nature
пого'да|n f|weather
со'лнце|n n|sun
луна'|n f|moon
звезда'|n f|star
не'бо|n n|sky; heaven
о'блако|n n|cloud
дождь|n m|rain
снег|n m|snow
ве'тер|n m|wind
гроза'|n f|thunderstorm
тума'н|n m|fog
лёд|n m|ice
моро'з|n m|frost
жара'|n f|heat (weather)
гра'дус|n m|degree
земля'|n f|earth; land; ground
мир|n m|world; peace
во'здух|n m|air
ого'нь|n m|fire
мо'ре|n n|sea
о'зеро|n n|lake
река'|n f|river
бе'рег|n m|shore; bank
о'стров|n m|island
гора'|n f|mountain
лес|n m|forest
по'ле|n n|field
де'рево|n n|tree; wood
цвето'к|n m|flower
трава'|n f|grass
лист|n m|leaf; sheet
ка'мень|n m|stone
песо'к|n m|sand
живо'тное|n n|animal
соба'ка|n f|dog
ко'шка|n f|cat
ло'шадь|n f|horse
коро'ва|n f|cow
свинья'|n f|pig
пти'ца|n f|bird
медве'дь|n m|bear
волк|n m|wolf
лиса'|n f|fox
за'яц|n m|hare
мышь|n f|mouse
змея'|n f|snake
насеко'мое|n n|insect
идёт дождь|phr|it is raining
идёт снег|phr|it is snowing
хо'лодно|adv|it is cold
жа'рко|adv|it is hot
тепло'|adv|it is warm
со'лнечно|adv|sunny
# ---- spor / bos zaman ----
спорт|n m|sport
футбо'л|n m|football; soccer
хокке'й|n m|hockey
те'ннис|n m|tennis
ша'хматы|n pl|chess
бассе'йн|n m|swimming pool
стадио'н|n m|stadium
кома'нда|n f|team; command
матч|n m|match (sport)
трениро'вка|n f|training; workout
чемпиона'т|n m|championship
побе'да|n f|victory
хо'бби|n n|hobby
увлече'ние|n n|hobby; passion
конце'рт|n m|concert
вы'ставка|n f|exhibition
спекта'кль|n m|performance; play (theatre)
вечери'нка|n f|party
день рожде'ния|phr|birthday
пра'здновать|v ipf|to celebrate
отмеча'ть|v ipf|to celebrate; to note
# ---- duygular / soyut ----
жизнь|n f|life
смерть|n f|death
любо'вь|n f|love
дру'жба|n f|friendship
сча'стье|n n|happiness
ра'дость|n f|joy
го'ре|n n|grief; sorrow
страх|n m|fear
наде'жда|n f|hope
мечта'|n f|dream (aspiration)
сон|n m|sleep; dream
пра'вда|n f|truth
ложь|n f|lie; falsehood
мысль|n f|thought
иде'я|n f|idea
мне'ние|n n|opinion
чу'вство|n n|feeling; sense
хара'ктер|n m|character; temper
настрое'ние|n n|mood
жела'ние|n n|wish; desire
интере'с|n m|interest
свобо'да|n f|freedom
пра'во|n n|right; law
зако'н|n m|law
поря'док|n m|order
вы'бор|n m|choice
возмо'жность|n f|opportunity; possibility
причи'на|n f|reason; cause
сле'дствие|n n|consequence; investigation
слу'чай|n m|case; occasion; incident
спо'соб|n m|way; method
усло'вие|n n|condition
разни'ца|n f|difference
часть|n f|part
коне'ц|n m|end
нача'ло|n n|beginning
середи'на|n f|middle
ме'сто|n n|place; seat
сторона'|n f|side
фо'рма|n f|form; shape; uniform
вид|n m|view; appearance; kind; aspect
тип|n m|type
ро'д|n m|gender; kind; family line
число'|n n|number; date
коли'чество|n n|quantity; amount
ка'чество|n n|quality
вес|n m|weight
о'бщество|n n|society
госуда'рство|n n|state (country)
прави'тельство|n n|government
наро'д|n m|people; nation
война'|n f|war
а'рмия|n f|army
поли'ция|n f|police
культу'ра|n f|culture
иску'сство|n n|art
рели'гия|n f|religion
# ---- sik fiil kaliplari ----
меня' зову'т|phr|my name is
как вас зову'т|phr|what is your name (formal)
мне ну'жно|phr|I need
мне нра'вится|phr|I like
у меня' есть|phr|I have
у меня' нет|phr|I don't have
я не понима'ю|phr|I don't understand
повтори'те, пожа'луйста|phr|please repeat
говори'те ме'дленнее|phr|speak more slowly
я не зна'ю|phr|I don't know
ско'лько вам лет|phr|how old are you
я из Ту'рции|phr|I am from Turkey
где нахо'дится|phr|where is (located)
мо'жно|adv|it is possible; one may
нельзя'|adv|it is not allowed; one must not
на'до|adv|it is necessary; must
ну'жно|adv|it is necessary; need
жаль|adv|it is a pity; sorry
пора'|adv|it is time (to)
ви'дно|adv|evidently; can be seen
слы'шно|adv|can be heard
поня'тно|adv|clear; understood
# ---- ek isimler ----
но'вость|n f|piece of news
откры'тка|n f|postcard
конве'рт|n m|envelope
посы'лка|n f|parcel
ма'рка|n f|stamp; brand
бага'ж|n m|luggage
ке'мпинг|n m|camping
пляж|n m|beach
экску'рсия|n f|excursion; guided tour
гид|n m|guide (person)
сувени'р|n m|souvenir
фотоаппара'т|n m|camera (photo)
про'бка|n f|traffic jam; cork
парко'вка|n f|parking
бензи'н|n m|petrol; gasoline
шофёр|n m|chauffeur; driver
пассажи'р|n m|passenger
расписа'ние|n n|timetable; schedule
отправле'ние|n n|departure
прибы'тие|n n|arrival
платфо'рма|n f|platform
ваго'н|n m|carriage; wagon
ка'сса|n f|ticket office; cash desk
вход|n m|entrance
вы'ход|n m|exit
у'гол|n m|corner; angle
светофо'р|n m|traffic light
перехо'д|n m|crossing; transition
тротуа'р|n m|pavement; sidewalk
ба'шня|n f|tower
дворе'ц|n m|palace
кре'пость|n f|fortress
па'мятник|n m|monument
фонта'н|n m|fountain
река' Москва'|phr|the Moskva River
# ---- ek fiiller (B1) ----
добива'ться|v ipf|to achieve; to strive for
дости'гнуть|v pf|to reach; to achieve
развива'ть|v ipf|to develop
разви'ть|v pf|to develop
создава'ть|v ipf|to create
созда'ть|v pf|to create
уничтожа'ть|v ipf|to destroy
защища'ть|v ipf|to defend; to protect
защити'ть|v pf|to defend; to protect
напада'ть|v ipf|to attack
обсужда'ть|v ipf|to discuss
обсуди'ть|v pf|to discuss
спо'рить|v ipf|to argue; to dispute
соглаша'ться|v ipf|to agree
согласи'ться|v pf|to agree
отка'зываться|v ipf|to refuse; to give up
отказа'ться|v pf|to refuse; to give up
жа'ловаться|v ipf|to complain
благодари'ть|v ipf|to thank
поздравля'ть|v ipf|to congratulate
жела'ть|v ipf|to wish
извиня'ться|v ipf|to apologize
извини'ться|v pf|to apologize
волнова'ться|v ipf|to worry; to be nervous
беспоко'иться|v ipf|to worry
серди'ться|v ipf|to be angry
ра'доваться|v ipf|to be glad; to rejoice
удивля'ться|v ipf|to be surprised
удиви'ться|v pf|to be surprised
скуча'ть|v ipf|to miss; to be bored
привыка'ть|v ipf|to get used to
привы'кнуть|v pf|to get used to
замеча'ть|v ipf|to notice
заме'тить|v pf|to notice
внима'тельно|adv|carefully; attentively
представля'ть|v ipf|to imagine; to introduce; to present
предста'вить|v pf|to imagine; to introduce; to present
опи'сывать|v ipf|to describe
описа'ть|v pf|to describe
подчёркивать|v ipf|to underline; to emphasize
зави'сеть|v ipf|to depend
влия'ть|v ipf|to influence
отлича'ться|v ipf|to differ
соотве'тствовать|v ipf|to correspond; to match
производи'ть|v ipf|to produce; to make (an impression)
потребля'ть|v ipf|to consume
тра'тить|v ipf|to spend (money, time)
потра'тить|v pf|to spend (money, time)
эконо'мить|v ipf|to save; to economize
зараба'тывать|v ipf|to earn
зарабо'тать|v pf|to earn
увольня'ть|v ipf|to dismiss; to fire
нанима'ть|v ipf|to hire
руководи'ть|v ipf|to manage; to lead
управля'ть|v ipf|to manage; to drive; to govern
слу'жить|v ipf|to serve
лечи'ть|v ipf|to treat (medically)
вы'лечить|v pf|to cure
выздора'вливать|v ipf|to recover (health)
худе'ть|v ipf|to lose weight
толсте'ть|v ipf|to gain weight
кури'ть|v ipf|to smoke
"""
