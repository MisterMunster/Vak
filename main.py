import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
from processor import BatchProcessor
import os
from config_manager import ConfigManager

class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Batch Processor")
        self.root.geometry("600x500")

        # Variables
        self.service_account_path = tk.StringVar()
        self.input_folder_id = tk.StringVar()
        self.done_folder_id = tk.StringVar()
        self.sheet_id = tk.StringVar()

        self.config_manager = ConfigManager()
        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        # Service Account File
        tk.Label(self.root, text="Service Account JSON:").pack(anchor="w", padx=10, pady=(10, 0))
        frame_sa = tk.Frame(self.root)
        frame_sa.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_sa, textvariable=self.service_account_path).pack(side="left", fill="x", expand=True)
        tk.Button(frame_sa, text="Browse", command=self.browse_sa).pack(side="right", padx=(5, 0))

        # Input Folder ID
        tk.Label(self.root, text="Input Drive Folder ID:").pack(anchor="w", padx=10)
        self.combo_input = ttk.Combobox(self.root, textvariable=self.input_folder_id)
        self.combo_input.pack(fill="x", padx=10, pady=5)

        # Done Folder ID
        tk.Label(self.root, text="Done Drive Folder ID:").pack(anchor="w", padx=10)
        self.combo_done = ttk.Combobox(self.root, textvariable=self.done_folder_id)
        self.combo_done.pack(fill="x", padx=10, pady=5)

        # Sheet ID
        tk.Label(self.root, text="Google Sheet ID:").pack(anchor="w", padx=10)
        self.combo_sheet = ttk.Combobox(self.root, textvariable=self.sheet_id)
        self.combo_sheet.pack(fill="x", padx=10, pady=5)

        # Process Button
        self.btn_process = tk.Button(self.root, text="Batch Process", command=self.start_processing, bg="#e1e1e1", height=2)
        self.btn_process.pack(fill="x", padx=10, pady=15)

        # Log Window
        tk.Label(self.root, text="Log:").pack(anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def load_history(self):
        input_history = self.config_manager.get_history("input_folder_id")
        done_history = self.config_manager.get_history("done_folder_id")
        sheet_history = self.config_manager.get_history("sheet_id")

        self.combo_input['values'] = input_history
        self.combo_done['values'] = done_history
        self.combo_sheet['values'] = sheet_history

        if input_history: self.combo_input.set(input_history[0])
        if done_history: self.combo_done.set(done_history[0])
        if sheet_history: self.combo_sheet.set(sheet_history[0])

    def browse_sa(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            self.service_account_path.set(filename)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def start_processing(self):
        sa_path = self.service_account_path.get()
        input_id = self.input_folder_id.get()
        done_id = self.done_folder_id.get()
        sheet_id = self.sheet_id.get()

        if not all([sa_path, input_id, done_id, sheet_id]):
            messagebox.showerror("Error", "All fields are required")
            return

        if not os.path.exists(sa_path):
             messagebox.showerror("Error", "Service Account file not found")
             return

        self.btn_process.config(state="disabled")
        self.log("Starting processing thread...")

        # Save history
        self.config_manager.add_to_history("input_folder_id", input_id)
        self.config_manager.add_to_history("done_folder_id", done_id)
        self.config_manager.add_to_history("sheet_id", sheet_id)
        
        # update combo values immediately
        self.load_history()

        # Run in a separate thread to keep UI responsive
        threading.Thread(target=self.run_process, args=(sa_path, input_id, done_id, sheet_id), daemon=True).start()

    def run_process(self, sa_path, input_id, done_id, sheet_id):
        processor = BatchProcessor(sa_path)
        
        success, msg = processor.authenticate()
        self.log(msg)
        
        if success:
            processor.process_folder(input_id, done_id, sheet_id, self.log)
        
        self.log("Done.")
        self.root.after(0, lambda: self.btn_process.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
