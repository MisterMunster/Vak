"""Pluggable speech-to-text backends.

Two engines:

  * "google"  - the free Google Web Speech API (online). Light and fast but
                accepts no vocabulary hints, so unfamiliar proper nouns get
                snapped to soundalike common words.
  * "whisper" - OpenAI Whisper running locally via faster-whisper (offline
                after a one-time model download). Much stronger on names,
                and it accepts an initial_prompt, which we seed with the
                filename stem so the expected word/name biases recognition
                *before* transcription instead of being patched afterwards.

Both raise TranscriptionError subclasses so pipeline.process_file() can
report failures uniformly.
"""
import os
import re

import speech_recognition as sr

GOOGLE = "google"
WHISPER = "whisper"
DEFAULT_ENGINE = GOOGLE

# Whisper model sizes exposed in the GUI. "small" is the sweet spot for
# short name/word clips on CPU; "tiny"/"base" are faster and lighter.
WHISPER_MODELS = ("tiny", "base", "small", "medium")
DEFAULT_WHISPER_MODEL = "small"

# Rough one-time download sizes, shown to the user before first load.
_MODEL_SIZES_MB = {"tiny": 75, "base": 145, "small": 465, "medium": 1500}


class TranscriptionError(Exception):
    """Base: the engine ran but produced no usable text."""


class NoSpeechError(TranscriptionError):
    """No intelligible speech was detected in the audio."""


class EngineUnavailableError(TranscriptionError):
    """The engine cannot run (missing dependency / no internet)."""


# --------------------------------------------------------------------- #
# Google Web Speech (online)
# --------------------------------------------------------------------- #
def _transcribe_google(wav_path, hint=None):
    # The free endpoint has no hint mechanism; `hint` is accepted for
    # interface symmetry and ignored.
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        raise NoSpeechError("No intelligible speech detected")
    except sr.RequestError as e:
        raise EngineUnavailableError(
            f"Speech service unavailable (check internet): {e}")


# --------------------------------------------------------------------- #
# Whisper via faster-whisper (offline)
# --------------------------------------------------------------------- #
_whisper_model = None
_whisper_model_name = None


def whisper_available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def whisper_model_loaded():
    return _whisper_model is not None


def whisper_download_note(model_name=DEFAULT_WHISPER_MODEL):
    mb = _MODEL_SIZES_MB.get(model_name, 500)
    return (f"Loading Whisper '{model_name}' model "
            f"(first use downloads ~{mb} MB, then it's cached locally)...")


def _get_whisper(model_name):
    """Lazy singleton. Reloads only if the user switched model sizes."""
    global _whisper_model, _whisper_model_name
    if _whisper_model is None or _whisper_model_name != model_name:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            model_name, device="cpu", compute_type="int8")
        _whisper_model_name = model_name
    return _whisper_model


def _transcribe_whisper(wav_path, hint=None, model_name=DEFAULT_WHISPER_MODEL):
    if not whisper_available():
        raise EngineUnavailableError(
            "Whisper engine not installed - run: pip install faster-whisper")
    model = _get_whisper(model_name)

    # The filename stem is our best guess at what the clip contains. Feeding
    # it as initial_prompt biases the decoder toward that vocabulary, which
    # is exactly what the Google endpoint can't do. Whisper still transcribes
    # what it actually hears - the prompt is a nudge, not a mandate - and the
    # post-hoc filename correction in pipeline.py remains as a safety net.
    prompt = f"A recording of the name or phrase: {hint}." if hint else None

    segments, _info = model.transcribe(
        wav_path,
        language="en",
        initial_prompt=prompt,
        beam_size=5,
        vad_filter=True,          # skip leading/trailing silence
        condition_on_previous_text=False,
    )
    text = " ".join(s.text.strip() for s in segments).strip()

    # Whisper punctuates ("Kristen Ann Beifus.") - strip sentence punctuation
    # so it doesn't leak into the IPA/Sanskrit stages.
    text = re.sub(r"[.,!?;:]+$", "", text).strip()
    text = re.sub(r"\s+", " ", text)

    if not text:
        raise NoSpeechError("No intelligible speech detected")
    return text


# --------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------- #
def engine_label(engine):
    return {GOOGLE: "Google Web Speech (online)",
            WHISPER: "Whisper (offline, better with names)"}.get(engine, engine)


def transcribe(wav_path, engine=DEFAULT_ENGINE, hint=None,
               whisper_model=DEFAULT_WHISPER_MODEL):
    """Transcribe a WAV file with the chosen engine.

    hint: expected content (typically the cleaned filename stem), used to
    bias engines that support it. Raises TranscriptionError on failure.
    """
    if engine == WHISPER:
        return _transcribe_whisper(wav_path, hint=hint, model_name=whisper_model)
    return _transcribe_google(wav_path, hint=hint)
