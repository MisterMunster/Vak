"""Vak - Audio to Sanskrit converter GUI.

Two workflows:
  * "Convert Audio Files" tab - drop up to 20 local audio files, get
    transcription / IPA / Sanskrit / IAST in a table, export to CSV.
    No Google account needed.
  * "Google Drive (Advanced)" tab - the original service-account workflow:
    process a Drive folder and log results to a Google Sheet.
"""
import csv
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import pipeline
from config_manager import ConfigManager
from processor import DriveBatchProcessor

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

MAX_BATCH = 20

RESULT_COLUMNS = [
    ("file", "File", 150),
    ("status", "Status", 90),
    ("text", "Transcription", 160),
    ("ipa", "IPA", 140),
    ("sanskrit", "Sanskrit", 140),
    ("iast", "IAST", 140),
    ("iast_sep", "IAST (separated)", 170),
]


class VakApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vak - Audio to Sanskrit Converter")
        self.root.geometry("980x680")
        self.root.minsize(760, 560)

        self.config_manager = ConfigManager()
        self.queued_files = []
        self.results = []
        self.processing = False
        self.ui_queue = queue.Queue()

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self.local_tab = ttk.Frame(notebook)
        self.drive_tab = ttk.Frame(notebook)
        notebook.add(self.local_tab, text="  Convert Audio Files  ")
        notebook.add(self.drive_tab, text="  Google Drive (Advanced)  ")

        self._build_local_tab()
        self._build_drive_tab()
        self._poll_ui_queue()

    # ------------------------------------------------------------------ #
    # Local files tab
    # ------------------------------------------------------------------ #
    def _build_local_tab(self):
        tab = self.local_tab

        drop_text = (
            "Drop audio files here" if DND_AVAILABLE
            else "Click here to choose audio files"
        )
        self.drop_zone = tk.Label(
            tab,
            text=f"\N{HEAVY PLUS SIGN}  {drop_text}\n"
                 f"(or click to browse)\n\n"
                 f"WAV, MP3, M4A, FLAC, OGG  -  up to {MAX_BATCH} files per batch",
            bg="#eef2f7", fg="#2c3e50",
            font=("Segoe UI", 12),
            relief="groove", bd=2,
            height=5, cursor="hand2",
        )
        self.drop_zone.pack(fill="x", padx=12, pady=(12, 6))
        self.drop_zone.bind("<Button-1>", lambda e: self.browse_files())
        if DND_AVAILABLE:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self.on_drop)

        # Queued file list
        queue_frame = ttk.Frame(tab)
        queue_frame.pack(fill="x", padx=12, pady=(0, 6))

        list_frame = ttk.Frame(queue_frame)
        list_frame.pack(side="left", fill="both", expand=True)
        self.file_listbox = tk.Listbox(list_frame, height=5, selectmode="extended")
        list_scroll = ttk.Scrollbar(list_frame, command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=list_scroll.set)
        self.file_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")

        btn_frame = ttk.Frame(queue_frame)
        btn_frame.pack(side="right", fill="y", padx=(8, 0))
        self.count_label = ttk.Label(btn_frame, text=f"0 / {MAX_BATCH} files")
        self.count_label.pack(pady=(0, 6))
        ttk.Button(btn_frame, text="Add Files...", command=self.browse_files).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Clear List", command=self.clear_queue).pack(fill="x", pady=2)

        # Process button + progress
        self.btn_convert = tk.Button(
            tab, text="Convert Files", command=self.start_local_processing,
            bg="#2c7be5", fg="white", activebackground="#1a68d1",
            activeforeground="white", font=("Segoe UI", 11, "bold"), height=2,
        )
        self.btn_convert.pack(fill="x", padx=12, pady=6)

        progress_frame = ttk.Frame(tab)
        progress_frame.pack(fill="x", padx=12)
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True)
        self.status_label = ttk.Label(progress_frame, text="Ready", width=40, anchor="e")
        self.status_label.pack(side="right", padx=(8, 0))

        # Results table
        results_frame = ttk.Frame(tab)
        results_frame.pack(fill="both", expand=True, padx=12, pady=(6, 0))

        self.tree = ttk.Treeview(
            results_frame, columns=[c[0] for c in RESULT_COLUMNS],
            show="headings", selectmode="browse",
        )
        for key, heading, width in RESULT_COLUMNS:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, stretch=True)
        self.tree.tag_configure("error", foreground="#b02a37")

        tree_y = ttk.Scrollbar(results_frame, command=self.tree.yview)
        tree_x = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.config(yscrollcommand=tree_y.set, xscrollcommand=tree_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_y.grid(row=0, column=1, sticky="ns")
        tree_x.grid(row=1, column=0, sticky="ew")
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self.show_result_detail)

        hint = ttk.Label(
            tab, text="Double-click a row to view and copy the full result.",
            foreground="#6c757d",
        )
        hint.pack(anchor="w", padx=12)

        export_frame = ttk.Frame(tab)
        export_frame.pack(fill="x", padx=12, pady=(2, 12))
        ttk.Button(export_frame, text="Export Results to CSV...",
                   command=self.export_csv).pack(side="left")
        ttk.Button(export_frame, text="Clear Results",
                   command=self.clear_results).pack(side="left", padx=(8, 0))

    # ---- queue management ---- #
    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        self.add_files(paths)

    def browse_files(self):
        if self.processing:
            return
        exts = " ".join(f"*{e}" for e in sorted(pipeline.SUPPORTED_FORMATS))
        paths = filedialog.askopenfilenames(
            title="Choose audio files",
            filetypes=[("Audio files", exts), ("All files", "*.*")],
        )
        if paths:
            self.add_files(paths)

    def add_files(self, paths):
        if self.processing:
            return
        skipped, needs_ffmpeg = [], []
        for path in paths:
            if not os.path.isfile(path) or not pipeline.is_supported(path):
                skipped.append(os.path.basename(path))
                continue
            if path in self.queued_files:
                continue
            if len(self.queued_files) >= MAX_BATCH:
                messagebox.showwarning(
                    "Batch limit",
                    f"Only {MAX_BATCH} files can be processed per batch.\n"
                    "Extra files were not added.")
                break
            if pipeline.needs_ffmpeg(path) and not pipeline.ffmpeg_available():
                needs_ffmpeg.append(os.path.basename(path))
            self.queued_files.append(path)
            self.file_listbox.insert(tk.END, os.path.basename(path))

        self._update_count()
        if skipped:
            messagebox.showwarning(
                "Some files skipped",
                "These are not supported audio files:\n" + "\n".join(skipped[:10]))
        if needs_ffmpeg:
            messagebox.showwarning(
                "FFmpeg not found",
                "These files need FFmpeg to convert (it is not installed):\n"
                + "\n".join(needs_ffmpeg[:10])
                + "\n\nInstall FFmpeg or use WAV/FLAC files instead.")

    def remove_selected(self):
        if self.processing:
            return
        for index in reversed(self.file_listbox.curselection()):
            self.file_listbox.delete(index)
            del self.queued_files[index]
        self._update_count()

    def clear_queue(self):
        if self.processing:
            return
        self.file_listbox.delete(0, tk.END)
        self.queued_files.clear()
        self._update_count()

    def _update_count(self):
        self.count_label.config(text=f"{len(self.queued_files)} / {MAX_BATCH} files")

    # ---- processing ---- #
    def start_local_processing(self):
        if self.processing:
            return
        if not self.queued_files:
            messagebox.showinfo("No files", "Add some audio files first - "
                                "drag them into the box or click Add Files.")
            return

        self._set_processing(True)
        files = list(self.queued_files)
        self.progress.config(maximum=len(files), value=0)
        threading.Thread(target=self._local_worker, args=(files,), daemon=True).start()

    def _local_worker(self, files):
        for i, path in enumerate(files, start=1):
            self.ui_queue.put(("status", f"Processing {i} of {len(files)}: "
                                         f"{os.path.basename(path)}"))
            result = pipeline.process_file(path)
            self.ui_queue.put(("result", result, i))
        self.ui_queue.put(("local_done", len(files)))

    def _set_processing(self, active):
        self.processing = active
        state = "disabled" if active else "normal"
        self.btn_convert.config(state=state)
        self.btn_drive.config(state=state)

    # ---- results ---- #
    def _add_result(self, result):
        self.results.append(result)
        if result.ok:
            values = (result.file_name, "OK", result.text, result.ipa,
                      result.sanskrit, result.iast, result.iast_separated)
            tags = ()
        else:
            values = (result.file_name, "Failed", result.error, "", "", "", "")
            tags = ("error",)
        self.tree.insert("", tk.END, values=values, tags=tags)

    def show_result_detail(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        if index >= len(self.results):
            return
        result = self.results[index]

        win = tk.Toplevel(self.root)
        win.title(result.file_name)
        win.geometry("560x360")
        win.transient(self.root)

        fields = [("File", result.file_name)]
        if result.ok:
            fields += [("Transcription", result.text), ("IPA", result.ipa),
                       ("Sanskrit", result.sanskrit), ("IAST", result.iast),
                       ("IAST (separated)", result.iast_separated)]
        else:
            fields += [("Error", result.error)]

        for row, (label, value) in enumerate(fields):
            ttk.Label(win, text=label + ":", font=("Segoe UI", 9, "bold")).grid(
                row=row, column=0, sticky="nw", padx=10, pady=4)
            entry = tk.Entry(win, font=("Segoe UI", 11))
            entry.insert(0, value)
            entry.config(state="readonly", readonlybackground="white")
            entry.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=4)
        win.columnconfigure(1, weight=1)
        ttk.Label(win, text="Select text and press Ctrl+C to copy.",
                  foreground="#6c757d").grid(
            row=len(fields), column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

    def clear_results(self):
        if self.processing:
            return
        self.tree.delete(*self.tree.get_children())
        self.results.clear()

    def export_csv(self):
        if not self.results:
            messagebox.showinfo("Nothing to export", "Convert some files first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save results as CSV",
            defaultextension=".csv",
            filetypes=[("CSV (opens in Excel)", "*.csv")],
            initialfile="vak_results.csv",
        )
        if not path:
            return
        try:
            # utf-8-sig so Excel renders Devanagari and IAST diacritics
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["File", "Status", "Transcription", "IPA",
                                 "Sanskrit", "IAST", "IAST (separated)"])
                for r in self.results:
                    if r.ok:
                        writer.writerow([r.file_name, "OK", r.text, r.ipa,
                                         r.sanskrit, r.iast, r.iast_separated])
                    else:
                        writer.writerow([r.file_name, "Failed", r.error,
                                         "", "", "", ""])
            messagebox.showinfo("Exported", f"Results saved to:\n{path}")
        except OSError as e:
            messagebox.showerror("Export failed", str(e))

    # ------------------------------------------------------------------ #
    # Google Drive tab
    # ------------------------------------------------------------------ #
    def _build_drive_tab(self):
        tab = self.drive_tab
        self.service_account_path = tk.StringVar(
            value=self.config_manager.get_value("service_account_path"))
        self.input_folder_id = tk.StringVar()
        self.done_folder_id = tk.StringVar()
        self.sheet_id = tk.StringVar()

        ttk.Label(tab, text="Service Account JSON:").pack(anchor="w", padx=10, pady=(10, 0))
        frame_sa = ttk.Frame(tab)
        frame_sa.pack(fill="x", padx=10, pady=5)
        ttk.Entry(frame_sa, textvariable=self.service_account_path).pack(
            side="left", fill="x", expand=True)
        ttk.Button(frame_sa, text="Browse", command=self.browse_sa).pack(
            side="right", padx=(5, 0))

        ttk.Label(tab, text="Input Drive Folder ID:").pack(anchor="w", padx=10)
        self.combo_input = ttk.Combobox(tab, textvariable=self.input_folder_id)
        self.combo_input.pack(fill="x", padx=10, pady=5)

        ttk.Label(tab, text="Done Drive Folder ID:").pack(anchor="w", padx=10)
        self.combo_done = ttk.Combobox(tab, textvariable=self.done_folder_id)
        self.combo_done.pack(fill="x", padx=10, pady=5)

        ttk.Label(tab, text="Google Sheet ID:").pack(anchor="w", padx=10)
        self.combo_sheet = ttk.Combobox(tab, textvariable=self.sheet_id)
        self.combo_sheet.pack(fill="x", padx=10, pady=5)

        self.btn_drive = tk.Button(
            tab, text="Process Drive Folder", command=self.start_drive_processing,
            bg="#e1e1e1", font=("Segoe UI", 10, "bold"), height=2)
        self.btn_drive.pack(fill="x", padx=10, pady=15)

        ttk.Label(tab, text="Log:").pack(anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(tab, height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._load_drive_history()

    def _load_drive_history(self):
        for combo, key in ((self.combo_input, "input_folder_id"),
                           (self.combo_done, "done_folder_id"),
                           (self.combo_sheet, "sheet_id")):
            history = self.config_manager.get_history(key)
            combo['values'] = history
            if history:
                combo.set(history[0])

    def browse_sa(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            self.service_account_path.set(filename)

    def start_drive_processing(self):
        if self.processing:
            return
        sa_path = self.service_account_path.get().strip()
        input_id = self.input_folder_id.get().strip()
        done_id = self.done_folder_id.get().strip()
        sheet_id = self.sheet_id.get().strip()

        if not all([sa_path, input_id, done_id, sheet_id]):
            messagebox.showerror("Error", "All fields are required")
            return
        if not os.path.exists(sa_path):
            messagebox.showerror("Error", "Service Account file not found")
            return

        self.config_manager.set_value("service_account_path", sa_path)
        self.config_manager.add_to_history("input_folder_id", input_id)
        self.config_manager.add_to_history("done_folder_id", done_id)
        self.config_manager.add_to_history("sheet_id", sheet_id)
        self._load_drive_history()

        self._set_processing(True)
        self.drive_log("Starting processing...")
        threading.Thread(
            target=self._drive_worker,
            args=(sa_path, input_id, done_id, sheet_id), daemon=True).start()

    def _drive_worker(self, sa_path, input_id, done_id, sheet_id):
        processor = DriveBatchProcessor(sa_path)
        log = lambda msg: self.ui_queue.put(("drive_log", msg))

        success, msg = processor.authenticate()
        log(msg)
        if success:
            processor.process_folder(input_id, done_id, sheet_id, log)
        self.ui_queue.put(("drive_done",))

    def drive_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    # ------------------------------------------------------------------ #
    # Thread-safe UI updates
    # ------------------------------------------------------------------ #
    def _poll_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                kind = msg[0]
                if kind == "status":
                    self.status_label.config(text=msg[1])
                elif kind == "result":
                    self._add_result(msg[1])
                    self.progress.config(value=msg[2])
                elif kind == "local_done":
                    failed = sum(1 for r in self.results[-msg[1]:] if not r.ok)
                    done = msg[1] - failed
                    self.status_label.config(
                        text=f"Finished: {done} converted"
                             + (f", {failed} failed" if failed else ""))
                    self.clear_queue_after_run()
                    self._set_processing(False)
                elif kind == "drive_log":
                    self.drive_log(msg[1])
                elif kind == "drive_done":
                    self.drive_log("Done.")
                    self._set_processing(False)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_ui_queue)

    def clear_queue_after_run(self):
        self.file_listbox.delete(0, tk.END)
        self.queued_files.clear()
        self._update_count()


def _selftest(out_path):
    """Headless check that the text pipeline works in a packaged build.
    Used by CI on the PyInstaller output; writes results to a file because
    windowed executables have no console."""
    import eng_to_ipa
    import ipa_map
    text = "bhakti yoga church judge"
    ipa = eng_to_ipa.convert(text)
    sanskrit = ipa_map.ipa_to_sanskrit(ipa.translate(pipeline._IPA_NOISE))
    iast = ipa_map.sanskrit_to_iast(sanskrit)
    separated = ipa_map.get_iast_separated(iast)
    lines = [f"text: {text}", f"ipa: {ipa}", f"sanskrit: {sanskrit}",
             f"iast: {iast}", f"separated: {separated}",
             f"dnd: {DND_AVAILABLE}"]
    if all([ipa, sanskrit, iast, separated]) and "*" not in iast:
        lines.append("SELFTEST OK")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        _selftest(sys.argv[2] if len(sys.argv) > 2 else "selftest_out.txt")
        return
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    VakApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
