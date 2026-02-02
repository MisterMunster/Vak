# ipa_map.py

# IPA to Sanskrit (Devanagari) Mapping
# This is a simplified mapping based on common English IPA (eng_to_ipa style) to Sanskrit approximating sounds.
IPA_TO_SANSKRIT = {
    'b': 'ब्', 'd': 'ड्', 'f': 'फ्', 'g': 'ग्', 'h': 'ह्', 'j': 'य्', 'k': 'क्', 'l': 'ल्',
    'm': 'म्', 'n': 'न्', 'p': 'प्', 'r': 'र्', 's': 'स्', 't': 'ट्', 'v': 'व्', 'w': 'व्',
    'z': 'ज्', 'ʒ': 'श्', 'dʒ': 'ज्', 'tʃ': 'च्', 'θ': 'थ्', 'ð': 'द्', 'ʃ': 'श्', 'ŋ': 'ङ्',
    'ə': 'अ', 'i': 'इ', 'ɪ': 'इ', 'e': 'ए', 'æ': 'ऐ', 'a': 'आ', 'ɑ': 'आ', 'ɒ': 'ओ', 'ɔ': 'औ',
    'u': 'उ', 'ʊ': 'उ', 'ʌ': 'अ', 'o': 'ओ', 'aɪ': 'ऐ', 'aʊ': 'औ', 'ɔɪ': 'ओइ', 'eə': 'एअ',
    'ɪə': 'इअ', 'ʊə': 'उअ', 'ju': 'यु', 'ɔː': 'औ', 'ɑː': 'आ', 'iː': 'ई', 'uː': 'ऊ', '3': 'अ',
    'ɛ': 'ए', 'ɡ': 'ग्', 'ɹ': 'र्', '?': '', 
    # Add more as needed
}

# Sanskrit (Devanagari) to IAST Mapping
SANSKRIT_TO_IAST = {
    'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū', 'ऋ': 'ṛ', 'ॠ': 'ṝ',
    'ऌ': 'ḷ', 'ॡ': 'ḹ', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'ṃ', 'अः': 'ḥ',
    'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'ṅa',
    'च': 'ca', 'छ': 'cha', ' ज': 'ja', 'झ': 'jha', 'ञ': 'ña',
    'ट': 'ṭa', 'ठ': 'ṭha', 'ड': 'ḍa', 'ढ': 'ḍha', 'ण': 'ṇa',
    'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
    'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
    'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
    'श': 'śa', 'ष': 'ṣa', 'स': 'sa', 'ह': 'ha',
    '्': '', # Virama suppresses the inherent vowel
    'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū', 'ृ': 'ṛ', 'ॄ': 'ṝ',
    'ॢ': 'ḷ', 'ॣ': 'ḹ', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'ṃ', 'ः': 'ḥ',
    
    # Consonants with Virama (halanta) mapping to clean consonants without 'a'
    'क्': 'k', 'ख्': 'kh', 'ग्': 'g', 'घ': 'gh', 'ङ्': 'ṅ',
    'च्': 'c', 'छ': 'ch', 'ज्': 'j', 'झ्': 'jh', 'ञ्': 'ñ',
    'ट्': 'ṭ', 'ठ्': 'ṭh', 'ड्': 'ḍ', 'ढ्': 'ḍh', 'ण्': 'ṇ',
    'त्': 't', 'थ्': 'th', 'द्': 'd', 'ध्': 'dh', 'न्': 'n',
    'प्': 'p', 'फ्': 'ph', 'ब्': 'b', 'भ्': 'bh', 'म्': 'm',
    'य्': 'y', 'र्': 'r', 'ल्': 'l', 'व्': 'v',
    'श्': 'ś', 'ष्': 'ṣ', 'स्': 's', 'ह्': 'h'
}

