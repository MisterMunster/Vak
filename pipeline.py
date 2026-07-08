"""Core audio -> text -> IPA -> Sanskrit -> IAST pipeline.

Processes a single local audio file with no Google account required.
Both the local GUI tab and the Google Drive batch processor run files
through process_file().
"""
import os
import shutil
import tempfile
from dataclasses import dataclass

import eng_to_ipa
import speech_recognition as sr

import ipa_map

# Formats the speech_recognition library reads natively.
NATIVE_FORMATS = {'.wav', '.aiff', '.aif', '.flac'}
# Formats that must first be converted to WAV via pydub, which needs ffmpeg.
CONVERTIBLE_FORMATS = {'.mp3', '.m4a', '.ogg', '.aac', '.wma'}
SUPPORTED_FORMATS = NATIVE_FORMATS | CONVERTIBLE_FORMATS

# eng_to_ipa marks stress with ˈ/ˌ and flags out-of-dictionary words with *.
# These are kept in the displayed IPA but must not reach the Sanskrit stage,
# where they would come out as literal garbage characters.
_IPA_NOISE = str.maketrans('', '', 'ˈˌ*')


@dataclass
class PipelineResult:
    file_name: str
    ok: bool = False
    text: str = ""
    ipa: str = ""
    sanskrit: str = ""
    iast: str = ""
    iast_separated: str = ""
    error: str = ""

    def as_row(self):
        """Values in Google Sheet / CSV column order (without timestamp)."""
        if self.ok:
            return [self.text, self.ipa, self.sanskrit, self.iast, self.iast_separated]
        return [f"[{self.error}]", "", "", "", ""]


def _find_winget_ffmpeg():
    """Locates a winget-installed ffmpeg for processes whose PATH predates
    the install (Windows only updates PATH for newly launched shells)."""
    local_appdata = os.environ.get('LOCALAPPDATA')
    if not local_appdata:
        return None
    import glob
    matches = glob.glob(os.path.join(
        local_appdata, 'Microsoft', 'WinGet', 'Packages',
        'Gyan.FFmpeg*', '*', 'bin', 'ffmpeg.exe'))
    return os.path.dirname(matches[0]) if matches else None


def ffmpeg_available():
    if shutil.which('ffmpeg') is not None:
        return True
    bin_dir = _find_winget_ffmpeg()
    if bin_dir:
        os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
        return shutil.which('ffmpeg') is not None
    return False


def needs_ffmpeg(path):
    return os.path.splitext(path)[1].lower() in CONVERTIBLE_FORMATS


def is_supported(path):
    return os.path.splitext(path)[1].lower() in SUPPORTED_FORMATS


def _to_wav(path):
    """Returns (readable_path, temp_path_or_None). Converts via pydub when
    the format is not natively readable."""
    if os.path.splitext(path)[1].lower() in NATIVE_FORMATS:
        return path, None

    from pydub import AudioSegment  # deferred: pulls in ffmpeg machinery
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    audio = AudioSegment.from_file(path)
    audio.export(wav_path, format="wav")
    return wav_path, wav_path


def process_file(path):
    """Transcribes one audio file and derives IPA, Sanskrit and IAST."""
    result = PipelineResult(file_name=os.path.basename(path))

    if not os.path.exists(path):
        result.error = "File not found"
        return result
    if not is_supported(path):
        result.error = f"Unsupported format ({os.path.splitext(path)[1]})"
        return result
    if needs_ffmpeg(path) and not ffmpeg_available():
        result.error = "FFmpeg is required to convert this format - install it or use WAV/FLAC"
        return result

    temp_wav = None
    try:
        wav_path, temp_wav = _to_wav(path)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        result.text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        result.error = "No intelligible speech detected"
        return result
    except sr.RequestError as e:
        result.error = f"Speech service unavailable (check internet): {e}"
        return result
    except Exception as e:
        result.error = f"Could not read audio: {e}"
        return result
    finally:
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except OSError:
                pass

    try:
        result.ipa = eng_to_ipa.convert(result.text)
        clean_ipa = result.ipa.translate(_IPA_NOISE)
        result.sanskrit = ipa_map.ipa_to_sanskrit(clean_ipa)
        result.iast = ipa_map.sanskrit_to_iast(result.sanskrit)
        result.iast_separated = ipa_map.get_iast_separated(result.iast)
        result.ok = True
    except Exception as e:
        result.error = f"Phonetic conversion failed: {e}"

    return result
