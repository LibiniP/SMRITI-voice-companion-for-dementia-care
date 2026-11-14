"""Fixed, carefully worded reply templates in four languages.

Why templates and not free generation: for a vulnerable user, every sentence should be predictable.
The only free text spoken is text the caregiver wrote and approved (status, description, memories, reminders).

NOTE: Hindi, Kannada and Tamil wording should be reviewed by a native speaker before any real use.
"""

LANGS = ["en-IN", "hi-IN", "kn-IN", "ta-IN"]

# "your daughter" in each language (possessive included, so grammar stays correct)
RELATION_PHRASE = {
    "en-IN": {"daughter": "your daughter", "son": "your son", "wife": "your wife", "husband": "your husband",
              "mother": "your mother", "father": "your father", "brother": "your brother",
              "sister": "your sister", "grandchild": "your grandchild"},
    "hi-IN": {"daughter": "आपकी बेटी", "son": "आपका बेटा", "wife": "आपकी पत्नी", "husband": "आपके पति",
              "mother": "आपकी माँ", "father": "आपके पिता", "brother": "आपके भाई",
              "sister": "आपकी बहन", "grandchild": "आपके पोते/पोती"},
    "kn-IN": {"daughter": "ನಿಮ್ಮ ಮಗಳು", "son": "ನಿಮ್ಮ ಮಗ", "wife": "ನಿಮ್ಮ ಹೆಂಡತಿ", "husband": "ನಿಮ್ಮ ಗಂಡ",
              "mother": "ನಿಮ್ಮ ತಾಯಿ", "father": "ನಿಮ್ಮ ತಂದೆ", "brother": "ನಿಮ್ಮ ಸಹೋದರ",
              "sister": "ನಿಮ್ಮ ಸಹೋದರಿ", "grandchild": "ನಿಮ್ಮ ಮೊಮ್ಮಗು"},
    "ta-IN": {"daughter": "உங்கள் மகள்", "son": "உங்கள் மகன்", "wife": "உங்கள் மனைவி", "husband": "உங்கள் கணவர்",
              "mother": "உங்கள் அம்மா", "father": "உங்கள் அப்பா", "brother": "உங்கள் சகோதரர்",
              "sister": "உங்கள் சகோதரி", "grandchild": "உங்கள் பேரக்குழந்தை"},
}

