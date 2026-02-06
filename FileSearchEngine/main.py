import os
import re
import threading
import queue
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, ttk

# ---------------- CONFIG ----------------
MAX_RESULTS = 500
TEXT_EXTENSIONS = {".txt", ".py", ".md", ".log"}
# ---------------------------------------


class FileSearchApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("File Search Engine")
        self.geometry("1050x650")

        self.search_thread = None
        self.stop_event = threading.Event()
        self.result_queue = queue.Queue()
        self.files_checked = 0

        self._build_ui()
        self.after(100, self.process_queue)

    # ---------- UI ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Root folder
        root_frame = ctk.CTkFrame(self)
        root_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        root_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(root_frame, text="Root Folder:").grid(row=0, column=0, padx=5)
        self.root_path = ctk.StringVar(value=str(Path.home()))
        ctk.CTkEntry(root_frame, textvariable=self.root_path).grid(
            row=0, column=1, sticky="ew", padx=5
        )
        ctk.CTkButton(root_frame, text="Browse", command=self.browse).grid(
            row=0, column=2, padx=5
        )

        # Search row
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, sticky="ew", padx=10)
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(search_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.query = ctk.StringVar()
        ctk.CTkEntry(search_frame, textvariable=self.query).grid(
            row=0, column=1, sticky="ew", padx=5
        )

        self.regex = ctk.BooleanVar()
        self.case_sensitive = ctk.BooleanVar()
        ctk.CTkCheckBox(search_frame, text="Regex", variable=self.regex).grid(row=0, column=2)
        ctk.CTkCheckBox(search_frame, text="Case", variable=self.case_sensitive).grid(row=0, column=3)

        # Filters
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.scope = ctk.StringVar(value="both")
        ctk.CTkRadioButton(filter_frame, text="Files", variable=self.scope, value="files").grid(row=0, column=0)
        ctk.CTkRadioButton(filter_frame, text="Folders", variable=self.scope, value="folders").grid(row=0, column=1)
        ctk.CTkRadioButton(filter_frame, text="Both", variable=self.scope, value="both").grid(row=0, column=2)

        ctk.CTkLabel(filter_frame, text="Type:").grid(row=0, column=3, padx=(20, 5))
        self.file_type = ctk.StringVar(value="*")
        ctk.CTkEntry(filter_frame, textvariable=self.file_type, width=80).grid(row=0, column=4)

        ctk.CTkLabel(filter_frame, text="Min KB:").grid(row=0, column=5)
        self.min_size = ctk.StringVar()
        ctk.CTkEntry(filter_frame, textvariable=self.min_size, width=70).grid(row=0, column=6)

        ctk.CTkLabel(filter_frame, text="Max KB:").grid(row=0, column=7)
        self.max_size = ctk.StringVar()
        ctk.CTkEntry(filter_frame, textvariable=self.max_size, width=70).grid(row=0, column=8)

        self.search_btn = ctk.CTkButton(filter_frame, text="Search", command=self.start_search)
        self.search_btn.grid(row=0, column=9, padx=10)

        self.cancel_btn = ctk.CTkButton(filter_frame, text="Cancel", command=self.cancel_search, fg_color="darkred")
        self.cancel_btn.grid(row=0, column=10)

        # Results
        self.tree = ttk.Treeview(self, columns=("path", "size", "date"), show="headings")
        self.tree.heading("path", text="Path")
        self.tree.heading("size", text="Size")
        self.tree.heading("date", text="Modified")
        self.tree.column("path", width=650)
        self.tree.grid(row=3, column=0, sticky="nsew", padx=10)

        # Status
        self.status = ctk.StringVar(value="Idle")
        ctk.CTkLabel(self, textvariable=self.status).grid(row=4, column=0, sticky="w", padx=15, pady=5)

    # ---------- Actions ----------
    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.root_path.set(folder)

    def start_search(self):
        if not self.query.get().strip():
            return

        self.tree.delete(*self.tree.get_children())
        self.stop_event.clear()
        self.files_checked = 0
        self.status.set("Scanning...")

        self.search_thread = threading.Thread(target=self.scan_files, daemon=True)
        self.search_thread.start()

    def cancel_search(self):
        self.stop_event.set()
        self.status.set("Cancelled")

    # ---------- Search Logic ----------
    def scan_files(self):
        root = Path(self.root_path.get())
        query = self.query.get().strip()

        flags = 0 if self.case_sensitive.get() else re.IGNORECASE

        if self.regex.get():
            pattern = re.compile(query, flags)
        else:
            wildcard = re.escape(query).replace("\\*", ".*")
            pattern = re.compile(wildcard, flags)

        min_kb = float(self.min_size.get()) if self.min_size.get() else None
        max_kb = float(self.max_size.get()) if self.max_size.get() else None
        ftype = self.file_type.get().lower()

        for path, dirs, files in os.walk(root):
            if self.stop_event.is_set():
                return

            entries = []
            if self.scope.get() in ("files", "both"):
                entries += [Path(path) / f for f in files]
            if self.scope.get() in ("folders", "both"):
                entries += [Path(path) / d for d in dirs]

            for item in entries:
                if self.stop_event.is_set():
                    return

                self.files_checked += 1

                name = item.name
                if not pattern.search(name):
                    continue

                if item.is_file():
                    if ftype != "*" and not name.endswith(ftype):
                        continue

                    size_kb = item.stat().st_size / 1024
                    if min_kb and size_kb < min_kb:
                        continue
                    if max_kb and size_kb > max_kb:
                        continue
                else:
                    size_kb = ""

                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                self.result_queue.put((str(item), size_kb, mtime.strftime("%Y-%m-%d %H:%M")))

                if self.result_queue.qsize() >= MAX_RESULTS:
                    return

    def process_queue(self):
        try:
            while True:
                path, size, date = self.result_queue.get_nowait()
                self.tree.insert("", "end", values=(path, f"{size:.1f} KB" if size else "", date))
                self.status.set(f"Scanning… {self.files_checked} items checked")
        except queue.Empty:
            pass

        self.after(100, self.process_queue)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = FileSearchApp()
    app.mainloop()