def ipa_to_sanskrit(ipa_text):
    """
    Converts/Transliterates English IPA symbols to Sanskrit Devanagari.
    This is a rough approximation as English phonemes don't map 1:1 to Sanskrit.
    """
    result = ""
    i = 0
    n = len(ipa_text)
    
    # Sort keys by length descending to match longest sequences first
    sorted_keys = sorted(IPA_TO_SANSKRIT.keys(), key=len, reverse=True)
    
    while i < n:
        match_found = False
        for key in sorted_keys:
            if ipa_text[i:].startswith(key):
                result += IPA_TO_SANSKRIT[key]
                # Check for consonant-vowel combinations to handle inherent 'a' or matras
                # For this simple version, we stick to the direct mapping.
                # In Devanagari, consonants in the map have Virama (e.g., 'k' -> 'क्')
                # But vowels (e.g. 'ə' -> 'अ') are independent vowels.
                # A proper transliterator would combine 'k' + 'ə' -> 'क'.
                # Let's try a logic fix purely for basic readability:
                # If we just added a vowel and previous was a halanta consonant, merge them?
                # For now, let's keep it simple: string replacement.
                i += len(key)
                match_found = True
                break
        
        if not match_found:
            # Keep unknown characters as is or skip
            result += ipa_text[i]
            i += 1
            
    # Post-processing to clean up:
    # This is a very naive implementation. 
    # e.g., 'क्' + 'अ' should become 'क'
    # 'क्' + 'आ' should become 'का'
    
    # We will do a second pass to fix "Halanta + Vowel" -> "Matra/Full Consonant"
    processed = ""
    # However, implementing a full sandhi/grammar engine is complex. 
    # Let's rely on the char-by-char concat for now, or just basic cleanup if user requested "Sanskrit".
    # Given the previous context was "Transliterate phonetic output", let's assume raw mapping is okay,
    # but let's try to fix at least the 'a' deletion.
    
    # Refined loop for merging:
    # Let's restart the mapping approach slightly.
    
    output = []
    # Re-run the matching with a buffer
    i = 0
    while i < n:
        best_match = None
        best_len = 0
        for key in sorted_keys:
            if ipa_text[i:].startswith(key):
                if len(key) > best_len:
                    best_match = IPA_TO_SANSKRIT[key]
                    best_len = len(key)
        
        if best_match is not None:
             output.append(best_match)
             i += best_len
        else:
            output.append(ipa_text[i])
            i += 1
            
    # Now join and try to fix Halanta+Vowel
    # Halanta char is one that ends in '्'
    # Vowels are 'अ', 'आ', etc.
    
    # Map Independent Vowel to Matra (when following a consonant)
    VOWEL_TO_MATRA = {
        'अ': '', # 'a' deletes the halanta
        'आ': 'ा', 'इ': 'ि', 'ई': 'ी', 'उ': 'ु', 'ऊ': 'ू',
        'ए': 'े', 'ऐ': 'ै', 'ओ': 'ो', 'औ': 'ौ',
        # etc.
    }
    
    final_str = ""
    last_was_halanta = False
    
    for chunk in output:
        # Check if current chunk is a vowel
        if last_was_halanta and chunk in VOWEL_TO_MATRA:
            # Remove the last char (virama '्') from final_str
            final_str = final_str[:-1] 
            # Add matra
            final_str += VOWEL_TO_MATRA[chunk]
            last_was_halanta = False # Now it's a full syllable
        else:
            final_str += chunk
            if chunk.endswith('्'):
                last_was_halanta = True
            else:
                last_was_halanta = False
                
    return final_str

def sanskrit_to_iast(sanskrit_text):
    """
    Converts Sanskrit Devanagari to IAST.
    """
    # This is simpler, mostly greedy replacement
    result = ""
    i = 0
    n = len(sanskrit_text)
    
    sorted_keys = sorted(SANSKRIT_TO_IAST.keys(), key=len, reverse=True)
    
    while i < n:
        match_found = False
        for key in sorted_keys:
            if sanskrit_text[i:].startswith(key):
                result += SANSKRIT_TO_IAST[key]
                i += len(key)
                match_found = True
                break
        
        if not match_found:
            result += sanskrit_text[i]
            i += 1
            
    return result
