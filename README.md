# Vak - Audio to Sanskrit Converter

Vak transcribes spoken audio to text, then converts the text to its International Phonetic Alphabet (IPA) representation, Sanskrit (Devanagari) script, and IAST transliteration.

There are two ways to use it:

1. **Convert Audio Files (recommended for most users)** - drag & drop up to 20 audio files from your computer, click one button, and get the results in a table you can export to a CSV file (opens in Excel). No Google account or setup required.
2. **Google Drive (Advanced)** - the original automated workflow: process every audio file in a Google Drive folder, log results to a Google Sheet, and move the processed files to a "Done" folder. Requires a Google service account.

## Quick Start (for everyday use)

1. Install [Python 3](https://www.python.org/downloads/) (check "Add Python to PATH" during install).
2. Install the app's dependencies - open a terminal in the Vak folder and run:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   python main.py
   ```
4. In the **Convert Audio Files** tab:
   * Drag audio files into the big drop box (or click it to browse). Up to **20 files per batch**.
   * Click **Convert Files**.
   * Watch the progress bar; results appear in the table as each file finishes.
   * Double-click any row to see the full result and copy text from it.
   * Click **Export Results to CSV...** to save everything to a file that opens in Excel.

An internet connection is required (transcription uses the Google Web Speech API).

### Supported audio formats

| Format | Needs FFmpeg? |
|--------|---------------|
| WAV, FLAC, AIFF | No |
| MP3, M4A, OGG, AAC, WMA | Yes |

**FFmpeg** is bundled automatically via the `imageio-ffmpeg` dependency in `requirements.txt` - no separate install needed. `pip install -r requirements.txt` pulls in a self-contained ffmpeg binary for your platform, and the compiled `.app`/`.exe` builds include it too. If a system-installed `ffmpeg` is already on your PATH, that one is used instead.

## Google Drive Mode (Advanced)

You need a **Google Service Account** with access to your Drive folders and Google Sheet.

1. **Create a Service Account**: In the [Google Cloud Console](https://console.cloud.google.com/), create a project and enable the **Google Drive API** and **Google Sheets API**.
2. **Download JSON Key**: Create a key for the service account and download the JSON file.
3. **Share Resources** with the service account email (Editor access):
   * Your **Input Drive Folder**
   * Your **Done Drive Folder**
   * Your **Google Sheet**

Then in the **Google Drive (Advanced)** tab, fill in the service account JSON path and the three IDs (taken from the URLs of the folders/sheet) and click **Process Drive Folder**. The app remembers your last 10 entries for each field.

Each processed file appends a row to the sheet: `Filename, Timestamp, Text, Phonetic, Sanskrit, IAST, IAST_Separated`, and the file is moved to the Done folder.

## Component Overview

| File | Purpose |
|------|---------|
| `main.py` | The GUI (tkinter). Local drag & drop tab + Google Drive tab. Runs work on a background thread and updates the UI through a thread-safe queue. |
| `pipeline.py` | The core pipeline: audio file → WAV → transcription → IPA → Sanskrit → IAST → separated IAST. Used by both tabs. |
| `ipa_map.py` | The IPA→Devanagari and Devanagari→IAST mapping tables and conversion functions. |
| `processor.py` | Google Drive/Sheets integration: lists, downloads, and moves Drive files; appends result rows to the sheet. |
| `config_manager.py` | Remembers recently used field values in `history.json` (stored next to the app). |

## Logic Flow

1. **Audio → WAV**: Files not natively readable are converted with `pydub`/FFmpeg to a temporary WAV (deleted afterwards).
2. **Transcribe**: The Google Web Speech API (via `speech_recognition`) turns speech into text.
3. **Filename correction**: The Web Speech API accepts no vocabulary hints, so unfamiliar proper nouns get replaced with soundalike common words ("Kristen Ann Beifus" → "Kristen Anne by Fitz"). Since files are typically named after the word being spoken, the transcript is compared to the filename stem both as text and as Metaphone phonetic encodings (`rapidfuzz` + `jellyfish`); if they score ≥ 70/100, the filename wins. Corrected rows show **OK (name-corrected)** in the status column, and the detail view shows what the API originally heard. Files with unrelated names ("New Recording 12.m4a") score low and are left untouched.
4. **IPA**: `eng_to_ipa` converts the text to IPA. Stress marks (`ˈ ˌ`) and out-of-dictionary markers (`*`) are shown in the IPA column but stripped before the next step so they don't pollute the output.
5. **Sanskrit**: The IPA string is mapped phoneme-by-phoneme (longest match first) to Devanagari, merging vowels into matras after consonants.
6. **IAST**: The Devanagari is transliterated to IAST.
7. **Separated IAST**: The IAST string is split into individual Sanskrit phonemes, comma-separated. Digraphs are kept whole: "bhakti" → `bh,a,k,t,i`; "Kailash" → `k,ai,l,ā,ś`.

### Strict IAST Charset

The output uses this IAST character set:
`a ā i ī u ū ṛ ṝ ḷ l̤ e ai o au k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l v ś ṣ s h ḻ ṁ m̐ ḥ ẖ ḫ`
