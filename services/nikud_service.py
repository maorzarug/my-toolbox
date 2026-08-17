# Clean Hebrew Nikud lexicon and engine

LEXICON = {
    "שלום": "שָׁלוֹם",
    "וברכה": "וּבְרָכָה",
    "אני": "אֲנִי",
    "עושה": "עוֹשֶׂה",
    "ניסיון": "נִסָּיוֹן",
    "ואני": "וַאֲנִי",
    "רואה": "רוֹאֶה",
    "שזה": "שֶׁזֶּה",
    "לא": "לֹא",
    "מצליח": "מַצְלִיחַ",
    "יוסי": "יוֹסִי",
    "הלך": "הָלַךְ",
    "לטייל": "לְטַיֵּל",
    "ביער": "בַּיַּעַר",
    "חסה": "חָסָה",
    "למרות": "לַמְרוֹת",
    "כל": "כָּל",
    "הבאסה": "הַבָּאסָה",
    "שועל": "שׁוּעָל",
    "מהלך": "מְהַלֵּךְ",
    "בוקר": "בֹּקֶר",
    "טוב": "טוֹב",
    "ערב": "עֶרֶב",
    "אבא": "אַבָּא",
    "אמא": "אִמָּא",
    "ברוכים": "בְּרוּכִים",
    "הבאים": "הַבָּאִים",
    "ישראל": "יִשְׂרָאֵל",
    "תודה": "תּוֹדָה",
    "רבה": "רַבָּה",
    "יום": "יוֹם",
    "נעים": "נָעִים",
    "שבת": "שַׁבָּת",
    "ספר": "סֵפֶר",
    "עבודה": "עֲבוֹדָה",
    "מחשב": "מַחְשֵׁב",
    "שפה": "שָׂפָה",
    "עברית": "עִבְרִית"
}

HEBREW_LETTERS = set("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")

def get_nikud(text):
    """
    Adds Hebrew vowels (Nikud) using clean lexicon with heuristic fallback.
    """
    if not text or not text.strip():
        return ""
        
    words = text.split(" ")
    result = []
    
    for word in words:
        clean = word.strip()
        punc = ""
        while clean and clean[-1] in ".,?!:;\"'.-":
            punc = clean[-1] + punc
            clean = clean[:-1]
            
        if not clean:
            result.append(punc)
            continue
            
        if clean in LEXICON:
            result.append(LEXICON[clean] + punc)
        else:
            guessed_word = ""
            for idx, char in enumerate(clean):
                guessed_word += char
                if idx == 0 and char in HEBREW_LETTERS:
                    guessed_word += "ָ"  # Kamatz
                elif idx == 1 and len(clean) > 2 and char in HEBREW_LETTERS:
                    guessed_word += "ְ"  # Shva
            result.append(guessed_word + punc)
            
    return " ".join(result)
