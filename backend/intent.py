"""Rule-based intent detection for English, Hindi, Kannada and Tamil. No ML model needed for the MVP.

Priority matters: safety intents are checked first, then everything else.
"""
import re

# ---------- keyword tables ----------
# ASCII keywords match on word boundaries; non-ASCII keywords match as substrings.

KEYWORDS = {
    "emergency": [
        "chest pain", "can't breathe", "cannot breathe", "fell down", "i fell", "fallen", "bleeding",
        "dizzy", "emergency", "ambulance", "pain", "hurt", "hurts",
        "दर्द", "सीने", "साँस", "सांस", "गिर गया", "गिर गई", "चक्कर", "बचाओ", "खून", "एम्बुलेंस",
        "ನೋವು", "ಎದೆ ನೋವು", "ಉಸಿರ", "ಬಿದ್ದ", "ತಲೆ ಸುತ್ತ", "ರಕ್ತ", "ಆಂಬ್ಯುಲೆನ್ಸ್",
        "வலி", "நெஞ்சு", "மூச்சு", "விழுந்", "மயக்கம", "இரத்தம்", "ஆம்புலன்ஸ்",
    ],
    "medication": [
        "medicine", "medicines", "tablet", "tablets", "pill", "pills", "dose", "injection",
        "दवा", "दवाई", "गोली", "खुराक",
        "ಔಷಧ", "ಮಾತ್ರೆ", "ಗುಳಿಗೆ",
        "மருந்து", "மாத்திரை",
    ],
    "help": [
        "help", "help me", "need help",
        "मदद", "सहायता",
        "ಸಹಾಯ",
        "உதவி",
    ],
    "who_am_i": [
        "who am i", "what is my name", "my name",
        "मैं कौन", "मेरा नाम",
        "ನಾನು ಯಾರು", "ನನ್ನ ಹೆಸರು",
        "நான் யார்", "என் பெயர்",
    ],
    "confusion": [
        "where am i", "what is this place", "confused", "i am lost", "i'm lost", "don't know where",
        "मैं कहाँ", "मैं कहां", "भूल गया", "भूल गई", "खो गया", "खो गई",
        "ನಾನು ಎಲ್ಲಿ", "ಕಳೆದು", "ಮರೆತ", "ಗೊಂದಲ",
        "நான் எங்கே", "நான் எங்க", "மறந்த", "தொலைந்", "குழப்பம",
    ],
    "distress": [
        "scared", "afraid", "lonely", "alone", "sad", "crying", "worried", "miss", "frightened",
        "डर", "अकेला", "अकेली", "उदास", "रो रहा", "रो रही", "चिंता", "याद आ",
        "ಭಯ", "ಒಂಟಿ", "ದುಃಖ", "ಅಳು", "ಚಿಂತೆ", "ನೆನಪಾಗ",
        "பயம", "தனிமை", "தனியாக", "வருத்த", "அழுகை", "அழுகிறேன்", "கவலை",
    ],
    "hungry": [
        "hungry", "starving", "want to eat", "want food", "need food",
        "भूख", "खाना चाहिए",
        "ಹಸಿವ", "ಊಟ ಬೇಕು",
        "பசி", "சாப்பிட வேண்டும்",
    ],
    "thirsty": [
        "thirsty", "water", "drink",
        "प्यास", "पानी",
        "ಬಾಯಾರಿಕೆ", "ದಾಹ", "ನೀರು",
        "தாகம", "தண்ணீர",
    ],
    "call": [
        "talk to", "speak to", "call", "phone", "meet", "see my", "want to see",
        "बात", "फोन", "मिलना", "बुला",
        "ಮಾತನಾಡ", "ಫೋನ್", "ಕರೆ", "ನೋಡ",
        "பேச", "அழை", "பார்க்க", "போன்",
    ],
    "where": [
        "where", "when will", "coming", "when is",
        "कहाँ", "कहां", "कब आ", "कब आएगी", "कब आएगा",
        "ಎಲ್ಲಿ", "ಯಾವಾಗ",
        "எங்கே", "எங்க", "எப்போது", "எப்ப",
    ],
    "food": [
        "food", "eat", "dish", "meal",
        "खाना", "खाने", 
        "ಊಟ", "ತಿಂಡಿ", "ತಿನ್ನ",
        "சாப்பா", "உணவு", 
    ],
    "song": [
        "song", "songs", "music", "sing",
        "गाना", "गाने", "गीत", "संगीत",
        "ಹಾಡು", "ಹಾಡ", "ಸಂಗೀತ",
        "பாட்டு", "பாடல்", "இசை",
    ],
    "place": [
        "place", "places", "visit", "temple", "village", "favourite place", "favorite place",
        "जगह", "घूम", "मंदिर", "गाँव",
        "ಸ್ಥಳ", "ಜಾಗ", "ಊರು", "ದೇವಸ್ಥಾನ",
        "இடம்", "ஊர்", "கோவில",
    ],
    "hobby": [
        "hobby", "hobbies", "garden", "gardening", "like to do",
        "शौक",
        "ಹವ್ಯಾಸ",
        "பொழுதுபோக்கு",
    ],
    "reminder": [
        "today", "tomorrow", "reminder", "schedule", "appointment", "event", "festival", "birthday", "plan",
        "आज", "कल", "ನಾಳೆ", "ಇಂದು", "இன்று", "நாளை", "याद दिला", "कार्यक्रम", "त्योहार", "जन्मदिन",
        "ಇಂದು", "ನಾಳೆ", "ನೆನಪಿಸು", "ಕಾರ್ಯಕ್ರಮ", "ಹಬ್ಬ", "ಹುಟ್ಟುಹಬ್ಬ",
        "இன்று", "நாளை", "நினைவூட்டு", "நிகழ்ச்சி", "பண்டிகை", "பிறந்தநாள",
    ],
    "memory": [
        "remember", "childhood", "story", "past", "tell me about", "wedding", "job", "work",
        "बचपन", "कहानी", "याद", "शादी", "नौकरी",
        "ಬಾಲ್ಯ", "ಕಥೆ", "ನೆನಪು", "ಮದುವೆ", "ಕೆಲಸ",
        "குழந்தைப் பருவ", "கதை", "நினைவு", "திருமணம", "வேலை",
    ],
    "reassure": [
        "is everything ok", "is everything okay", "all okay", "am i okay", "safe",
        "सब ठीक", "ठीक हूँ", "सुरक्षित",
        "ಸರಿಯಾ", "ಸುರಕ್ಷಿತ",
        "சரியா", "பாதுகாப்பு",
    ],
    "greeting": [
        "hello", "hi", "hey", "good morning", "good evening", "good afternoon", "how are you",
        "नमस्ते", "नमस्कार", "सुप्रभात",
        "ನಮಸ್ಕಾರ", "ಹಲೋ",
        "வணக்கம", "ஹலோ",
    ],
}