T = {
    "en-IN": {
        "greeting": "Hello {pname}. I am here with you. How are you feeling?",
        "family_where_ok": "{rel} {fname} {status}.",
        "family_where_unknown": "I do not know where {rel} {fname} is right now. I can tell your caregiver that you are asking.",
        "family_who": "Yes, {fname} is {rel}. {desc}",
        "family_missing": "I do not have details about {rel} yet. I will tell your caregiver.",
        "call_family": "Of course. I will tell your caregiver that you would like to talk to {fname}. Please stay here with me.",
        "memory_found": "{items}",
        "unknown": "I am not sure about that, and I do not want to tell you something wrong. I can ask your caregiver.",
        "reminder_found": "Here is what is planned: {items}.",
        "reminder_tomorrow": "Tomorrow's plan is: {items}.",
        "reminder_tomorrow_none": "I do not see anything planned for tomorrow. I can ask your caregiver.",
        "reminder_none": "I do not see anything planned right now. I can ask your caregiver.",
        "confusion": "I am here with you. {loc} I will let your caregiver know.",
        "who_am_i": "Your name is {pname}.",
        "distress": "I am sorry you feel this way. You are not alone. I am here with you. I will let your caregiver know.",
        "help": "I have sent a message to your caregiver. If you are in danger, please call the emergency number.",
        "emergency": "I have sent an urgent message to your caregiver. If this is an emergency, please call {emergency} right now.",
        "medication": "I cannot give advice about medicines. Please ask your caregiver or your doctor. I have let your caregiver know.",
        "reassure": "I am here with you. You are not alone.",
        "empty": "I did not hear anything. Please tap the button and try again.",
    },
    "hi-IN": {
        "greeting": "नमस्ते {pname}। मैं आपके साथ हूँ। आप कैसा महसूस कर रहे हैं?",
        "family_where_ok": "{rel} {fname} {status}।",
        "family_where_unknown": "मुझे अभी नहीं पता कि {rel} {fname} कहाँ हैं। मैं आपकी देखभाल करने वाले को बता सकती हूँ कि आप पूछ रहे हैं।",
        "family_who": "हाँ, {fname} {rel} हैं। {desc}",
        "family_missing": "मेरे पास अभी {rel} के बारे में जानकारी नहीं है। मैं आपकी देखभाल करने वाले को बता दूँगी।",
        "call_family": "ज़रूर। मैं आपकी देखभाल करने वाले को बता दूँगी कि आप {fname} से बात करना चाहते हैं। कृपया मेरे साथ यहीं रुकिए।",
        "memory_found": "{items}",
        "unknown": "मुझे इसके बारे में पक्का पता नहीं है, और मैं आपको गलत बात नहीं बताना चाहती। मैं आपकी देखभाल करने वाले से पूछ सकती हूँ।",
        "reminder_found": "आज की योजना यह है: {items}।",
        "reminder_tomorrow": "कल की योजना यह है: {items}।",
        "reminder_tomorrow_none": "मुझे कल की कोई योजना नहीं दिख रही। मैं आपकी देखभाल करने वाले से पूछ सकता हूँ।",
        "reminder_none": "मुझे अभी कोई योजना नहीं दिख रही। मैं आपकी देखभाल करने वाले से पूछ सकती हूँ।",
        "confusion": "मैं आपके साथ हूँ। {loc} मैं आपकी देखभाल करने वाले को बता दूँगी।",
        "who_am_i": "आपका नाम {pname} है।",
        "distress": "मुझे दुख है कि आप ऐसा महसूस कर रहे हैं। आप अकेले नहीं हैं, मैं आपके साथ हूँ। मैं आपकी देखभाल करने वाले को बता दूँगी।",
        "help": "मैंने आपकी देखभाल करने वाले को संदेश भेज दिया है। अगर आप खतरे में हैं, तो कृपया आपातकालीन नंबर पर फ़ोन कीजिए।",
        "emergency": "मैंने आपकी देखभाल करने वाले को तुरंत संदेश भेज दिया है। अगर यह आपातकाल है, तो कृपया अभी {emergency} पर फ़ोन कीजिए।",
        "medication": "मैं दवाइयों के बारे में सलाह नहीं दे सकती। कृपया अपनी देखभाल करने वाले या डॉक्टर से पूछिए। मैंने उन्हें बता दिया है।",
        "reassure": "मैं आपके साथ हूँ। आप अकेले नहीं हैं।",
        "empty": "मुझे कुछ सुनाई नहीं दिया। कृपया बटन दबाकर फिर से बोलिए।",
    },
    "kn-IN": {
        "greeting": "ನಮಸ್ಕಾರ {pname}. ನಾನು ನಿಮ್ಮ ಜೊತೆ ಇದ್ದೇನೆ. ನಿಮಗೆ ಹೇಗನಿಸುತ್ತಿದೆ?",
        "family_where_ok": "{rel} {fname} {status}.",
        "family_where_unknown": "{rel} {fname} ಈಗ ಎಲ್ಲಿದ್ದಾರೆ ಎಂದು ನನಗೆ ಗೊತ್ತಿಲ್ಲ. ನೀವು ಕೇಳುತ್ತಿದ್ದೀರಿ ಎಂದು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ತಿಳಿಸಬಹುದು.",
        "family_who": "ಹೌದು, {fname} {rel}. {desc}",
        "family_missing": "{rel} ಬಗ್ಗೆ ನನ್ನ ಬಳಿ ಇನ್ನೂ ಮಾಹಿತಿ ಇಲ್ಲ. ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ತಿಳಿಸುತ್ತೇನೆ.",
        "call_family": "ಖಂಡಿತ. ನೀವು {fname} ಜೊತೆ ಮಾತನಾಡಲು ಬಯಸುತ್ತೀರಿ ಎಂದು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ತಿಳಿಸುತ್ತೇನೆ. ದಯವಿಟ್ಟು ನನ್ನ ಜೊತೆ ಇಲ್ಲೇ ಇರಿ.",
        "memory_found": "{items}",
        "unknown": "ಇದರ ಬಗ್ಗೆ ನನಗೆ ಖಚಿತವಿಲ್ಲ, ತಪ್ಪು ಹೇಳಲು ನನಗೆ ಇಷ್ಟವಿಲ್ಲ. ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರನ್ನು ಕೇಳಬಹುದು.",
        "reminder_found": "ಇಂದಿನ ಯೋಜನೆ ಹೀಗಿದೆ: {items}.",
        "reminder_tomorrow": "ನಾಳೆಯ ಯೋಜನೆ ಹೀಗಿದೆ: {items}.",
        "reminder_tomorrow_none": "ನಾಳೆಗೆ ಯಾವುದೇ ಯೋಜನೆ ಕಾಣಿಸುತ್ತಿಲ್ಲ. ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರನ್ನು ಕೇಳಬಹುದು.",
        "reminder_none": "ಈಗ ಯಾವುದೇ ಯೋಜನೆ ಕಾಣಿಸುತ್ತಿಲ್ಲ. ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರನ್ನು ಕೇಳಬಹುದು.",
        "confusion": "ನಾನು ನಿಮ್ಮ ಜೊತೆ ಇದ್ದೇನೆ. {loc} ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ತಿಳಿಸುತ್ತೇನೆ.",
        "who_am_i": "ನಿಮ್ಮ ಹೆಸರು {pname}.",
        "distress": "ನಿಮಗೆ ಹೀಗನಿಸುತ್ತಿರುವುದಕ್ಕೆ ಬೇಸರವಾಗುತ್ತಿದೆ. ನೀವು ಒಬ್ಬರೇ ಅಲ್ಲ, ನಾನು ನಿಮ್ಮ ಜೊತೆ ಇದ್ದೇನೆ. ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ತಿಳಿಸುತ್ತೇನೆ.",
        "help": "ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ಸಂದೇಶ ಕಳುಹಿಸಿದ್ದೇನೆ. ನೀವು ಅಪಾಯದಲ್ಲಿದ್ದರೆ ದಯವಿಟ್ಟು ತುರ್ತು ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ.",
        "emergency": "ನಾನು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ತುರ್ತು ಸಂದೇಶ ಕಳುಹಿಸಿದ್ದೇನೆ. ಇದು ತುರ್ತು ಪರಿಸ್ಥಿತಿಯಾದರೆ ದಯವಿಟ್ಟು ಈಗಲೇ {emergency} ಗೆ ಕರೆ ಮಾಡಿ.",
        "medication": "ಔಷಧಿಗಳ ಬಗ್ಗೆ ನಾನು ಸಲಹೆ ನೀಡಲಾರೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆರೈಕೆದಾರರು ಅಥವಾ ವೈದ್ಯರನ್ನು ಕೇಳಿ. ನಾನು ಅವರಿಗೆ ತಿಳಿಸಿದ್ದೇನೆ.",
        "reassure": "ನಾನು ನಿಮ್ಮ ಜೊತೆ ಇದ್ದೇನೆ. ನೀವು ಒಬ್ಬರೇ ಅಲ್ಲ.",
        "empty": "ನನಗೆ ಏನೂ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಬಟನ್ ಒತ್ತಿ ಮತ್ತೆ ಮಾತನಾಡಿ.",
    },
    "ta-IN": {
        "greeting": "வணக்கம் {pname}. நான் உங்களுடன் இருக்கிறேன். நீங்கள் எப்படி உணர்கிறீர்கள்?",
        "family_where_ok": "{rel} {fname} {status}.",
        "family_where_unknown": "{rel} {fname} இப்போது எங்கே இருக்கிறார் என்று எனக்குத் தெரியவில்லை. நீங்கள் கேட்கிறீர்கள் என்று உங்கள் பராமரிப்பாளரிடம் சொல்லலாமா?",
        "family_who": "ஆமாம், {fname} {rel}. {desc}",
        "family_missing": "{rel} பற்றிய தகவல் என்னிடம் இன்னும் இல்லை. நான் உங்கள் பராமரிப்பாளரிடம் சொல்கிறேன்.",
        "call_family": "சரி. நீங்கள் {fname} உடன் பேச விரும்புகிறீர்கள் என்று உங்கள் பராமரிப்பாளரிடம் சொல்கிறேன். தயவுசெய்து என்னுடன் இங்கேயே இருங்கள்.",
        "memory_found": "{items}",
        "unknown": "இதைப் பற்றி எனக்கு உறுதியாகத் தெரியவில்லை, தவறாகச் சொல்ல விரும்பவில்லை. உங்கள் பராமரிப்பாளரிடம் கேட்கலாமா?",
        "reminder_found": "இன்றைய திட்டம் இதுதான்: {items}.",
        "reminder_tomorrow": "நாளைய திட்டம் இதுதான்: {items}.",
        "reminder_tomorrow_none": "நாளைக்கு எந்தத் திட்டமும் தெரியவில்லை. உங்கள் பராமரிப்பாளரிடம் கேட்கலாம்.",
        "reminder_none": "இப்போது எந்தத் திட்டமும் தெரியவில்லை. உங்கள் பராமரிப்பாளரிடம் கேட்கலாமா?",
        "confusion": "நான் உங்களுடன் இருக்கிறேன். {loc} உங்கள் பராமரிப்பாளரிடம் சொல்கிறேன்.",
        "who_am_i": "உங்கள் பெயர் {pname}.",
        "distress": "நீங்கள் இப்படி உணர்வது வருத்தமாக இருக்கிறது. நீங்கள் தனியாக இல்லை, நான் உங்களுடன் இருக்கிறேன். உங்கள் பராமரிப்பாளரிடம் சொல்கிறேன்.",
        "help": "உங்கள் பராமரிப்பாளருக்குச் செய்தி அனுப்பியிருக்கிறேன். நீங்கள் ஆபத்தில் இருந்தால் தயவுசெய்து அவசர எண்ணை அழையுங்கள்.",
        "emergency": "உங்கள் பராமரிப்பாளருக்கு அவசரச் செய்தி அனுப்பியிருக்கிறேன். இது அவசரநிலை என்றால் தயவுசெய்து இப்போதே {emergency} எண்ணை அழையுங்கள்.",
        "medication": "மருந்துகள் பற்றி என்னால் ஆலோசனை சொல்ல முடியாது. தயவுசெய்து உங்கள் பராமரிப்பாளர் அல்லது மருத்துவரிடம் கேளுங்கள். அவர்களுக்குத் தெரிவித்திருக்கிறேன்.",
        "reassure": "நான் உங்களுடன் இருக்கிறேன். நீங்கள் தனியாக இல்லை.",
        "empty": "எனக்கு எதுவும் கேட்கவில்லை. தயவுசெய்து பொத்தானை அழுத்தி மீண்டும் பேசுங்கள்.",
    },
}


