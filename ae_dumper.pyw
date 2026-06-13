import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from playwright.async_api import async_playwright
import requests
import subprocess
from tkinter import filedialog
import os
from playwright_stealth import Stealth
import re
from datetime import datetime
import json
import sys

# Credentials
USERNAME = "anders_sund85@hotmail.com"
PASSWORD = "1o3j6akk"

class AEDumperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AdultEmpire Movie Dumper")
        self.root.geometry("800x650")
        self.root.configure(bg="#1a1a1a")
        
        # Set Icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "ae.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(False, icon)
        except Exception as e:
            print(f"Errore caricamento icona: {e}")

        self.active_processes = []
        self.setup_ui()
        
        # Check session on startup in background thread
        threading.Thread(target=self.run_startup_check, daemon=True).start()
        
        # Clean shutdown handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#1a1a1a", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#333333", foreground="#ffffff")
        style.configure("TNotebook", background="#1a1a1a", borderwidth=0)
        style.configure("TNotebook.Tab", background="#333333", foreground="white", padding=[10, 5], font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", "#ff9900")], foreground=[("selected", "black")])

        # Initialize Config
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.load_config()

        # Header
        header = tk.Label(self.root, text="AdultEmpire Movie Dumper", font=("Segoe UI", 18, "bold"), bg="#1a1a1a", fg="#ff9900")
        header.pack(pady=(10, 5))

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Single Video
        self.tab_single = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_single, text="Single Video")

        # Tab 2: Batch Download
        self.tab_batch = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_batch, text="Batch Download (Queue)")
        
        # Tab 3: Settings
        self.tab_settings = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_settings, text="Settings")

        # --- Single Video Layout ---
        input_frame = tk.Frame(self.tab_single, bg="#1a1a1a")
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl_url = ttk.Label(input_frame, text="Paste video link:")
        lbl_url.pack(anchor="w")

        self.url_entry = ttk.Entry(input_frame, width=80)
        self.url_entry.pack(pady=5, fill="x")
        self.url_entry.insert(0, "")
        self.create_context_menu(self.url_entry)

        self.btn_find = ttk.Button(self.tab_single, text="DOWNLOAD", command=self.start_finding)
        self.btn_find.pack(pady=5)

        # Result Area (Single)
        result_frame = tk.Frame(self.tab_single, bg="#1a1a1a")
        result_frame.pack(fill="both", expand=True, padx=20, pady=5)

        lbl_res = ttk.Label(result_frame, text="Log / Result:")
        lbl_res.pack(anchor="w")

        # Log color changed to Orange #ff9900
        self.result_text = tk.Text(result_frame, height=8, bg="#333333", fg="#ff9900", font=("Consolas", 9), insertbackground="white")
        self.result_text.pack(fill="both", expand=True, pady=5)
        self.create_context_menu(self.result_text)
        
        # Resolution Buttons Frame
        self.res_frame = tk.Frame(self.tab_single, bg="#1a1a1a")
        self.res_frame.pack(pady=10)

        # --- Batch Layout ---
        batch_frame = tk.Frame(self.tab_batch, bg="#1a1a1a")
        batch_frame.pack(fill="both", expand=True, padx=20, pady=10)

        lbl_batch = ttk.Label(batch_frame, text="Paste link list (one per line):")
        lbl_batch.pack(anchor="w")

        self.batch_text = tk.Text(batch_frame, height=15, bg="#333333", fg="white", font=("Consolas", 9), insertbackground="white")
        self.batch_text.pack(fill="both", expand=True, pady=5)
        self.create_context_menu(self.batch_text)

        self.btn_batch = ttk.Button(self.tab_batch, text="START BATCH", command=self.start_batch)
        self.btn_batch.pack(pady=10)

        # --- Settings Tab Layout ---
        sett_cnt = tk.Frame(self.tab_settings, bg="#1a1a1a")
        sett_cnt.pack(fill="both", expand=True, padx=20, pady=10)

        # Filename Template
        lbl_tmpl = ttk.Label(sett_cnt, text="Filename Template:")
        lbl_tmpl.pack(anchor="w", pady=(0, 2))
        
        lbl_info = tk.Label(sett_cnt, text="Variables: {date}, {cast}, {title}, {studio}", bg="#1a1a1a", fg="#888888", font=("Segoe UI", 8))
        lbl_info.pack(anchor="w", pady=(0, 5))

        self.tmpl_var = tk.StringVar(value=self.config.get("filename_template", "{date} - {cast} - {title} [{studio}]"))
        self.tmpl_var.trace("w", self.save_config_callback)
        self.ent_tmpl = ttk.Entry(sett_cnt, textvariable=self.tmpl_var, width=80)
        self.ent_tmpl.pack(fill="x", pady=5)
        self.create_context_menu(self.ent_tmpl)
        
        # N_m3u8DL-RE Options
        lbl_opts = ttk.Label(sett_cnt, text="Downloader Options (N_m3u8DL-RE):")
        lbl_opts.pack(anchor="w", pady=(15, 5))
        
        # Threads
        fr_threads = tk.Frame(sett_cnt, bg="#1a1a1a")
        fr_threads.pack(anchor="w", pady=2)
        tk.Label(fr_threads, text="Threads:", bg="#1a1a1a", fg="white").pack(side="left")
        self.threads_var = tk.StringVar(value=self.config.get("threads", "16"))
        self.threads_var.trace("w", self.save_config_callback)
        self.spn_threads = ttk.Spinbox(fr_threads, from_=1, to=32, textvariable=self.threads_var, width=5)
        self.spn_threads.pack(side="left", padx=5)
        
        # Flags
        self.var_no_log = tk.BooleanVar(value=self.config.get("flag_no_log", True))
        self.var_no_log.trace("w", self.save_config_callback)
        chk_log = tk.Checkbutton(sett_cnt, text="--no-log (Disable tool log files)", variable=self.var_no_log, bg="#1a1a1a", fg="white", selectcolor="#333333", activebackground="#1a1a1a", activeforeground="white")
        chk_log.pack(anchor="w")

        self.var_no_date = tk.BooleanVar(value=self.config.get("flag_no_date", True))
        self.var_no_date.trace("w", self.save_config_callback)
        chk_date = tk.Checkbutton(sett_cnt, text="--no-date-info (Don't write date in file)", variable=self.var_no_date, bg="#1a1a1a", fg="white", selectcolor="#333333", activebackground="#1a1a1a", activeforeground="white")
        chk_date.pack(anchor="w")

        # --- Credentials Settings ---
        tk.Frame(sett_cnt, bg="#444444", height=1).pack(fill="x", pady=(15, 5))
        lbl_creds_title = tk.Label(sett_cnt, text="Account Credentials", bg="#1a1a1a", fg="#ff9900", font=("Segoe UI", 10, "bold"))
        lbl_creds_title.pack(anchor="w", pady=(0, 5))

        fr_creds = tk.Frame(sett_cnt, bg="#1a1a1a")
        fr_creds.pack(anchor="w", pady=(5, 0))

        tk.Label(fr_creds, text="Email:", bg="#1a1a1a", fg="white", font=("Segoe UI", 10)).pack(side="left")
        self.username_var = tk.StringVar(value=self.config.get("username", USERNAME))
        self.ent_username = ttk.Entry(fr_creds, textvariable=self.username_var, width=30)
        self.ent_username.pack(side="left", padx=(5, 15))
        self.username_var.trace("w", self.save_config_callback)
        self.create_context_menu(self.ent_username)

        tk.Label(fr_creds, text="Password:", bg="#1a1a1a", fg="white", font=("Segoe UI", 10)).pack(side="left")
        self.password_var = tk.StringVar(value=self.config.get("password", PASSWORD))
        self.ent_password = ttk.Entry(fr_creds, textvariable=self.password_var, show="*", width=20)
        self.ent_password.pack(side="left", padx=5)
        self.password_var.trace("w", self.save_config_callback)
        self.create_context_menu(self.ent_password)

        # --- Proxy Settings ---
        tk.Frame(sett_cnt, bg="#444444", height=1).pack(fill="x", pady=(15, 5))
        lbl_proxy_title = tk.Label(sett_cnt, text="Proxy", bg="#1a1a1a", fg="#ff9900", font=("Segoe UI", 10, "bold"))
        lbl_proxy_title.pack(anchor="w", pady=(0, 5))

        self.var_proxy_enabled = tk.BooleanVar(value=self.config.get("proxy_enabled", False))
        self.var_proxy_enabled.trace("w", self.save_config_callback)
        chk_proxy = tk.Checkbutton(
            sett_cnt, text="Enable Proxy",
            variable=self.var_proxy_enabled,
            bg="#1a1a1a", fg="white", selectcolor="#333333",
            activebackground="#1a1a1a", activeforeground="white",
            font=("Segoe UI", 10)
        )
        chk_proxy.pack(anchor="w")

        fr_proxy = tk.Frame(sett_cnt, bg="#1a1a1a")
        fr_proxy.pack(anchor="w", pady=(5, 0))

        tk.Label(fr_proxy, text="Type:", bg="#1a1a1a", fg="white", font=("Segoe UI", 10)).pack(side="left")
        self.proxy_type_var = tk.StringVar(value=self.config.get("proxy_type", "socks5"))
        self.cmb_proxy_type = ttk.Combobox(fr_proxy, textvariable=self.proxy_type_var, state="readonly", width=8)
        self.cmb_proxy_type['values'] = ["socks5", "http"]
        self.cmb_proxy_type.pack(side="left", padx=(5, 15))
        self.proxy_type_var.trace("w", self.save_config_callback)

        tk.Label(fr_proxy, text="Host:", bg="#1a1a1a", fg="white", font=("Segoe UI", 10)).pack(side="left")
        self.proxy_host_var = tk.StringVar(value=self.config.get("proxy_host", "192.168.0.90"))
        self.ent_proxy_host = ttk.Entry(fr_proxy, textvariable=self.proxy_host_var, width=18)
        self.ent_proxy_host.pack(side="left", padx=(5, 15))
        self.proxy_host_var.trace("w", self.save_config_callback)
        self.create_context_menu(self.ent_proxy_host)

        tk.Label(fr_proxy, text="Porta:", bg="#1a1a1a", fg="white", font=("Segoe UI", 10)).pack(side="left")
        self.proxy_port_var = tk.StringVar(value=self.config.get("proxy_port", "9118"))
        self.ent_proxy_port = ttk.Entry(fr_proxy, textvariable=self.proxy_port_var, width=7)
        self.ent_proxy_port.pack(side="left", padx=5)
        self.proxy_port_var.trace("w", self.save_config_callback)
        self.create_context_menu(self.ent_proxy_port)

        tk.Label(sett_cnt, text="Privoxy (HTTP): port 8118  |  microsocks (SOCKS5): port 9118",
                 bg="#1a1a1a", fg="#666666", font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))

        # --- Shared Settings Area (Bottom) ---
        settings_frame = tk.Frame(self.root, bg="#1a1a1a")
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Download Folder
        lbl_dl = tk.Label(settings_frame, text="Download Folder:", bg="#1a1a1a", fg="white")
        lbl_dl.pack(side="left")

        self.dl_path_var = tk.StringVar(value=self.config.get("download_path", os.path.join(os.path.expanduser("~"), "Downloads")))
        self.ent_dl = tk.Entry(settings_frame, textvariable=self.dl_path_var, width=30, bg="#333333", fg="white")
        self.ent_dl.pack(side="left", padx=5)
        
        btn_browse = ttk.Button(settings_frame, text="...", command=self.browse_folder, width=3)
        btn_browse.pack(side="left")

        # Quality
        lbl_qual = tk.Label(settings_frame, text="   Quality:", bg="#1a1a1a", fg="white")
        lbl_qual.pack(side="left", padx=(10, 5))
        
        self.qual_var = tk.StringVar(value=self.config.get("quality", "Always ask"))
        self.qual_var.trace("w", self.save_config_callback) # Save on change
        self.cmb_qual = ttk.Combobox(settings_frame, textvariable=self.qual_var, state="readonly", width=12)
        self.cmb_qual['values'] = ["Always ask", "Best", "2160p", "1440p", "1080p", "720p", "480p"]
        self.cmb_qual.pack(side="left")

        # Login Button
        self.btn_login = ttk.Button(settings_frame, text="🔑 LOGIN", command=self.start_login, width=10)
        self.btn_login.pack(side="left", padx=(15, 5))

        self.lbl_login_status = tk.Label(settings_frame, text="● Not logged in", bg="#1a1a1a", fg="#ff4444", font=("Segoe UI", 9))
        self.lbl_login_status.pack(side="left")

        # --- Progress Area (Status Label Only) ---
        progress_frame = tk.Frame(self.root, bg="#1a1a1a")
        progress_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_status = tk.Label(progress_frame, text="Ready.", bg="#1a1a1a", fg="white", anchor="w")
        self.lbl_status.pack(fill="x")
        
        # Removed Progress Bar widget as requested

    def load_config(self):
        self.config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                pass
        
        # Defaults if missing
        if "filename_template" not in self.config:
            self.config["filename_template"] = "{date} - {cast} - {title} [{studio}]"
        if "threads" not in self.config:
            self.config["threads"] = "16"
        if "flag_no_log" not in self.config:
            self.config["flag_no_log"] = True
        if "flag_no_date" not in self.config:
            self.config["flag_no_date"] = True
        # Credentials defaults
        if "username" not in self.config:
            self.config["username"] = USERNAME
        if "password" not in self.config:
            self.config["password"] = PASSWORD
        # Proxy defaults
        if "proxy_enabled" not in self.config:
            self.config["proxy_enabled"] = False
        if "proxy_host" not in self.config:
            self.config["proxy_host"] = "192.168.0.90"
        if "proxy_port" not in self.config:
            self.config["proxy_port"] = "9118"

    def save_config(self):
        self.config["download_path"] = self.dl_path_var.get()
        self.config["quality"] = self.qual_var.get()
        # New Settings
        self.config["filename_template"] = self.tmpl_var.get()
        self.config["threads"] = self.threads_var.get()
        self.config["flag_no_log"] = self.var_no_log.get()
        self.config["flag_no_date"] = self.var_no_date.get()
        # Credentials
        self.config["username"] = self.username_var.get().strip()
        self.config["password"] = self.password_var.get().strip()
        # Proxy
        self.config["proxy_enabled"] = self.var_proxy_enabled.get()
        self.config["proxy_type"] = self.proxy_type_var.get()
        self.config["proxy_host"] = self.ent_proxy_host.get().strip()
        self.config["proxy_port"] = self.ent_proxy_port.get().strip()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_config_callback(self, *args):
        self.save_config()

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.dl_path_var.set(folder_selected)
            self.save_config()

    def log(self, message):
        self.result_text.insert(tk.END, f"{message}\n")
        self.result_text.see(tk.END)

    def copy_to_clipboard(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if content.startswith("http"):
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Copied", "URL copied to clipboard!")

    def spawn_download_thread(self, url, label, filename):
        """Helper to start download from UI button click"""
        # Disable buttons to prevent double click
        for widget in self.res_frame.winfo_children():
            widget.destroy()
            
        def run_dl():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.download_stream(url, label, filename))
            loop.close()
            
        threading.Thread(target=run_dl, daemon=True).start()


    def start_finding(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a valid URL.")
            return

        self.btn_find.config(state="disabled")
        self.result_text.delete("1.0", tk.END)
        # Clear previous resolution buttons
        for widget in self.res_frame.winfo_children():
            widget.destroy()
            
        self.log("Initializing browser...")
        
        # Start the background task
        threading.Thread(target=self.run_async_task, args=(url,), daemon=True).start()

    def _get_proxy_url(self):
        """Restituisce la stringa del proxy (socks5:// o http://) se abilitato, altrimenti None."""
        if self.var_proxy_enabled.get():
            host = self.ent_proxy_host.get().strip()
            port = self.ent_proxy_port.get().strip()
            scheme = self.proxy_type_var.get()  # 'socks5' o 'http'
            if host and port:
                return f"{scheme}://{host}:{port}"
        return None

    async def parse_m3u8(self, m3u8_url, filename="master"):
        try:
            self.root.after(0, lambda: self.log("Parsing master.m3u8..."))
            proxy_url = self._get_proxy_url()
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            response = requests.get(m3u8_url, proxies=proxies, timeout=30)
            response.raise_for_status()
            content = response.text
            
            base_url = m3u8_url.rsplit('/', 1)[0]
            
            resolutions = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "RESOLUTION=" in line:
                    res_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    if res_match:
                        res_str = res_match.group(1)
                        height = res_str.split('x')[1] + "p"
                        
                        if i + 1 < len(lines):
                            stream_url = lines[i+1].strip()
                            if not stream_url.startswith('http'):
                                stream_url = f"{base_url}/{stream_url}"
                                if '?' in m3u8_url and '?' not in stream_url:
                                    query = m3u8_url.split('?')[1]
                                    stream_url += f"?{query}"
                                    
                            resolutions.append({'label': height, 'url': stream_url})
            
            await self.display_resolutions(resolutions, filename)

        except Exception as e:
            self.root.after(0, lambda: self.log(f"M3U8 parsing error: {str(e)}"))

    async def display_resolutions(self, resolutions, filename="master"):
        if not resolutions:
            self.root.after(0, lambda: self.log("No resolutions found."))
            return
            
        self.root.after(0, lambda: self.log(f"Found {len(resolutions)} resolutions."))
        self.root.after(0, lambda: self.log(f"Filename: {filename}.mp4"))
        
        resolutions.sort(key=lambda x: int(x['label'].replace('p', '')), reverse=True)

        preferred_qual = self.qual_var.get()
        
        # Auto-download logic
        if preferred_qual != "Always ask":
            target_res = None
            
            if preferred_qual == "Best":
                target_res = resolutions[0]
                self.root.after(0, lambda: self.log("Selected automatic best quality."))
            else:
                for res in resolutions:
                    if res['label'] == preferred_qual:
                        target_res = res
                        break
                
                if not target_res:
                    self.root.after(0, lambda: self.log(f"Quality {preferred_qual} not found. Falling back to best ({resolutions[0]['label']})."))
                    target_res = resolutions[0]
            
            if target_res:
                 # In async flow, we await directly
                 await self.download_stream(target_res['url'], target_res['label'], filename)
                 return 
        
        # Manual Mode logic
        # If we are in batch, we can't wait for user input easily without freezing logic
        # So we just show buttons. The batch loop will continue unfortunately.
        # But user *should* set quality for batch.
        
        # Helper to update UI from thread
        def show_buttons():
            tk.Label(self.res_frame, text="Download Resolution:", bg="#1a1a1a", fg="#ff9900", font=("Segoe UI", 10, "bold")).pack(pady=5)
            btn_frame = tk.Frame(self.res_frame, bg="#1a1a1a")
            btn_frame.pack()
            
            for res in resolutions:
                 btn = ttk.Button(btn_frame, text=res['label'], command=lambda u=res['url'], l=res['label'], f=filename: self.spawn_download_thread(u, l, f))
                 btn.pack(side="left", padx=5)
                 
        self.root.after(0, show_buttons)


    async def download_stream(self, url, label, filename):
        save_dir = self.dl_path_var.get()
        tool_path = os.path.join(os.getcwd(), "tools", "N_m3u8DL-RE.exe")
        
        if not os.path.exists(tool_path):
            self.root.after(0, lambda: messagebox.showerror("Error", f"Missing tool: {tool_path}"))
            return
            
        # Prepare Progress UI
        self.root.after(0, lambda: self.lbl_status.config(text=f"Downloading: {label}"))
            
        # Build Command
        threads = self.threads_var.get()
        
        cmd = [
            tool_path,
            url,
            "--save-dir", save_dir,
            "--save-name", filename,
            "--thread-count", threads,
            "--tmp-dir", save_dir # Force temp dir to save dir to avoid script dir clutter
        ]
        
        if self.var_no_log.get():
            cmd.append("--no-log")
            
        if self.var_no_date.get():
            cmd.append("--no-date-info")
        
        self.root.after(0, lambda: self.log(f"Starting download {label}..."))
        
        # Create output dir if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        process = None
        try:
            # Use asyncio subprocess to read output
            # creationflags=0x08000000 is CREATE_NO_WINDOW on Windows
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=0x08000000
            )
            self.active_processes.append(process)

            # Regex to strip ANSI escape codes
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            # Read output for progress
            while True:
                chunk = await process.stdout.read(1024)
                if not chunk:
                    break
                
                chunk_str = chunk.decode('utf-8', errors='ignore')
                clean_str = ansi_escape.sub('', chunk_str)
                
                if "%" in clean_str:
                     matches = re.findall(r'(\d+\.?\d*)%', clean_str)
                     if matches:
                         try:
                             p = float(matches[-1])
                             if 0 <= p <= 100:
                                 # Update log with progress
                                 # We define a helper to update the last line
                                 def update_log_progress(val):
                                     # Check if last line is a progress line
                                     last_line = self.result_text.get("end-2l", "end-1c")
                                     if "Progress:" in last_line:
                                         self.result_text.delete("end-2l", "end-1c")
                                     
                                     self.result_text.insert(tk.END, f"Progress: {val:.1f}%\n")
                                     self.result_text.see(tk.END)
                                     self.lbl_status.config(text=f"Downloading... {val:.1f}%")

                                 self.root.after(0, lambda v=p: update_log_progress(v))
                         except:
                             pass
            
            return_code = await process.wait()
            
            if return_code == 0:
                self.root.after(0, lambda: self.log("Download Completed! 100%"))
                self.root.after(0, lambda: self.lbl_status.config(text="Completed."))
            else:
                self.root.after(0, lambda: self.log(f"Download error. Code: {return_code}"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Download exception: {str(e)}"))
        finally:
            if process and process in self.active_processes:
                self.active_processes.remove(process)




    def start_batch(self):
        content = self.batch_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Error", "List is empty.")
            return
            
        urls = [line.strip() for line in content.split('\n') if line.strip()]
        if not urls:
             messagebox.showwarning("Error", "No valid URLs found.")
             return

        self.btn_batch.config(state="disabled")
        self.btn_find.config(state="disabled")
        
        # Switch to Log Tab
        self.notebook.select(0)
        
        # Start background task with list
        threading.Thread(target=self.run_async_task, args=(urls, True), daemon=True).start()

    def run_async_task(self, data, is_batch=False):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.browser_task(data, is_batch))
        loop.close()

    async def browser_task(self, data, is_batch):
        urls = data if is_batch else [data]
        
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        is_headless = True  # Always headless for downloads as requested

        async with async_playwright() as p:
            self.root.after(0, lambda: self.log(f"Starting Browser Session (Headless={is_headless})..."))
            
            # 1. Initialize Browser & Login
            context, page = await self.init_browser_session(p, user_data_dir, is_headless)
            if not page:
                self.root.after(0, lambda: self.log("Initialization failed."))
                self.reset_ui_state()
                return

            try:
                # Setup M3U8 Listener
                self.captured_m3u8s = []
                async def handle_request(request):
                    if ".m3u8" in request.url:
                        self.captured_m3u8s.append(request.url)
                page.on("request", handle_request)

                # 2. Process URLs
                total = len(urls)
                for i, url in enumerate(urls):
                    if is_batch:
                        msg = f"\n>>> Processing [{i+1}/{total}]: {url}"
                        self.root.after(0, lambda m=msg: self.log(m))
                        self.root.after(0, lambda m=f"Batch {i+1}/{total}": self.lbl_status.config(text=m))
                    
                    self.captured_m3u8s.clear() # Reset for this video
                    try:
                        await self.process_video(page, url)
                    except Exception as e:
                        self.root.after(0, lambda err=e: self.log(f"Error processing video: {err}"))
            finally:
                await context.close()
                self.root.after(0, lambda: self.log("\nBatch Completed."))
                self.reset_ui_state()

    def reset_ui_state(self):
        self.root.after(0, lambda: self.btn_find.config(state="normal"))
        self.root.after(0, lambda: self.btn_batch.config(state="normal"))
        self.root.after(0, lambda: self.lbl_status.config(text="Ready."))

    async def init_browser_session(self, p, user_data_dir, is_headless):
        try:
            proxy_url = self._get_proxy_url()
            proxy_cfg = {"server": proxy_url} if proxy_url else None
            if proxy_url:
                self.root.after(0, lambda pu=proxy_url: self.log(f"Proxy active: {pu}"))
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=is_headless,
                proxy=proxy_cfg,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await Stealth().apply_stealth_async(page)
            
            # Verify saved session in chrome_profile
            self.root.after(0, lambda: self.log("Verifying saved session..."))
            await page.goto("https://www.adultempire.com/", wait_until="domcontentloaded")

            # Age Gate
            content = await page.content()
            age_gate_btn = page.locator("#ageConfirmationButton")
            if "confirm you are over 18" in content.lower() or "ageconfirmation" in page.url.lower() or await age_gate_btn.count() > 0:
                self.root.after(0, lambda: self.log("Age Gate..."))
                if await age_gate_btn.is_visible():
                    await age_gate_btn.click()
                else:
                    enter_btn = page.locator("a:has-text('Enter'), button:has-text('Enter'), button:has-text('18+')").first
                    if await enter_btn.is_visible():
                        await enter_btn.click()
                await page.wait_for_load_state("networkidle")

            content = await page.content()
            if "Log Out" in content or "Sign Out" in content or "My Account" in content:
                self.root.after(0, lambda: self.log("Session active OK!"))
                self.root.after(0, lambda: self.lbl_login_status.config(text="● Logged in", fg="#44ff88"))
                return context, page
            else:
                self.root.after(0, lambda: self.log("Session expired or missing. Use the LOGIN button."))
                self.root.after(0, lambda: self.lbl_login_status.config(text="● Not logged in", fg="#ff4444"))
                await context.close()
                return None, None

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Browser Init Error: {e}"))
            return None, None

    async def process_video(self, page, user_url):
        try:
            # Metadata
            self.root.after(0, lambda: self.log("Analyzing product page..."))
            scrape_url = user_url.split('?')[0]
            await page.goto(scrape_url, wait_until="domcontentloaded")
            
            final_filename = "master"
            try:
                title = await page.evaluate('''() => {
                    const h1 = document.querySelector('h1');
                    if (!h1) return "Unknown Title";
                    const clone = h1.cloneNode(true);
                    clone.querySelectorAll('.sale, .label, a').forEach(e => e.remove()); 
                    return clone.innerText.trim();
                }''')
                
                studio = "Unknown Studio"
                studio_el = page.locator('li:has-text("Studio:") a').first
                if await studio_el.count() > 0:
                    studio = (await studio_el.inner_text()).strip()
                
                date_str = "0000-00-00"
                released_el = page.locator('li:has-text("Released:")').first
                if await released_el.count() > 0:
                    released_text = await released_el.inner_text()
                    released_text = released_text.replace("Released:", "").strip()
                    try:
                        dt = datetime.strptime(released_text, "%b %d %Y")
                        date_str = dt.strftime("%Y-%m-%d")
                    except:
                        pass
                
                performers = []
                cast_locators = page.locator('.PerformerName')
                count = await cast_locators.count()
                for i in range(count):
                    name = (await cast_locators.nth(i).inner_text()).strip()
                    if name and name not in performers:
                        performers.append(name)
                
                performers_str = " & ".join(performers) if performers else "Unknown Cast"
                
                # Dynamic Filename Formatting
                template = self.tmpl_var.get()
                # Default safety
                if not template: 
                    template = "{date} - {cast} - {title} [{studio}]"
                
                # Replace placeholders
                f_name = template.replace("{date}", date_str)
                f_name = f_name.replace("{cast}", performers_str)
                f_name = f_name.replace("{title}", title)
                f_name = f_name.replace("{studio}", studio)
                
                final_filename = self.sanitize_filename(f_name)
                self.root.after(0, lambda: self.log(f"File: {final_filename}"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Metadata Warn: {e}"))

            # Player
            player_url = user_url
            if "?viewpart=videoplayer" not in player_url:
                player_url += "&viewpart=videoplayer" if "?" in player_url else "?viewpart=videoplayer"
            
            await page.goto(player_url)
            self.root.after(0, lambda: self.log("Capturing m3u8..."))
            
            final_m3u8 = None
            for _ in range(60):
                for url in self.captured_m3u8s:
                    if "master.m3u8" in url:
                        final_m3u8 = url
                        break
                if final_m3u8: break
                
                # Fallback to any m3u8 if waiting too long
                if _ > 10 and self.captured_m3u8s:
                     pass # Wait a bit longer for master preference
                await asyncio.sleep(0.5)
            
            if not final_m3u8 and self.captured_m3u8s:
                final_m3u8 = self.captured_m3u8s[0]
            
            if final_m3u8:
                await self.parse_m3u8(final_m3u8, final_filename)
            else:
                self.root.after(0, lambda: self.log("M3U8 not found."))
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Video Error: {e}"))

    def start_login(self):
        """Opens browser in visible mode for manual login (user clicked button)."""
        self.btn_login.config(state="disabled")
        self.lbl_status.config(text="Opening browser for login...")
        threading.Thread(target=self.run_login_task, args=(True,), daemon=True).start()

    def start_login_auto(self):
        """Starts automatic login in the background (headless first)."""
        self.btn_login.config(state="disabled")
        self.lbl_status.config(text="Logging in automatically...")
        threading.Thread(target=self.run_login_task, args=(False,), daemon=True).start()

    def run_startup_check(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.startup_check_task())
        except Exception as e:
            print(f"Startup check thread error: {e}")
        loop.close()

    async def startup_check_task(self):
        self.root.after(0, lambda: self.lbl_status.config(text="Verifying session..."))
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        
        try:
            async with async_playwright() as p:
                context, page = await self.init_browser_session(p, user_data_dir, is_headless=True)
                if page:
                    self.root.after(0, lambda: self.log("Session active OK on startup."))
                    self.root.after(0, lambda: self.lbl_status.config(text="Ready."))
                    await context.close()
                else:
                    self.root.after(0, lambda: self.log("Session expired or missing. Starting automatic login..."))
                    self.root.after(0, self.start_login_auto)
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Session check error: {e}"))
            self.root.after(0, lambda: self.log("Starting automatic login..."))
            self.root.after(0, self.start_login_auto)

    def run_login_task(self, force_headed=False):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.login_task(force_headed))
        loop.close()

    async def login_task(self, force_headed=False):
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        proxy_url = self._get_proxy_url()
        proxy_cfg = {"server": proxy_url} if proxy_url else None
        logged_in = False
        
        is_headless = not force_headed
        
        try:
            async with async_playwright() as p:
                if is_headless:
                    self.root.after(0, lambda: self.log("Starting automatic login in background..."))
                else:
                    self.root.after(0, lambda: self.log("Starting Playwright (headed mode)..."))

                try:
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir,
                        headless=is_headless,
                        proxy=proxy_cfg,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        viewport={"width": 1280, "height": 720},
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                    )
                except Exception as ex:
                    err = str(ex)
                    self.root.after(0, lambda e=err: self.log(f"Browser launch error: {e}"))
                    return

                page = context.pages[0] if context.pages else await context.new_page()

                try:
                    await Stealth().apply_stealth_async(page)
                except Exception as ex:
                    err = str(ex)
                    self.root.after(0, lambda e=err: self.log(f"Warn stealth: {e}"))

                try:
                    await page.goto("https://www.adultempire.com/account/loginpage", wait_until="domcontentloaded", timeout=30000)
                    # Automate Age Gate if visible so user gets directly to the login form
                    age_gate_btn = page.locator("#ageConfirmationButton")
                    if await age_gate_btn.is_visible():
                        self.root.after(0, lambda: self.log("Automating Age Gate..."))
                        await age_gate_btn.click()
                        await page.wait_for_load_state("networkidle")
                except Exception as ex:
                    err = str(ex)
                    self.root.after(0, lambda e=err: self.log(f"Navigation error: {e}"))

                # Captcha selectors to verify if a captcha challenge is visible
                captcha_selectors = [
                    'iframe[src*="recaptcha"]',
                    'iframe[src*="turnstile"]',
                    '.g-recaptcha',
                    '#g-recaptcha-response',
                    '.cf-turnstile',
                    'div:has-text("captcha")'
                ]

                # Check if captcha is visible on the page before auto-filling
                if is_headless:
                    has_captcha = False
                    for selector in captcha_selectors:
                        try:
                            loc = page.locator(selector)
                            if await loc.count() > 0 and await loc.first.is_visible():
                                has_captcha = True
                                break
                        except:
                            pass
                    
                    if has_captcha:
                        self.root.after(0, lambda: self.log("reCAPTCHA detected! Switching to headed mode for manual login..."))
                        await context.close()
                        # Run headed login task
                        self.root.after(0, lambda: threading.Thread(target=self.run_login_task, args=(True,), daemon=True).start())
                        return

                # Auto-fill credentials and submit
                try:
                    self.root.after(0, lambda: self.log("Auto-filling credentials..."))
                    await page.wait_for_selector("#login_username", timeout=10000)
                    await asyncio.sleep(0.5)
                    
                    username = self.username_var.get().strip()
                    password = self.password_var.get().strip()
                    
                    await page.fill("#login_username", username)
                    await asyncio.sleep(0.3)
                    await page.fill("#login_password", password)
                    await asyncio.sleep(0.3)
                    
                    login_btn = page.locator('form[action*="Login"] button[type="submit"], button:has-text("Log In"), button:has-text("Sign In")').first
                    if await login_btn.is_visible():
                        self.root.after(0, lambda: self.log("Submitting login form..."))
                        await login_btn.click()
                except Exception as ex:
                    self.root.after(0, lambda: self.log(f"Auto-fill error: {ex}"))

                if is_headless:
                    self.root.after(0, lambda: self.log("Waiting for automated login completion..."))
                    self.root.after(0, lambda: self.lbl_status.config(text="Logging in automatically..."))
                else:
                    self.root.after(0, lambda: self.log("Please login in the browser. It will be detected automatically..."))
                    self.root.after(0, lambda: self.lbl_status.config(text="Waiting for login..."))

                for _ in range(30 if is_headless else 600):  # 30 seconds max for auto, 10 minutes max for manual
                    try:
                        if not context.pages:
                            self.root.after(0, lambda: self.log("Browser closed by user."))
                            break
                        content = await page.content()
                        if "Log Out" in content or "Sign Out" in content or "My Account" in content:
                            logged_in = True
                            break
                        
                        # In headless mode, check if a captcha was triggered during login
                        if is_headless and _ > 3:
                            has_captcha = False
                            for selector in captcha_selectors:
                                try:
                                    loc = page.locator(selector)
                                    if await loc.count() > 0 and await loc.first.is_visible():
                                        has_captcha = True
                                        break
                                except:
                                    pass
                            if has_captcha:
                                self.root.after(0, lambda: self.log("reCAPTCHA triggered during login! Switching to headed mode..."))
                                logged_in = False
                                break
                    except Exception as ex:
                        err = str(ex)
                        # If page is navigating it's normal, wait and retry
                        if "navigating" in err or "content" in err.lower():
                            await asyncio.sleep(1)
                            continue
                        # True disconnection (browser closed by user)
                        self.root.after(0, lambda e=err: self.log(f"Browser disconnected: {e}"))
                        break
                    await asyncio.sleep(1)

                if logged_in:
                    self.root.after(0, lambda: self.log("✓ Login completed! Session saved in chrome_profile."))
                    self.root.after(0, lambda: self.lbl_status.config(text="Login saved."))
                    self.root.after(0, lambda: self.lbl_login_status.config(text="● Logged in", fg="#44ff88"))
                    await asyncio.sleep(2)
                else:
                    if is_headless:
                        self.root.after(0, lambda: self.log("Automatic login failed or reCAPTCHA detected. Opening headed browser..."))
                        await context.close()
                        self.root.after(0, lambda: threading.Thread(target=self.run_login_task, args=(True,), daemon=True).start())
                        return
                    else:
                        self.root.after(0, lambda: self.log("Login not completed or window closed before login."))
                        self.root.after(0, lambda: self.lbl_status.config(text="Login not completed."))

                try:
                    await context.close()
                except Exception:
                    pass

        except Exception as ex:
            err = str(ex)
            self.root.after(0, lambda e=err: self.log(f"Login error: {e}"))
            if is_headless:
                self.root.after(0, lambda: threading.Thread(target=self.run_login_task, args=(True,), daemon=True).start())
        finally:
            if not is_headless or logged_in:
                self.root.after(0, lambda: self.btn_login.config(state="normal"))
                self.root.after(0, lambda: self.lbl_status.config(text="Ready."))


    def on_closing(self):
        """Kills any active subprocesses on exit to avoid orphan processes."""
        if hasattr(self, 'active_processes'):
            for p in self.active_processes:
                try:
                    p.terminate()
                except:
                    pass
        self.root.destroy()

    def create_context_menu(self, widget):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Taglia", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copia", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Incolla", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Seleziona tutto", command=lambda: widget.event_generate("<<SelectAll>>"))
        
        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)
            return "break"
            
        widget.bind("<Button-3>", show_menu)

    def sanitize_filename(self, name):
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '-', name)
        # Remove control characters
        name = "".join([c for c in name if ord(c) >= 32])
        return name.strip()

if __name__ == "__main__":
    root = tk.Tk()
    app = AEDumperGUI(root)
    root.mainloop()