# Tamil entries are word stems on purpose: Tamil adds endings (மகள் -> மகளிடம்), so we match the stem.
# Relations: English key -> words in each language. Order matters ("grandchild" first, because
# the Kannada word for grandchild contains the word for son).
RELATIONS = {
    "grandchild": ["grandson", "granddaughter", "grandchild", "पोता", "पोती", "नाती", "ಮೊಮ್ಮಗ", "பேரன", "பேத்த"],
    "daughter": ["daughter", "बेटी", "बिटिया", "ಮಗಳು", "ಮಗಳ", "மகள"],
    "son": ["son", "बेटा", "बेटे", "ಮಗ", "மகன"],
    "wife": ["wife", "पत्नी", "बीवी", "ಹೆಂಡತಿ", "மனைவ"],
    "husband": ["husband", "पति", "ಗಂಡ", "கணவர"],
    "mother": ["mother", "mom", "mummy", "माँ", "मां", "मम्मी", "ಅಮ್ಮ", "ತಾಯಿ", "அம்ம"],
    "father": ["father", "dad", "papa", "पिता", "पापा", "ಅಪ್ಪ", "ತಂದೆ", "அப்ப", "தந்தை"],
    "brother": ["brother", "भाई", "ಅಣ್ಣ", "ತಮ್ಮ", "அண்ணன", "தம்ப"],
    "sister": ["sister", "बहन", "ಅಕ್ಕ", "ತಂಗಿ", "அக்க", "தங்கை"],
}