def render(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in T else "en-IN"
    text = T[lang][key].format(**kwargs)
    text = " ".join(text.split())  # tidy spaces when an optional field is empty
    return text[0].upper() + text[1:] if text else text


def relation_phrase(lang: str, relation: str) -> str:
    lang = lang if lang in RELATION_PHRASE else "en-IN"
    return RELATION_PHRASE[lang].get(relation, relation)


# ======================================================================
# Conversation extras: kind words, follow-ups, hungry/thirsty/comfort check-ins, setup templates.
# NOTE: Hindi, Kannada and Tamil wording should be reviewed by a native speaker before real use.
# ======================================================================
T["en-IN"].update({
    "topic_yes": "I am glad. Please tell me more.",
    "topic_no": "That is alright. We can talk about anything you like.",

    "kind": ["It is lovely talking with you.", "I am happy to be here with you.", "You are doing very well.", "I enjoy our time together."],
    "more": ["Would you like to tell me more?", "What else is on your mind?", "I am listening. Tell me anything you like."],
    "topic_q": "Shall we talk about {topic}?",
    "calm": "Let us take a slow, deep breath together.",
    "ask_thirsty": "Are you feeling thirsty?",
    "ask_hungry": "Are you feeling hungry?",
    "ask_comfort": "Is anything bothering you or hurting you right now?",
    "thirsty_yes": "Alright. I will tell your caregiver right away so they can bring you some water. Please stay here with me.",
    "hungry_yes": "Alright. I will tell your caregiver right away so they can help you with food. Please stay here with me.",
    "comfort_yes": "I am sorry to hear that. I will tell your caregiver right away. Please stay here with me.",
    "thirsty_no": "That is good.",
    "hungry_no": "That is good.",
    "comfort_no": "I am glad.",
    "who_am_i_unknown": "I do not know your name yet. Your caregiver can tell me.",
    "friend": "friend",
})
T["hi-IN"].update({
    "topic_yes": "मुझे अच्छा लगा। कृपया और बताइए।",
    "topic_no": "ठीक है। आप जिस बारे में चाहें, हम बात कर सकते हैं।",

    "kind": ["आपसे बात करके बहुत अच्छा लग रहा है।", "मुझे आपके साथ रहकर खुशी होती है।", "आप बहुत अच्छा कर रहे हैं।", "हमारा साथ मुझे अच्छा लगता है।"],
    "more": ["क्या आप मुझे और कुछ बताना चाहेंगे?", "आपके मन में और क्या है?", "मैं सुन रही हूँ। आप जो चाहें बताइए।"],
    "topic_q": "क्या हम {topic} के बारे में बात करें?",
    "calm": "आइए, एक साथ धीरे-धीरे गहरी साँस लें।",
    "ask_thirsty": "क्या आपको प्यास लगी है?",
    "ask_hungry": "क्या आपको भूख लगी है?",
    "ask_comfort": "क्या अभी आपको कोई तकलीफ़ या दर्द है?",
    "thirsty_yes": "ठीक है। मैं अभी आपकी देखभाल करने वाले को बता देती हूँ ताकि वे आपके लिए पानी ला सकें। कृपया मेरे साथ यहीं रुकिए।",
    "hungry_yes": "ठीक है। मैं अभी आपकी देखभाल करने वाले को बता देती हूँ ताकि वे आपके खाने का इंतज़ाम कर सकें। कृपया मेरे साथ यहीं रुकिए।",
    "comfort_yes": "यह सुनकर मुझे दुख हुआ। मैं अभी आपकी देखभाल करने वाले को बता देती हूँ। कृपया मेरे साथ यहीं रुकिए।",
    "thirsty_no": "यह अच्छी बात है।",
    "hungry_no": "यह अच्छी बात है।",
    "comfort_no": "यह जानकर अच्छा लगा।",
    "who_am_i_unknown": "मुझे अभी आपका नाम नहीं पता। आपकी देखभाल करने वाले मुझे बता सकते हैं।",
    "friend": "दोस्त",
})
T["kn-IN"].update({
    "topic_yes": "ಖುಷಿಯಾಯಿತು. ದಯವಿಟ್ಟು ಇನ್ನಷ್ಟು ಹೇಳಿ.",
    "topic_no": "ಸರಿ. ನಿಮಗೆ ಇಷ್ಟವಾದ ಯಾವುದರ ಬಗ್ಗೆಯೂ ಮಾತಾಡೋಣ.",

    "kind": ["ನಿಮ್ಮ ಜೊತೆ ಮಾತನಾಡಲು ತುಂಬಾ ಖುಷಿಯಾಗುತ್ತದೆ.", "ನಿಮ್ಮ ಜೊತೆ ಇರುವುದು ನನಗೆ ಸಂತೋಷ.", "ನೀವು ತುಂಬಾ ಚೆನ್ನಾಗಿದ್ದೀರಿ.", "ನಮ್ಮ ಈ ಸಮಯ ನನಗೆ ಇಷ್ಟ."],
    "more": ["ಇನ್ನೂ ಏನಾದರೂ ಹೇಳಲು ಬಯಸುತ್ತೀರಾ?", "ನಿಮ್ಮ ಮನಸ್ಸಿನಲ್ಲಿ ಇನ್ನೇನಿದೆ?", "ನಾನು ಕೇಳುತ್ತಿದ್ದೇನೆ. ನಿಮಗೆ ಇಷ್ಟವಾದದ್ದನ್ನು ಹೇಳಿ."],
    "topic_q": "{topic} ಬಗ್ಗೆ ಮಾತನಾಡೋಣವೇ?",
    "calm": "ನಿಧಾನವಾಗಿ ಒಟ್ಟಿಗೆ ದೀರ್ಘ ಉಸಿರು ತೆಗೆದುಕೊಳ್ಳೋಣ.",
    "ask_thirsty": "ನಿಮಗೆ ಬಾಯಾರಿಕೆಯಾಗುತ್ತಿದೆಯೇ?",
    "ask_hungry": "ನಿಮಗೆ ಹಸಿವಾಗುತ್ತಿದೆಯೇ?",
    "ask_comfort": "ಈಗ ನಿಮಗೆ ಏನಾದರೂ ತೊಂದರೆ ಅಥವಾ ನೋವು ಇದೆಯೇ?",
    "thirsty_yes": "ಸರಿ. ನಿಮಗೆ ನೀರು ತರಲು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ಈಗಲೇ ತಿಳಿಸುತ್ತೇನೆ. ದಯವಿಟ್ಟು ನನ್ನ ಜೊತೆ ಇಲ್ಲೇ ಇರಿ.",
    "hungry_yes": "ಸರಿ. ನಿಮಗೆ ಊಟ ಕೊಡಲು ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ಈಗಲೇ ತಿಳಿಸುತ್ತೇನೆ. ದಯವಿಟ್ಟು ನನ್ನ ಜೊತೆ ಇಲ್ಲೇ ಇರಿ.",
    "comfort_yes": "ಇದನ್ನು ಕೇಳಿ ಬೇಸರವಾಯಿತು. ನಿಮ್ಮ ಆರೈಕೆದಾರರಿಗೆ ಈಗಲೇ ತಿಳಿಸುತ್ತೇನೆ. ದಯವಿಟ್ಟು ನನ್ನ ಜೊತೆ ಇಲ್ಲೇ ಇರಿ.",
    "thirsty_no": "ಒಳ್ಳೆಯದು.",
    "hungry_no": "ಒಳ್ಳೆಯದು.",
    "comfort_no": "ಸಂತೋಷ.",
    "who_am_i_unknown": "ನಿಮ್ಮ ಹೆಸರು ನನಗೆ ಇನ್ನೂ ಗೊತ್ತಿಲ್ಲ. ನಿಮ್ಮ ಆರೈಕೆದಾರರು ನನಗೆ ಹೇಳಬಹುದು.",
    "friend": "ಸ್ನೇಹಿತರೇ",
})
T["ta-IN"].update({
    "topic_yes": "மகிழ்ச்சி. தயவுசெய்து இன்னும் சொல்லுங்கள்.",
    "topic_no": "சரி. உங்களுக்கு விருப்பமானதைப் பற்றி பேசலாம்.",

    "kind": ["உங்களுடன் பேசுவது மிகவும் மகிழ்ச்சியாக இருக்கிறது.", "உங்களுடன் இருப்பது எனக்கு மகிழ்ச்சி.", "நீங்கள் மிக நன்றாக இருக்கிறீர்கள்.", "நம் நேரம் எனக்குப் பிடிக்கும்."],
    "more": ["இன்னும் ஏதாவது சொல்ல விரும்புகிறீர்களா?", "உங்கள் மனதில் வேறு என்ன இருக்கிறது?", "நான் கேட்கிறேன். உங்களுக்குப் பிடித்ததைச் சொல்லுங்கள்."],
    "topic_q": "{topic} பற்றிப் பேசலாமா?",
    "calm": "மெதுவாக ஒன்றாக ஆழ்ந்த மூச்சு எடுப்போம்.",
    "ask_thirsty": "உங்களுக்குத் தாகமாக இருக்கிறதா?",
    "ask_hungry": "உங்களுக்குப் பசிக்கிறதா?",
    "ask_comfort": "இப்போது உங்களுக்கு ஏதாவது தொந்தரவோ வலியோ இருக்கிறதா?",
    "thirsty_yes": "சரி. உங்களுக்குத் தண்ணீர் கொண்டுவர உங்கள் பராமரிப்பாளரிடம் இப்போதே சொல்கிறேன். தயவுசெய்து என்னுடன் இங்கேயே இருங்கள்.",
    "hungry_yes": "சரி. உங்களுக்கு உணவு தர உங்கள் பராமரிப்பாளரிடம் இப்போதே சொல்கிறேன். தயவுசெய்து என்னுடன் இங்கேயே இருங்கள்.",
    "comfort_yes": "இதைக் கேட்டு வருத்தமாக இருக்கிறது. உங்கள் பராமரிப்பாளரிடம் இப்போதே சொல்கிறேன். தயவுசெய்து என்னுடன் இங்கேயே இருங்கள்.",
    "thirsty_no": "நல்லது.",
    "hungry_no": "நல்லது.",
    "comfort_no": "மகிழ்ச்சி.",
    "who_am_i_unknown": "உங்கள் பெயர் எனக்கு இன்னும் தெரியாது. உங்கள் பராமரிப்பாளர் எனக்குச் சொல்லலாம்.",
    "friend": "நண்பரே",
})

# What the assistant offers to talk about, per memory category (no "about" word: the template adds it)
TOPIC = {
    "en-IN": {"food": "your favourite food", "song": "your favourite songs", "place": "your favourite places",
              "hobby": "your hobbies", "life_event": "your life stories", "other": "your memories"},
    "hi-IN": {"food": "आपके पसंदीदा खाने", "song": "आपके पसंदीदा गानों", "place": "आपकी पसंदीदा जगहों",
              "hobby": "आपके शौक", "life_event": "आपकी ज़िंदगी की कहानियों", "other": "आपकी यादों"},
    "kn-IN": {"food": "ನಿಮ್ಮ ಇಷ್ಟದ ಊಟ", "song": "ನಿಮ್ಮ ಇಷ್ಟದ ಹಾಡುಗಳು", "place": "ನಿಮ್ಮ ಇಷ್ಟದ ಸ್ಥಳಗಳು",
              "hobby": "ನಿಮ್ಮ ಹವ್ಯಾಸಗಳು", "life_event": "ನಿಮ್ಮ ಜೀವನದ ಕಥೆಗಳು", "other": "ನಿಮ್ಮ ನೆನಪುಗಳು"},
    "ta-IN": {"food": "உங்களுக்குப் பிடித்த உணவு", "song": "உங்களுக்குப் பிடித்த பாடல்கள்", "place": "உங்களுக்குப் பிடித்த இடங்கள்",
              "hobby": "உங்கள் பொழுதுபோக்குகள்", "life_event": "உங்கள் வாழ்க்கைக் கதைகள்", "other": "உங்கள் நினைவுகள்"},
}

# Sentences built from the caregiver's short setup answers, in the patient's preferred language
MEMORY_TPL = {
    "en-IN": {"food": "Your favourite food is {x}.", "song": "You love listening to {x}.", "place": "You enjoy visiting {x}.",
              "hobby": "You enjoy {x}.", "special": "Something special about you: {x}."},
    "hi-IN": {"food": "आपका पसंदीदा खाना {x} है।", "song": "आपको {x} सुनना बहुत पसंद है।", "place": "आपको {x} जाना पसंद है।",
              "hobby": "आपको {x} का शौक है।", "special": "आपके बारे में एक खास बात: {x}।"},
    "kn-IN": {"food": "ನಿಮ್ಮ ಇಷ್ಟದ ಊಟ {x}.", "song": "ನಿಮಗೆ {x} ಕೇಳುವುದು ಇಷ್ಟ.", "place": "ನಿಮಗೆ {x} ಗೆ ಹೋಗುವುದು ಇಷ್ಟ.",
              "hobby": "ನಿಮಗೆ {x} ಇಷ್ಟ.", "special": "ನಿಮ್ಮ ಬಗ್ಗೆ ಒಂದು ವಿಶೇಷ: {x}."},
    "ta-IN": {"food": "உங்களுக்குப் பிடித்த உணவு {x}.", "song": "உங்களுக்கு {x} கேட்பது பிடிக்கும்.", "place": "உங்களுக்கு {x} செல்வது பிடிக்கும்.",
              "hobby": "உங்களுக்கு {x} பிடிக்கும்.", "special": "உங்களைப் பற்றி ஒரு சிறப்பு: {x}."},
}
MEMORY_CATEGORY = {"food": "food", "song": "song", "place": "place", "hobby": "hobby", "special": "life_event"}


def pick(lang: str, key: str, i: int) -> str:
    """Rotate through a list of phrases so the assistant does not repeat itself."""
    items = T[lang if lang in T else "en-IN"][key]
    return items[i % len(items)]


def topic_phrase(lang: str, category: str) -> str:
    d = TOPIC[lang if lang in TOPIC else "en-IN"]
    return d.get(category, d["other"])


def friend(lang: str) -> str:
    return T[lang if lang in T else "en-IN"]["friend"]


def memory_sentence(lang: str, field: str, value: str) -> str:
    tpl = MEMORY_TPL[lang if lang in MEMORY_TPL else "en-IN"][field]
    return tpl.format(x=value.strip())
