# ipa_map.py

# Refined IPA to Sanskrit (Devanagari) Mapping
# Designed to produce more phonetically plausible Sanskrit names from English IPA.

IPA_TO_SANSKRIT = {
    # Consonants - Mapping to Virama forms to allow easier vowel joining
    'b': 'ब्', 'd': 'ड्', 'f': 'फ्', 'g': 'ग्', 'h': 'ह्', 'j': 'य्', 'k': 'क्', 'l': 'ल्',
    'm': 'म्', 'n': 'न्', 'p': 'प्', 'r': 'र्', 's': 'स्', 't': 'ट्', 'v': 'व्', 'w': 'व्',
    'z': 'ज्', 'ʒ': 'श्', 'dʒ': 'ज्', 'tʃ': 'च्', 'θ': 'थ्', 'ð': 'द्', 'ʃ': 'श्', 'ŋ': 'ङ्',
    'ɡ': 'ग्', 'ɹ': 'र्',
    
    # Vowels
    'ə': 'अ', 
    'i': 'इ', 'ɪ': 'इ', 
    'e': 'ए', 'ɛ': 'ए',
    'æ': 'अ', # 'cat' -> mapped to 'a' rather than 'ai' for better name approx (e.g. 'Ram')
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

# Devanagari Logic Sets
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
    'ृ': 'ṛ', 'ॄ': 'ṝ', 'ॢ': 'ḷ', 'ॣ': 'ḹ',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ं': 'ṃ', 'ः': 'ḥ', 'ँ': 'm̐'
}

INDEPENDENT_VOWELS = {
    'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū',
    'ऋ': 'ṛ', 'ॠ': 'ṝ', 'ऌ': 'ḷ', 'ॡ': 'ḹ',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
}

VIRAMA = '्'

def ipa_to_sanskrit(ipa_text):
    """
    Converts English IPA to Sanskrit Devanagari using a greedy match
    and post-process merging of Halanta+Vowel -> Matra.
    """
    if not ipa_text:
        return ""

    # 1. Greedy Tokenization
    tokens = []
    i = 0
    n = len(ipa_text)
    
    # Sort keys by length to match longest first
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
            # Skip unknown or keep as is? Let's keep as is to be safe
            tokens.append(ipa_text[i])
            i += 1
            
    # 2. Merger Parsing (Halanta + Vowel => Matra)
    # Map Independent Vowel to Matra
    VOWEL_TO_MATRA = {
        'अ': '', # 'a' just deletes the halanta
        'आ': 'ा', 'इ': 'ि', 'ई': 'ी', 'उ': 'ु', 'ऊ': 'ू',
        'ए': 'े', 'ऐ': 'ै', 'ओ': 'ो', 'औ': 'ौ',
    }
    
    merged_output = ""
    last_was_halanta = False
    
    for token in tokens:
        # Check if we can merge
        if last_was_halanta and token in VOWEL_TO_MATRA:
            # Pop the halanta (virama) from the end of the current buffer
            # Assume previous token ended with VIRAMA
            if merged_output.endswith(VIRAMA):
                merged_output = merged_output[:-1]
                
            merged_output += VOWEL_TO_MATRA[token]
            last_was_halanta = False # Matra attached, no longer halanta
        else:
            merged_output += token
            # Check state
            if token.endswith(VIRAMA):
                last_was_halanta = True
            else:
                last_was_halanta = False
                
    return merged_output

def sanskrit_to_iast(text):
    """
    Parses Devanagari and outputs IAST with correct inherent vowel handling.
    """
    if not text:
        return ""
        
    iast_output = ""
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        # 1. Is it a Consonant?
        if char in CONSONANTS:
            base = CONSONANTS[char]
            
            # Lookahead
            next_char = text[i+1] if i + 1 < n else None
            
            if next_char:
                if next_char == VIRAMA:
                    # Explicit suppression of vowel
                    iast_output += base
                    i += 2 # Consume Consonant + Virama
                    
                elif next_char in MATRAS:
                    # Matra overrides inherent 'a'
                    iast_output += base + MATRAS[next_char]
                    i += 2 # Consume Consonant + Matra
                    
                else:
                    # Followed by another consonant, vowel, or other char
                    # In Sanskrit, this implies distinct pronounciation
                    # If followed immediately by independent vowel (rare inside word without gap), 
                    # standard rule is Consonant has 'a'.
                    iast_output += base + 'a'
                    i += 1
            else:
                # End of string: implicitly 'a'
                iast_output += base + 'a'
                i += 1
                
        # 2. Is it an Independent Vowel?
        elif char in INDEPENDENT_VOWELS:
            iast_output += INDEPENDENT_VOWELS[char]
            i += 1
            
        # 3. Is it a stray Matra or modifier? (Should handle punctuation/spaces)
        elif char in MATRAS:
             # Should check previous logic, but if we land here, just append mapped value
             iast_output += MATRAS[char]
             i += 1
             
        # 4. Fallback
        else:
            # Map other symbols like anusvara if in dict, else keep
            # We put Anusvara in MATRAS for convenience but might appear standalone?
            # Actually Anusvara usually follows vowel - treated as matra.
            iast_output += char
            i += 1

    return iast_output

def get_iast_separated(iast_text):
    """
    Returns the IAST text with each character separated by a comma.
    Example: "rāma" -> "r,ā,m,a"
    """
    if not iast_text:
        return ""
    # We want to separate logical characters, not just python string chars?
    # Actually IAST uses combining marks sometimes, but SANSKRIT_TO_IAST uses precomposed chars mostly (ā, ī).
    # Standard python iteration yields unicode codepoints. 
    # Let's trust that python handles unicode chars (like 'ā') as length 1 string.
    # If using combining diacritics, we might split them. 
    # But our map uses precomposed (e.g. \u0101 for ā), so list(str) is safe.
    
    # However, 'kh', 'gh', 'ai', 'au' are digraphs in IAST representation of single sounds?
    # The prompt says "names in the IAST characterset, separating each character with a comma".
    # Usually IAST 'kh' is two characters 'k' and 'h'. 
    # "separating each character" likely means just standard character separation.
    # e.g. "S,h,i,v,a"
    
    return ",".join(list(iast_text))