# intent -> memory category used for lookup
INTENT_TO_CATEGORIES = {
    "food": ["food"],
    "song": ["song"],
    "place": ["place"],
    "hobby": ["hobby"],
    "memory": ["life_event", "other"],
}

# Order of checks (first hit wins). Family intents are handled separately below.
PRIORITY = [
    "emergency", "medication", "help", "who_am_i", "confusion", "distress", "hungry", "thirsty",
]

# "I am not hungry" must not raise a hunger alert
NEGATIONS = ["not", "no", "dont", "don't", "never", "नहीं", "नही", "ಇಲ್ಲ", "இல்லை", "இல்ல"]
AFTER_FAMILY = ["food", "song", "place", "hobby", "reminder", "memory", "reassure", "greeting"]



# ======================================================================
# Tanglish: Tamil written in English letters ("en magal enga?", "enakku pasikkuthu").
# Prisma may return a code-mixed sentence in Latin script, and people type it that way too.
# Spellings vary a lot (magal/makal, thagam/dhagam), so most entries are word *beginnings* (stems);
# short common words are matched whole so they cannot fire inside English words ("enga" vs "engage").
# ======================================================================
TANGLISH_EXACT = {
    "greeting": ["vanakkam", "vanakam", "vanakkamma"],
    "where": ["enga", "enge", "engae", "eppo", "eppodhu", "eppothu"],
    "who_am_i": ["en peyar", "en peru", "en per"],
    "confusion": ["naan enga", "nan enga"],
    "food": ["saapadu", "sapadu", "saappadu", "tiffin"],
    "reminder": ["inniku", "inniki", "indru", "naalai", "naalaiku", "naalaikku"],
    "reassure": ["ellam sari", "ellam seri", "ellam okay"],
    "help": ["udhavi", "uthavi"],
}
TANGLISH_STEMS = {
    "emergency": ["nenju vali", "nenju vaali", "nenju valikk", "valikk", "valikud", "valikir", "moochu", "mooch thin",
                  "vizhund", "vizhunt", "mayakk", "mayakam", "raththam", "ratham", "ambulans"],
    "medication": ["marundh", "marunth", "maruth", "maathirai", "mathirai"],
    "help": ["udhavi", "uthavi"],
    "confusion": ["marandh", "maranth", "marant", "kuzhapp", "kulapp", "kuzhamb"],
    "distress": ["payam", "bayam", "bhayam", "thaniy", "thanimai", "kavalai", "kavala", "varutham", "varuththam",
                 "azhugai", "alugai", "azhuk", "azhar", "ninaivu varu", "miss pann"],
    "hungry": ["pasi", "pasik", "saapadu venum", "sapadu venum", "saappadu venum"],
    "thirsty": ["thagam", "dhagam", "daagam", "thaagam", "dhaagam", "thanni", "thaneer"],
    "call": ["pesanum", "pesanu", "pesa ven", "paakanum", "parkanum", "paarkanum"],
    "food": ["unavu", "unavai"],
    "song": ["paatu", "paattu", "paadal", "paadalg", "isai"],
    "place": ["kovil", "koyil", "idam", "ooru"],
    "memory": ["gnabagam", "nyabagam", "gnyabagam", "nyabaga", "kadhai", "kathai"],
    "greeting": [],
}
RELATION_STEMS = {   # Tanglish relation words, tried in the same order as RELATIONS (grandchild first)
    "grandchild": ["perakuzhand", "perakulan", "peran", "pethi", "perapillai"],
    "daughter": ["magal", "makal", "magaz", "ponnu"],
    "son": ["magan", "makan", "paiyan", "payyan"],
    "wife": ["manaivi", "pondatti"],
    "husband": ["kanavar", "purushan", "purusan"],
    "mother": ["ammaa"],
    "father": ["appaa"],
    "brother": ["annan", "thambi", "thambi"],
    "sister": ["thangai", "thangachi", "thangacci"],
}
# short whole words that are safe to match exactly
RELATION_TANGLISH_EXACT = {"mother": ["amma", "mummy"], "father": ["appa"], "brother": ["anna"], "sister": ["akka"]}
TANGLISH_NEGATIONS = ["illa", "illai", "illaye", "vendam", "venam", "venaam", "vendaam"]
TANGLISH_YES = {"aama", "aamam", "amam", "aam", "seri", "sari"}
TANGLISH_NO = {"illa", "illai", "vendam", "venam", "venaam", "vendaam"}

