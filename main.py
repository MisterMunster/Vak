import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
from processor import BatchProcessor
import os

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

        self.create_widgets()

    def create_widgets(self):
        # Service Account File
        tk.Label(self.root, text="Service Account JSON:").pack(anchor="w", padx=10, pady=(10, 0))
        frame_sa = tk.Frame(self.root)
        frame_sa.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_sa, textvariable=self.service_account_path).pack(side="left", fill="x", expand=True)
        tk.Button(frame_sa, text="Browse", command=self.browse_sa).pack(side="right", padx=(5, 0))

        # Input Folder ID
        tk.Label(self.root, text="Input Drive Folder ID:").pack(anchor="w", padx=10)
        tk.Entry(self.root, textvariable=self.input_folder_id).pack(fill="x", padx=10, pady=5)

        # Done Folder ID
        tk.Label(self.root, text="Done Drive Folder ID:").pack(anchor="w", padx=10)
        tk.Entry(self.root, textvariable=self.done_folder_id).pack(fill="x", padx=10, pady=5)

        # Sheet ID
        tk.Label(self.root, text="Google Sheet ID:").pack(anchor="w", padx=10)
        tk.Entry(self.root, textvariable=self.sheet_id).pack(fill="x", padx=10, pady=5)

        # Process Button
        self.btn_process = tk.Button(self.root, text="Batch Process", command=self.start_processing, bg="#e1e1e1", height=2)
        self.btn_process.pack(fill="x", padx=10, pady=15)

        # Log Window
        tk.Label(self.root, text="Log:").pack(anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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
