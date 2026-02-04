# ipa_map.py

# Refined IPA to Sanskrit (Devanagari) Mapping
IPA_TO_SANSKRIT = {
    # Consonants
    'b': 'ब्', 'd': 'ड्', 'f': 'फ्', 'g': 'ग्', 'h': 'ह्', 'j': 'य्', 'k': 'क्', 'l': 'ल्',
    'm': 'म्', 'n': 'न्', 'p': 'प्', 'r': 'र्', 's': 'स्', 't': 'ट्', 'v': 'व्', 'w': 'व्',
    'z': 'ज्', 'ʒ': 'श्', 'dʒ': 'ज्', 'tʃ': 'च्', 'θ': 'थ्', 'ð': 'द्', 'ʃ': 'श्', 'ŋ': 'ङ्',
    'ɡ': 'ग्', 'ɹ': 'र्',
    
    # Vowels
    'ə': 'अ', 
    'i': 'इ', 'ɪ': 'इ', 
    'e': 'ए', 'ɛ': 'ए',
    'æ': 'अ', 
    'a': 'आ', 'ɑ': 'आ', 
    'ɒ': 'ओ', 'ɔ': 'औ', 'ɔː': 'औ',
    'u': 'उ', 'ʊ': 'उ', 
    'ʌ': 'अ', 
    'o': 'ओ', 'oʊ': 'ओ', 'əʊ': 'ओ',
    
    # Diphthongs
    'aɪ': 'ऐ', 'aʊ': 'औ', 'ɔɪ': 'ओइ', 'eə': 'एअ',
    'ɪə': 'इअ', 'ʊə': 'उअ', 'ju': 'यु', 
    'iː': 'ई', 'uː': 'ऊ', '3': 'अ', 'ɑː': 'आ'
}

# Devanagari Mappings
CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ṅ',
    'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'ñ',
    'ट': 'ṭ', 'ठ': 'ṭh', 'ड': 'ḍ', 'ढ': 'ḍh', 'ण': 'ṇ',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'ś', 'ष': 'ṣ', 'स': 's', 'ह': 'h',
    'ळ': 'ḷ', 'क्ष': 'kṣ', 'ज्ञ': 'jñ' 
}

MATRAS = {
    'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū',
    'ृ': 'ṛ', 'ॄ': 'ṝ', 
    'ॢ': 'ḷ', 'ॣ': 'l̤', # Updated to user char l̤
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ं': 'ṁ', # User preferred ṁ
    'ः': 'ḥ', 'ँ': 'm̐'
}

INDEPENDENT_VOWELS = {
    'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū',
    'ऋ': 'ṛ', 'ॠ': 'ṝ', 
    'ऌ': 'ḷ', 'ॡ': 'l̤', # Updated
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
}

VIRAMA = '्'

# List of valid IAST phonemes provided by user, sorted by length (longest first)
# "aāiīuūṛṝḷl̤eaioaukkhgghṅcchjjhñṭṭhḍḍhṇtthddhnpphbbhmyrlvśṣshḻṁm̐ḥẖḫ"
# Parsed list:
IAST_PHONEMES = sorted([
    # Vowels
    'ai', 'au', 
    'ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'l̤', 'e', 'o', 'a', 'i', 'u',
    # Consonants
    'kh', 'gh', 'ch', 'jh', 'ṭh', 'ḍh', 'th', 'dh', 'ph', 'bh',
    'k', 'g', 'ṅ', 'c', 'j', 'ñ', 'ṭ', 'ḍ', 'ṇ',
    't', 'd', 'n', 'p', 'b', 'm',
    'y', 'r', 'l', 'v', 
    'ś', 'ṣ', 's', 'h', 'ḻ',
    # Modifiers
    'ṁ', 'm̐', 'ḥ', 'ẖ', 'ḫ'
], key=len, reverse=True)


def ipa_to_sanskrit(ipa_text):
    if not ipa_text:
        return ""

    tokens = []
    i = 0
    n = len(ipa_text)
    sorted_keys = sorted(IPA_TO_SANSKRIT.keys(), key=len, reverse=True)
    
    while i < n:
        match_found = False
        for key in sorted_keys:
            if ipa_text[i:].startswith(key):
                tokens.append(IPA_TO_SANSKRIT[key])
                i += len(key)
                match_found = True
                break
        if not match_found:
            tokens.append(ipa_text[i])
            i += 1
            
    VOWEL_TO_MATRA = {
        'अ': '', 'आ': 'ा', 'इ': 'ि', 'ई': 'ी', 'उ': 'ु', 'ऊ': 'ू',
        'ए': 'े', 'ऐ': 'ै', 'ओ': 'ो', 'औ': 'ौ',
    }
    
    merged_output = ""
    last_was_halanta = False
    
    for token in tokens:
        if last_was_halanta and token in VOWEL_TO_MATRA:
            if merged_output.endswith(VIRAMA):
                merged_output = merged_output[:-1]
            merged_output += VOWEL_TO_MATRA[token]
            last_was_halanta = False
        else:
            merged_output += token
            if token.endswith(VIRAMA):
                last_was_halanta = True
            else:
                last_was_halanta = False
                
    return merged_output

def sanskrit_to_iast(text):
    if not text:
        return ""
        
    iast_output = ""
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        if char in CONSONANTS:
            base = CONSONANTS[char]
            next_char = text[i+1] if i + 1 < n else None
            
            if next_char:
                if next_char == VIRAMA:
                    iast_output += base
                    i += 2 
                elif next_char in MATRAS:
                    iast_output += base + MATRAS[next_char]
                    i += 2
                else:
                    iast_output += base + 'a'
                    i += 1
            else:
                iast_output += base + 'a'
                i += 1
                
        elif char in INDEPENDENT_VOWELS:
            iast_output += INDEPENDENT_VOWELS[char]
            i += 1
            
        elif char in MATRAS:
             iast_output += MATRAS[char]
             i += 1
             
        else:
            iast_output += char
            i += 1

    return iast_output

def get_iast_separated(iast_text):
    """
    Separates the IAST string into user-defined phonemes.
    E.g., "bhai" -> "bh,ai"
    """
    if not iast_text:
        return ""
    
    output = []
    i = 0
    n = len(iast_text)
    
    # IAST_PHONEMES is sorted by length descending
    
    while i < n:
        match_found = False
        # Try to match largest phoneme at current position
        for phoneme in IAST_PHONEMES:
            if iast_text[i:].startswith(phoneme):
                output.append(phoneme)
                i += len(phoneme)
                match_found = True
                break
        
        if not match_found:
            # If char not in our strict set, keep it as single char (e.g. spaces, commas?)
            output.append(iast_text[i])
            i += 1
            
    return ",".join(output)