# ======================================================================
# Hinglish (Hindi in English letters) and Kanglish (Kannada in English letters), same idea as Tanglish.
# "exact" = whole words (safe inside English sentences), "stems" = word beginnings, "rel_*" = relation words.
# "signals" = common little words that only help decide WHICH language it is ("hai", "nanna"...).
# ======================================================================
HINGLISH = {
    "exact": {
        "greeting": ["namaste", "namaskar", "pranam"],
        "where": ["kahan", "kahaan", "kidhar", "kab"],
        "who_am_i": ["mera naam", "main kaun", "mai kaun", "mein kaun"],
        "confusion": ["main kahan", "mai kahan", "mein kahan", "bhool gaya", "bhool gayi", "bhul gaya", "bhul gayi",
                      "kho gaya", "kho gayi", "ghar jana", "ghar jaana", "ghar jaunga", "ghar jaungi"],
        "emergency": ["dard", "seene", "saans", "sans", "chakkar", "gir gaya", "gir gayi", "bachao", "khoon", "ambulance"],
        "medication": ["dawai", "dawa", "davai", "dava", "goli", "khurak"],
        "help": ["madad", "sahayata"],
        "distress": ["dar", "darr", "akela", "akeli", "udaas", "udas", "chinta", "ro raha", "ro rahi", "yaad aa", "yaad aati", "yaad aata"],
        "hungry": ["bhook", "bhookh", "bhuk", "bhukh", "khana chahiye"],
        "thirsty": ["pyaas", "pyas", "pyaasa", "pyasa", "paani", "pani"],
        "call": ["baat", "milna", "milni", "bulao", "bula"],
        "food": ["khana", "khane", "khaana", "nashta"],
        "song": ["gaana", "gaane", "gana", "geet", "sangeet", "bhajan"],
        "place": ["jagah", "ghoomna", "mandir", "gaon"],
        "reminder": ["aaj", "kal", "yaad dila", "karyakram", "tyohar", "janamdin"],
        "memory": ["kahani", "kissa", "purani baatein", "purani baatien"],
        "reassure": ["sab theek", "sab thik", "koi baat nahi"],
    },
    "stems": {},
    "rel_exact": {
        "grandchild": ["pota", "poti", "nati", "naati"],
        "daughter": ["beti", "betiya", "bitiya"],
        "son": ["beta", "bete", "betey"],
        "wife": ["patni", "biwi", "bivi"],
        "husband": ["pati", "shauhar"],
        "mother": ["maa", "mummy", "mataji"],
        "father": ["papa", "pitaji"],
        "brother": ["bhai", "bhaiya"],
        "sister": ["behen", "behn", "bahan", "bahen", "didi"],
    },
    "rel_stems": {},
    "signals": ["hai", "hain", "mera", "meri", "mere", "mujhe", "mujhko", "kya", "nahi", "nahin", "haan", "kaun", "kab", "kaise", "bahut", "chahiye"],
    "yes": {"haan", "haa", "han", "ji", "theek", "thik", "achha", "accha", "bilkul", "zaroor"},
    "no": {"nahi", "nahin", "nahee", "nhi"},
}
KANGLISH = {
    "exact": {
        "greeting": ["namaskara", "namaskaram"],
        "where": ["elli", "ellide", "ellidhe", "ellidare", "yelli", "yaavaga"],
        "who_am_i": ["nanna hesaru", "nanna hesru", "naanu yaaru", "nanu yaaru", "nan yaaru"],
        "confusion": ["naanu elli", "nanu elli", "nan elli", "maretidini", "marethe", "marete", "mane hogbeku", "mane hogabeku"],
        "emergency": ["novu", "ede novu", "edenovu", "usiraata", "usiru", "bidde", "biddhe", "raktha", "rakta"],
        "medication": ["maatre", "matre", "aushadhi", "oushadhi", "ausadhi", "gulige"],
        "help": ["sahaya", "sahaaya", "helpu"],
        "distress": ["bhaya", "ontiyaagi", "ontiyagi", "dukha", "dukkha", "chinte", "chinthe", "nenapaagtide", "nenapagtide"],
        "hungry": ["oota beku", "tindi beku"],
        "thirsty": ["neeru", "niru", "neeru beku", "neeru bekku"],
        "food": ["oota", "aahara", "ahara", "tindi"],
        "song": ["haadu", "haadugalu", "hadu", "hadugalu", "sangeetha", "sangeeta"],
        "place": ["devasthana", "devaru", "ooru", "oora", "jaaga", "jaga"],
        "reminder": ["indu", "ivattu", "ivathu", "naale", "nale", "habba", "huttuhabba"],
        "memory": ["nenapu", "nenapina", "gnapaka", "gyapaka", "kathe"],
        "reassure": ["ella chennagide", "ellaa chennagide", "ella sari"],
    },
    "stems": {
        "hungry": ["hasiv"],
        "thirsty": ["baayar", "bayar"],
        "call": ["maatad", "matad", "maatanad", "matanad", "nodbek", "nodabek"],
    },
    "rel_exact": {
        "grandchild": ["mommaga", "mommagalu", "mommakkalu"],
        "daughter": ["magalu", "magala", "magalige"],
        "son": ["maga", "magana", "maganu", "maganige", "magane"],
        "wife": ["hendati", "hendathi", "hendthi"],
        "husband": ["ganda", "gandanu"],
        "mother": ["amma", "taayi", "thayi", "tayi"],
        "father": ["appa", "thande", "tande"],
        "brother": ["anna", "tamma", "annayya"],
        "sister": ["akka", "thangi", "tangi", "akkayya"],
    },
    "rel_stems": {},
    "signals": ["nanna", "nanage", "nanu", "naanu", "neevu", "neenu", "beku", "bekku", "illa", "alla", "houdu", "haudu", "yaake", "yenu", "ide", "ide?"],
    "yes": {"houdu", "haudu", "beku", "bekku"},
    "no": {"beda", "bedaa", "illa"},
}
TAMIL_ROMAN = {
    "exact": TANGLISH_EXACT, "stems": TANGLISH_STEMS,
    "rel_exact": RELATION_TANGLISH_EXACT, "rel_stems": RELATION_STEMS,
    "signals": ["enakku", "enaku", "en", "ennoda", "unga", "neenga", "nee", "naan", "illai", "irukku", "irukkuthu", "venum", "venam", "enna", "yaar"],
}
ROMAN = {"ta-IN": TAMIL_ROMAN, "hi-IN": HINGLISH, "kn-IN": KANGLISH}   # tie-break order if scores are equal

