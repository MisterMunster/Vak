"""Filename-based transcript correction.

The free Google Web Speech API has no vocabulary-hint mechanism, so proper
nouns it doesn't know get snapped to the nearest common English words
("Kristen Ann Beifus" -> "Kristen Anne by Fitz"). But in Vak's workflow the
filename usually IS the ground truth - users name the file after the word or
name being spoken. So after transcription we compare the transcript to the
filename stem, both as raw text and as Metaphone phonetic encodings. If they
are similar enough, the filename wins.

The phonetic comparison is the important half: "by Fitz" and "Beifus" look
different on paper but encode almost identically, which is exactly the
failure mode of the speech API (it heard the right SOUNDS, it just picked
the wrong words for them).
"""
import os
import re

from rapidfuzz import fuzz
import jellyfish

# Similarity (0-100) required before the filename replaces the transcript.
# Below this, we assume the filename is unrelated to the audio content
# (e.g. "New Recording 12.m4a") and leave the transcript alone.
DEFAULT_THRESHOLD = 70

# Copy suffixes and bookkeeping noise commonly found in filename stems:
# "Kristen Ann Beifus (1)", "name - Copy", trailing counters, etc.
_COPY_SUFFIX = re.compile(r"(\s*[\(\[]\d+[\)\]]|\s*-\s*copy(\s*\d*)?)+$", re.IGNORECASE)
_SEPARATORS = re.compile(r"[_\-\.]+")
_MULTISPACE = re.compile(r"\s+")


def clean_stem(path):
    """Filename -> best-guess spoken text: strip extension, copy markers,
    and separator characters."""
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = _COPY_SUFFIX.sub("", stem)
    stem = _SEPARATORS.sub(" ", stem)
    return _MULTISPACE.sub(" ", stem).strip()


def _phonetic(text):
    """Word-by-word Metaphone encoding, joined with spaces."""
    encoded = []
    for word in re.findall(r"[A-Za-z']+", text):
        try:
            encoded.append(jellyfish.metaphone(word))
        except Exception:
            encoded.append(word.upper())
    return " ".join(encoded)


def similarity(transcript, stem):
    """0-100 similarity between transcript and filename stem, taking the
    best of orthographic and phonetic comparisons (token_sort tolerates
    word-order differences; plain ratio rewards exact structure)."""
    t, s = transcript.lower().strip(), stem.lower().strip()
    scores = [
        fuzz.ratio(t, s),
        fuzz.token_sort_ratio(t, s),
        fuzz.ratio(_phonetic(transcript), _phonetic(stem)),
    ]
    return max(scores)


def correct_transcript(transcript, path, threshold=DEFAULT_THRESHOLD):
    """Returns (final_text, corrected_from_or_None, score).

    If the filename stem is phonetically close to what the speech API
    heard, the stem is returned as the final text and the original
    transcript is returned as corrected_from so the UI can show what
    happened. Otherwise the transcript passes through untouched.
    """
    stem = clean_stem(path)

    # A usable stem needs at least two letters; "01.wav" tells us nothing.
    if len(re.sub(r"[^A-Za-z]", "", stem)) < 2 or not transcript.strip():
        return transcript, None, 0

    score = similarity(transcript, stem)
    if score >= threshold and transcript.strip().lower() != stem.lower():
        return stem, transcript, score
    return transcript, None, score
