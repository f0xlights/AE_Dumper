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
        self.root.geometry("700x500")
        self.root.configure(bg="#1a1a1a")
        
        # Set Icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "ae.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(False, icon)
        except Exception as e:
            print(f"Errore caricamento icona: {e}")

        self.setup_ui()

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
        self.notebook.add(self.tab_single, text="Singolo Video")

        # Tab 2: Batch Download
        self.tab_batch = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_batch, text="Batch Download (Coda)")
        
        # Tab 3: Settings
        self.tab_settings = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_settings, text="Impostazioni")

        # --- Single Video Layout ---
        input_frame = tk.Frame(self.tab_single, bg="#1a1a1a")
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl_url = ttk.Label(input_frame, text="Incolla il link del video:")
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

        lbl_res = ttk.Label(result_frame, text="Log / Risultato:")
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

        lbl_batch = ttk.Label(batch_frame, text="Incolla la lista di link (uno per riga):")
        lbl_batch.pack(anchor="w")

        self.batch_text = tk.Text(batch_frame, height=15, bg="#333333", fg="white", font=("Consolas", 9), insertbackground="white")
        self.batch_text.pack(fill="both", expand=True, pady=5)
        self.create_context_menu(self.batch_text)

        self.btn_batch = ttk.Button(self.tab_batch, text="AVVIA BATCH", command=self.start_batch)
        self.btn_batch.pack(pady=10)

        # --- Settings Tab Layout ---
        sett_cnt = tk.Frame(self.tab_settings, bg="#1a1a1a")
        sett_cnt.pack(fill="both", expand=True, padx=20, pady=10)

        # Filename Template
        lbl_tmpl = ttk.Label(sett_cnt, text="Template Nome File:")
        lbl_tmpl.pack(anchor="w", pady=(0, 2))
        
        lbl_info = tk.Label(sett_cnt, text="Variabili: {date}, {cast}, {title}, {studio}", bg="#1a1a1a", fg="#888888", font=("Segoe UI", 8))
        lbl_info.pack(anchor="w", pady=(0, 5))

        self.tmpl_var = tk.StringVar(value=self.config.get("filename_template", "{date} - {cast} - {title} [{studio}]"))
        self.tmpl_var.trace("w", self.save_config_callback)
        self.ent_tmpl = ttk.Entry(sett_cnt, textvariable=self.tmpl_var, width=80)
        self.ent_tmpl.pack(fill="x", pady=5)
        self.create_context_menu(self.ent_tmpl)
        
        # N_m3u8DL-RE Options
        lbl_opts = ttk.Label(sett_cnt, text="Opzioni Downloader (N_m3u8DL-RE):")
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
        chk_log = tk.Checkbutton(sett_cnt, text="--no-log (Disabilita log file del tool)", variable=self.var_no_log, bg="#1a1a1a", fg="white", selectcolor="#333333", activebackground="#1a1a1a", activeforeground="white")
        chk_log.pack(anchor="w")

        self.var_no_date = tk.BooleanVar(value=self.config.get("flag_no_date", True))
        self.var_no_date.trace("w", self.save_config_callback)
        chk_date = tk.Checkbutton(sett_cnt, text="--no-date-info (Non scrivere data nel file)", variable=self.var_no_date, bg="#1a1a1a", fg="white", selectcolor="#333333", activebackground="#1a1a1a", activeforeground="white")
        chk_date.pack(anchor="w")


        # --- Shared Settings Area (Bottom) ---
        settings_frame = tk.Frame(self.root, bg="#1a1a1a")
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Download Folder
        lbl_dl = tk.Label(settings_frame, text="Cartella Download:", bg="#1a1a1a", fg="white")
        lbl_dl.pack(side="left")

        self.dl_path_var = tk.StringVar(value=self.config.get("download_path", os.path.join(os.path.expanduser("~"), "Downloads")))
        self.ent_dl = tk.Entry(settings_frame, textvariable=self.dl_path_var, width=30, bg="#333333", fg="white")
        self.ent_dl.pack(side="left", padx=5)
        
        btn_browse = ttk.Button(settings_frame, text="...", command=self.browse_folder, width=3)
        btn_browse.pack(side="left")

        # Quality
        lbl_qual = tk.Label(settings_frame, text="   Qualità:", bg="#1a1a1a", fg="white")
        lbl_qual.pack(side="left", padx=(10, 5))
        
        self.qual_var = tk.StringVar(value=self.config.get("quality", "Chiedi sempre"))
        self.qual_var.trace("w", self.save_config_callback) # Save on change
        self.cmb_qual = ttk.Combobox(settings_frame, textvariable=self.qual_var, state="readonly", width=12)
        self.cmb_qual['values'] = ["Chiedi sempre", "Migliore", "2160p", "1440p", "1080p", "720p", "480p"]
        self.cmb_qual.pack(side="left")

        # Headless
        self.var_headless = tk.BooleanVar(value=True)
        self.chk_headless = tk.Checkbutton(settings_frame, text="Headless", variable=self.var_headless, bg="#1a1a1a", fg="white", selectcolor="#333333", activebackground="#1a1a1a", activeforeground="white")
        self.chk_headless.pack(side="left", padx=10)

        # --- Progress Area (Status Label Only) ---
        progress_frame = tk.Frame(self.root, bg="#1a1a1a")
        progress_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_status = tk.Label(progress_frame, text="Pronto.", bg="#1a1a1a", fg="white", anchor="w")
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

    def save_config(self):
        self.config["download_path"] = self.dl_path_var.get()
        self.config["quality"] = self.qual_var.get()
        # New Settings
        self.config["filename_template"] = self.tmpl_var.get()
        self.config["threads"] = self.threads_var.get()
        self.config["flag_no_log"] = self.var_no_log.get()
        self.config["flag_no_date"] = self.var_no_date.get()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f)
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
            messagebox.showinfo("Copiato", "URL copiato negli appunti!")

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
            messagebox.showwarning("Errore", "Per favore inserisci un URL valido.")
            return

        self.btn_find.config(state="disabled")
        self.result_text.delete("1.0", tk.END)
        # Clear previous resolution buttons
        for widget in self.res_frame.winfo_children():
            widget.destroy()
            
        self.log("Inizializzazione browser...")
        
        # Start the background task
        threading.Thread(target=self.run_async_task, args=(url,), daemon=True).start()

    async def parse_m3u8(self, m3u8_url, filename="master"):
        try:
            self.root.after(0, lambda: self.log("Parsing master.m3u8..."))
            # requests is blocking, but acceptable here. Ideally use aiohttp.
            response = requests.get(m3u8_url)
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
            self.root.after(0, lambda: self.log(f"Errore parsing M3U8: {str(e)}"))

    async def display_resolutions(self, resolutions, filename="master"):
        if not resolutions:
            self.root.after(0, lambda: self.log("Nessuna risoluzione trovata."))
            return
            
        self.root.after(0, lambda: self.log(f"Trovate {len(resolutions)} risoluzioni."))
        self.root.after(0, lambda: self.log(f"Nome file: {filename}.mp4"))
        
        resolutions.sort(key=lambda x: int(x['label'].replace('p', '')), reverse=True)

        preferred_qual = self.qual_var.get()
        
        # Auto-download logic
        if preferred_qual != "Chiedi sempre":
            target_res = None
            
            if preferred_qual == "Migliore":
                target_res = resolutions[0]
                self.root.after(0, lambda: self.log("Selezionata qualità migliore automatica."))
            else:
                for res in resolutions:
                    if res['label'] == preferred_qual:
                        target_res = res
                        break
                
                if not target_res:
                    self.root.after(0, lambda: self.log(f"Qualità {preferred_qual} non trovata. Fallback sulla migliore ({resolutions[0]['label']})."))
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
            tk.Label(self.res_frame, text="Scarica Risoluzione:", bg="#1a1a1a", fg="#ff9900", font=("Segoe UI", 10, "bold")).pack(pady=5)
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
            self.root.after(0, lambda: messagebox.showerror("Errore", f"Tool mancante: {tool_path}"))
            return
            
        # Prepare Progress UI
        self.root.after(0, lambda: self.lbl_status.config(text=f"Download in corso: {label}"))
            
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
        
        self.root.after(0, lambda: self.log(f"Avvio download {label}..."))
        
        try:
            # Use asyncio subprocess to read output
            # creationflags=0x08000000 is CREATE_NO_WINDOW on Windows
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=0x08000000
            )

            # Regex to strip ANSI escape codes
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            last_progress_time = 0
            
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
                                     self.lbl_status.config(text=f"Scaricando... {val:.1f}%")

                                 self.root.after(0, lambda v=p: update_log_progress(v))
                         except:
                             pass

            return_code = await process.wait()
            
            if return_code == 0:
                self.root.after(0, lambda: self.log("Download Completato! 100%"))
                self.root.after(0, lambda: self.lbl_status.config(text="Completato."))
            else:
                 self.root.after(0, lambda: self.log(f"Errore download. Codice: {return_code}"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Eccezione download: {str(e)}"))




    def start_batch(self):
        content = self.batch_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Errore", "Lista vuota.")
            return
            
        urls = [line.strip() for line in content.split('\n') if line.strip()]
        if not urls:
             messagebox.showwarning("Errore", "Nessun URL valido trovato.")
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
        is_headless = self.var_headless.get()

        async with async_playwright() as p:
            self.root.after(0, lambda: self.log(f"Avvio Sessione Browser (Headless={is_headless})..."))
            
            # 1. Initialize Browser & Login
            context, page = await self.init_browser_session(p, user_data_dir, is_headless)
            if not page:
                self.root.after(0, lambda: self.log("Inizializzazione fallita."))
                self.reset_ui_state()
                return

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
                await self.process_video(page, url)
            
            await context.close()
            self.root.after(0, lambda: self.log("\nBatch Completato."))
            self.reset_ui_state()

    def reset_ui_state(self):
        self.root.after(0, lambda: self.btn_find.config(state="normal"))
        self.root.after(0, lambda: self.btn_batch.config(state="normal"))
        self.root.after(0, lambda: self.lbl_status.config(text="Pronto."))

    async def init_browser_session(self, p, user_data_dir, is_headless):
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=is_headless,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await Stealth().apply_stealth_async(page)
            
            # Login Check
            self.root.after(0, lambda: self.log("Verifica Login..."))
            await page.goto("https://www.adultempire.com/", wait_until="domcontentloaded")
            
            # Age Gate
            if "Confirm You Are Over 18" in await page.content():
                self.root.after(0, lambda: self.log("Age Gate..."))
                enter_btn = page.locator("a:has-text('Enter'), button:has-text('Enter')").first
                if await enter_btn.is_visible():
                    await enter_btn.click()
                    await page.wait_for_load_state("networkidle")

            # Check Status
            content = await page.content()
            if "Log Out" in content or "Sign Out" in content or "My Account" in content:
                self.root.after(0, lambda: self.log("Login OK!"))
                return context, page
            
            # Need Login
            self.root.after(0, lambda: self.log("Login richiesto..."))
            await page.goto("https://www.adultempire.com/account/loginpage?url=/account/accounthomepage/")
            
            self.root.after(0, lambda: self.log("Per favore esegui il login nel browser."))
            
            # Wait for Login
            for _ in range(120):
                content = await page.content()
                if "Log Out" in content or "Sign Out" in content or "My Account" in content:
                    self.root.after(0, lambda: self.log("Login Rilevato!"))
                    return context, page
                await asyncio.sleep(1)
            
            self.root.after(0, lambda: self.log("Timeout Login."))
            await context.close()
            return None, None
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Errore Init Browser: {e}"))
            return None, None

    async def process_video(self, page, user_url):
        try:
            # Metadata
            self.root.after(0, lambda: self.log("Analisi pagina prodotto..."))
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
                self.root.after(0, lambda: self.log(f"Warn Metadati: {e}"))

            # Player
            player_url = user_url
            if "?viewpart=videoplayer" not in player_url:
                player_url += "&viewpart=videoplayer" if "?" in player_url else "?viewpart=videoplayer"
            
            await page.goto(player_url)
            self.root.after(0, lambda: self.log("Cattura m3u8..."))
            
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
                self.root.after(0, lambda: self.log("M3U8 non trovato."))
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Errore Video: {e}"))

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