# Merge the new Hinglish / Kanglish words into the shared tables the detector already uses.
for _spec in (HINGLISH, KANGLISH):
    for _g, _words in _spec["exact"].items():
        KEYWORDS[_g] = KEYWORDS[_g] + _words
    for _g, _sts in _spec["stems"].items():
        TANGLISH_STEMS[_g] = TANGLISH_STEMS.get(_g, []) + _sts
    for _rel, _ws in _spec["rel_exact"].items():
        RELATION_TANGLISH_EXACT[_rel] = RELATION_TANGLISH_EXACT.get(_rel, []) + [w for w in _ws if w not in RELATION_TANGLISH_EXACT.get(_rel, [])]
    TANGLISH_YES |= _spec["yes"]
    TANGLISH_NO |= _spec["no"]
for _g, _words in TANGLISH_EXACT.items():
    KEYWORDS[_g] = KEYWORDS[_g] + _words
NEGATIONS = NEGATIONS + TANGLISH_NEGATIONS + ["nahi", "nahin", "nahee", "nhi", "beda", "bedaa"]


def _stem(text: str, stem: str) -> bool:
    """Word *beginning* match for ASCII Tanglish stems."""
    return re.search(r"(?<!\w)" + re.escape(stem), text) is not None


def romanised_lang(text: str, prefer: str | None = None) -> str | None:
    """Which language is this English-letter sentence really in? 'ta-IN' (Tanglish), 'hi-IN' (Hinglish),
    'kn-IN' (Kanglish) or None for plain English. The language with the most matching words wins;
    on a tie the patient's own language is preferred."""
    t = text.lower()
    scores = {}
    for lang, spec in ROMAN.items():
        n = sum(_matches(t, w) for ws in spec["exact"].values() for w in ws)
        n += sum(_stem(t, st) for sts in spec["stems"].values() for st in sts)
        n += sum(_matches(t, w) for ws in spec["rel_exact"].values() for w in ws)
        n += sum(_stem(t, st) for sts in spec["rel_stems"].values() for st in sts)
        hit = n
        n += sum(_matches(t, w) for w in spec["signals"])
        if hit:                      # little signal words alone never decide
            scores[lang] = n
    if not scores:
        return None
    top = max(scores.values())
    tied = [lang for lang in ROMAN if scores.get(lang) == top]
    return prefer if prefer in tied else tied[0]


def is_tanglish(text: str) -> bool:
    return romanised_lang(text) == "ta-IN"


def _matches(text: str, keyword: str) -> bool:
    if keyword.isascii():
        return re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text) is not None
    return keyword in text


def _has(text: str, group: str) -> bool:
    return (any(_matches(text, k) for k in KEYWORDS[group])
            or any(_stem(text, st) for st in TANGLISH_STEMS.get(group, [])))


def find_relation(text: str, family: list[dict]) -> dict | None:
    """Return the family member the patient is talking about, by name first, then by relation word."""
    for person in family:
        if person["name"].lower() in text:
            return person
    for relation, words in RELATIONS.items():
        if (any(_matches(text, w) for w in words)
                or any(_stem(text, st) for st in RELATION_STEMS.get(relation, []))
                or any(_matches(text, w) for w in RELATION_TANGLISH_EXACT.get(relation, []))):
            matches = [p for p in family if p["relation"] == relation]
            if matches:
                return matches[0]
            return {"name": "", "relation": relation, "missing": True}
    return None


TOMORROW_WORDS = ["tomorrow", "naalai", "nalai", "naale", "nale", "kal", "कल", "ನಾಳೆ", "நாளை"]


def asks_tomorrow(transcript: str) -> bool:
    t = transcript.lower()
    return any(_matches(t, w) for w in TOMORROW_WORDS)


def detect(transcript: str, family: list[dict]) -> dict:
    """Returns {'intent': str, 'person': dict|None, 'subject': str}."""
    text = transcript.lower().strip()
    if not text:
        return {"intent": "empty", "person": None, "subject": ""}

    negated = any(_matches(text, w) for w in NEGATIONS)
    for intent in PRIORITY:
        if intent in ("hungry", "thirsty") and negated:
            if _has(text, intent):
                return {"intent": "checkin_ok", "person": None, "subject": ""}  # "I am not hungry"
            continue
        if _has(text, intent):
            return {"intent": intent, "person": None, "subject": ""}

    person = find_relation(text, family)
    if person is not None:
        subject = person.get("name") or person["relation"]
        if _has(text, "call"):
            return {"intent": "call_family", "person": person, "subject": subject}
        if _has(text, "where"):
            return {"intent": "family_where", "person": person, "subject": subject}
        return {"intent": "family_who", "person": person, "subject": subject}

    for intent in AFTER_FAMILY:
        if _has(text, intent):
            return {"intent": intent, "person": None, "subject": ""}

    return {"intent": "general", "person": None, "subject": ""}


YES_WORDS = {"yes", "yeah", "yep", "yup", "ok", "okay", "sure", "please",
             "हाँ", "हां", "हा", "जी", "ठीक",
             "ಹೌದು", "ಹೂಂ", "ಹು",
             "ஆம்", "ஆமாம்", "ஆமா", "ஆம"}
NO_WORDS = {"no", "nope", "not", "nothing",
            "नहीं", "नही", "ना",
            "ಇಲ್ಲ", "ಬೇಡ",
            "இல்லை", "இல்ல", "வேண்டாம்"}


def yes_no(transcript: str) -> str | None:
    """Short answers only ('yes', 'no, thank you', 'हाँ'). Returns 'yes', 'no' or None."""
    tokens = [t.strip(".,?!।;:\"'") for t in transcript.lower().split()]
    tokens = [t for t in tokens if t]
    if not tokens or len(tokens) > 5:
        return None
    y = any(t in YES_WORDS or t in TANGLISH_YES for t in tokens)
    n = any(t in NO_WORDS or t in TANGLISH_NO for t in tokens)
    if y and not n:
        return "yes"
    if n and not y:
        return "no"
    return None
