import ast
import ctypes
import hashlib
import http.server
import operator
import os
import platform
import re
import shlex
import shutil
import socketserver
import string
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import urllib.request
import webbrowser
from tkinter.scrolledtext import ScrolledText

# PyTerminal 3.15 / ShellBridge v1.0.2 — Ultimate Complete Edition with Glassmorphism & Auto-Update

THEMES = {
    "glass": {
        "bg": "#1c1c1e", "title_bg": "#2c2c2e", "panel_bg": "#242426",
        "text": "#ffffff", "muted": "#8e8e93", "accent": "#0a84ff", "border": "#3a3a3c",
        "alpha": 0.93
    },
    "light": {
        "bg": "#f5f5f7", "title_bg": "#e9e9ed", "panel_bg": "#ffffff",
        "text": "#242426", "muted": "#77777d", "accent": "#3478f6", "border": "#d6d6dc",
        "alpha": 1.0
    },
    "dark": {
        "bg": "#1e1e1e", "title_bg": "#2d2d2d", "panel_bg": "#252526",
        "text": "#d4d4d4", "muted": "#858585", "accent": "#007acc", "border": "#3f3f46",
        "alpha": 1.0
    },
    "matrix": {
        "bg": "#0d0208", "title_bg": "#190b14", "panel_bg": "#000000",
        "text": "#00ff66", "muted": "#008f39", "accent": "#00ff66", "border": "#003311",
        "alpha": 1.0
    }
}

current_theme = "glass"
t = THEMES[current_theme]
BG, TITLE_BG, PANEL_BG, TEXT, MUTED, ACCENT, BORDER = t["bg"], t["title_bg"], t["panel_bg"], t["text"], t["muted"], t["accent"], t["border"]
FONT = ("Menlo", 10)

root = tk.Tk()
root.title("ShellBridge [v1.0.2]")
root.geometry("1020x680")
root.minsize(700, 450)
root.overrideredirect(True)  # Borderless clean custom frame
root.configure(bg=BG)
root.attributes('-alpha', t["alpha"])

command_history = []
history_index = 0
drive_directories = {}
current_shell = "internal"  # "internal", "cmd", "powershell", "python"
active_http_server = None

if os.name == "nt":
    for letter in string.ascii_uppercase:
        drive = letter + ":\\"
        if os.path.isdir(drive):
            drive_directories[letter] = drive

current_drive, _ = os.path.splitdrive(os.getcwd())
current_drive = current_drive[:1].upper()
if current_drive:
    drive_directories[current_drive] = os.getcwd()


# ---------------- Window Title Bar & Dragging ----------------

titlebar = tk.Frame(root, bg=TITLE_BG, height=42)
titlebar.pack(fill="x")
titlebar.pack_propagate(False)

def start_move(event):
    root._drag_x = event.x
    root._drag_y = event.y

def do_move(event):
    x = event.x_root - root._drag_x
    y = event.y_root - root._drag_y
    root.geometry(f"+{x}+{y}")

titlebar.bind("<Button-1>", start_move)
titlebar.bind("<B1-Motion>", do_move)

traffic_lights = tk.Frame(titlebar, bg=TITLE_BG)
traffic_lights.pack(side="left", padx=(14, 10))

def make_light(color, command=None):
    light = tk.Canvas(traffic_lights, width=12, height=12, bg=TITLE_BG, highlightthickness=0, bd=0)
    light.create_oval(1, 1, 11, 11, fill=color, outline=color)
    if command:
        light.bind("<Button-1>", lambda event: command())
    light.pack(side="left", padx=(0, 7))
    return light

make_light("#ff5f57", root.destroy)
make_light("#febc2e")
make_light("#28c840")

title_label = tk.Label(titlebar, text="ShellBridge [v1.0.2 - Pro Edition]", bg=TITLE_BG, fg=TEXT, font=("Arial", 10, "bold"))
title_label.place(relx=0.5, rely=0.5, anchor="center")
title_label.bind("<Button-1>", start_move)
title_label.bind("<B1-Motion>", do_move)


# ---------------- Quick Access Toolbar ----------------

toolbar = tk.Frame(root, bg=TITLE_BG, height=32)
toolbar.pack(fill="x", padx=14, pady=(6, 0))

def add_toolbar_btn(text, cmd):
    btn = tk.Button(toolbar, text=text, bg=PANEL_BG, fg=TEXT, bd=0, relief="flat", font=("Arial", 9), command=cmd, padx=8)
    btn.pack(side="left", padx=2, pady=3)
    return btn


# ---------------- Terminal Interface ----------------

terminal_frame = tk.Frame(root, bg=PANEL_BG, highlightbackground=BORDER, highlightthickness=1)
terminal_frame.pack(fill="both", expand=True, padx=14, pady=(8, 8))

output = ScrolledText(
    terminal_frame, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
    selectbackground="#264f78", selectforeground=TEXT, font=FONT,
    borderwidth=0, relief="flat", wrap="word", padx=12, pady=12
)
output.pack(fill="both", expand=True)
output.configure(state="disabled")

input_row = tk.Frame(root, bg=BG)
input_row.pack(fill="x", padx=14, pady=(0, 14))

prompt_label = tk.Label(input_row, text="›", bg=BG, fg=ACCENT, font=("Arial", 17, "bold"), width=2)
prompt_label.pack(side="left", padx=(0, 4))

entry = tk.Entry(
    input_row, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT, font=FONT,
    relief="flat", highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
)
entry.pack(side="left", fill="x", expand=True, ipady=8)


def write(message=""):
    output.configure(state="normal")
    output.insert("end", str(message) + "\n")
    output.see("end")
    output.configure(state="disabled")

def clear_output():
    output.configure(state="normal")
    output.delete("1.0", "end")
    output.configure(state="disabled")


# ---------------- Theme Application ----------------

def apply_theme(theme_name):
    global current_theme, BG, TITLE_BG, PANEL_BG, TEXT, MUTED, ACCENT, BORDER
    if theme_name not in THEMES:
        write(f"Unknown theme: {theme_name}. Choose from: glass, light, dark, matrix")
        return
    current_theme = theme_name
    t = THEMES[theme_name]
    BG, TITLE_BG, PANEL_BG, TEXT, MUTED, ACCENT, BORDER = t["bg"], t["title_bg"], t["panel_bg"], t["text"], t["muted"], t["accent"], t["border"]
    
    root.configure(bg=BG)
    root.attributes('-alpha', t["alpha"])
    titlebar.configure(bg=TITLE_BG)
    traffic_lights.configure(bg=TITLE_BG)
    title_label.configure(bg=TITLE_BG, fg=TEXT)
    toolbar.configure(bg=TITLE_BG)
    terminal_frame.configure(bg=PANEL_BG, highlightbackground=BORDER)
    output.configure(bg=PANEL_BG, fg=TEXT, insertbackground=TEXT)
    input_row.configure(bg=BG)
    prompt_label.configure(bg=BG, fg=ACCENT)
    entry.configure(bg=PANEL_BG, fg=TEXT, insertbackground=TEXT, highlightbackground=BORDER, highlightcolor=ACCENT)
    write(f"Theme switched to: {theme_name.upper()}")


# ---------------- Auto-Updater from GitHub ----------------

GITHUB_RAW_URL = "https://raw.githubusercontent.com/53mRepton/ShellBridge/main/shellbridge.py"

def check_for_updates():
    write("Checking GitHub for updates...")
    try:
        req = urllib.request.Request(GITHUB_RAW_URL, headers={'User-Agent': 'ShellBridge-Updater'})
        with urllib.request.urlopen(req, timeout=5) as response:
            remote_code = response.read().decode('utf-8')
            
        version_match = re.search(r'ShellBridge\s+\[v([\d\.]+)\]', remote_code)
        if not version_match:
            write("Could not parse version from remote repository.")
            return
            
        remote_version = version_match.group(1)
        current_version = "1.0.2"
        
        if remote_version > current_version:
            write(f"New version found: v{remote_version} (Current: v{current_version})")
            script_path = os.path.abspath(sys.argv[0])
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(remote_code)
                
            write("Update successful! Please restart ShellBridge to apply changes.")
            messagebox.showinfo("Update Complete", f"ShellBridge has been updated to v{remote_version}.\nPlease restart the application.")
        else:
            write(f"You are already running the latest version (v{current_version}).")
    except Exception as e:
        write(f"Failed to check for updates: {e}")


# ---------------- Pro Tools (Hashes & HTTP Server) ----------------

def calculate_hashes(filename):
    if not filename:
        write("Usage: hash <filename>")
        return
    filename = os.path.expanduser(filename.strip('"'))
    if not os.path.exists(filename):
        write(f"File not found: {filename}")
        return
    try:
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        with open(filename, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                md5_hash.update(byte_block)
                sha256_hash.update(byte_block)
        write(f"File: {os.path.basename(filename)}")
        write(f"MD5:    {md5_hash.hexdigest()}")
        write(f"SHA256: {sha256_hash.hexdigest()}")
    except Exception as e:
        write(f"Error computing hashes: {e}")

def start_http_server(port_str="8000"):
    global active_http_server
    try:
        port = int(port_str.strip()) if port_str else 8000
        if active_http_server:
            write("HTTP server is already running!")
            return
        
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", port), Handler)
        active_http_server = httpd
        
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        write(f"HTTP Server started successfully at http://localhost:{port} serving '{os.getcwd()}'")
        write("Type 'stopserve' to shut down the server.")
    except Exception as e:
        write(f"Could not start HTTP server: {e}")

def stop_http_server():
    global active_http_server
    if active_http_server:
        active_http_server.shutdown()
        active_http_server.server_close()
        active_http_server = None
        write("HTTP Server stopped.")
    else:
        write("No active HTTP server is running.")


# ---------------- Drive & File Operations ----------------

def change_drive(letter):
    global current_drive
    letter = letter.upper()
    if os.name != "nt":
        write("Drive switching is available on Windows only.")
        return
    drive_root = letter + ":\\"
    if not os.path.isdir(drive_root):
        write(f"Drive {letter}: is unavailable.")
        return
    target = drive_directories.get(letter, drive_root)
    if not os.path.isdir(target):
        target = drive_root
    try:
        os.chdir(target)
        current_drive = letter
        drive_directories[letter] = os.getcwd()
        write(os.getcwd())
    except OSError as error:
        write(f"Cannot access drive: {error}")

def touch_file(filename):
    if not filename:
        write("Usage: touch <filename>")
        return
    filename = os.path.expanduser(filename.strip('"'))
    try:
        with open(filename, 'a'):
            os.utime(filename, None)
        write(f"Touched: {filename}")
    except Exception as e:
        write(f"Could not touch file: {e}")

def remove_target(arg):
    try:
        args = shlex.split(arg)
    except Exception:
        args = arg.split()

    if not args:
        write("Usage: rm <file>  or  rm -rf <path>")
        return
    
    recursive = False
    target_path = None
    
    if args[0].startswith("-"):
        flags = args[0]
        if "r" in flags or "f" in flags:
            recursive = True
        if len(args) > 1:
            target_path = args[1]
        else:
            write("Missing target path for deletion.")
            return
    else:
        target_path = args[0]
        
    target_path = os.path.abspath(os.path.expanduser(target_path.strip('"')))
    
    if not os.path.exists(target_path):
        write(f"Path not found: {target_path}")
        return
        
    try:
        if os.path.isdir(target_path):
            if recursive:
                shutil.rmtree(target_path)
                write(f"Removed directory recursively: {target_path}")
            else:
                write(f"Is a directory: {target_path}. Use 'rm -rf' to remove folders.")
        else:
            os.remove(target_path)
            write(f"Removed file: {target_path}")
    except Exception as e:
        write(f"Could not remove target: {e}")


# ---------------- Windows SUBST Helpers ----------------

def subst_add(letter, folder):
    if os.name != "nt":
        write("SUBST is available on Windows only.")
        return
    letter = letter.upper().rstrip(":")
    folder = os.path.expandvars(folder.strip().strip('"'))
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        write(f"Folder not found: {folder}")
        return
    device = letter + ":"
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        target = "\\??\\" + folder
        result = kernel32.DefineDosDeviceW(0x1 | 0x8, device, target)
        if result:
            write(f"Mapping created: {device} -> {folder}")
        else:
            write(f"Mapping failed. Error: {ctypes.get_last_error()}")
    except Exception as error:
        write(f"Could not create mapping: {error}")

def subst_remove(letter):
    if os.name != "nt":
        write("SUBST is available on Windows only.")
        return
    letter = letter.upper().rstrip(":")
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        result = kernel32.DefineDosDeviceW(0x2 | 0x4 | 0x8, letter + ":", None)
        if result:
            write(f"Removed mapping definition for {letter}:")
        else:
            write(f"Could not remove mapping. Error: {ctypes.get_last_error()}")
    except Exception as error:
        write(f"Could not remove mapping: {error}")

def subst_list():
    if os.name != "nt":
        write("SUBST is available on Windows only.")
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    buffer = ctypes.create_unicode_buffer(4096)
    size = kernel32.GetLogicalDriveStringsW(len(buffer), buffer)
    if size == 0:
        write("Could not retrieve Windows drive list.")
        return
    found = False
    for drive in buffer[:size].split("\0"):
        if not drive:
            continue
        device_buffer = ctypes.create_unicode_buffer(4096)
        if kernel32.QueryDosDeviceW(drive[:2], device_buffer, len(device_buffer)):
            target = device_buffer.value
            if target.startswith("\\??\\"):
                write(f"{drive} -> {target[4:]}")
                found = True
    if not found:
        write("No SUBST-style mappings detected.")


# ---------------- Curl & ARP Helpers ----------------

def run_curl(arguments=""):
    try:
        cmd_list = ["curl"] + (shlex.split(arguments) if arguments else [])
        result = subprocess.run(cmd_list, capture_output=True, text=True, errors="replace", timeout=30, cwd=os.getcwd())
        if result.stdout.strip(): write(result.stdout.rstrip())
        if result.stderr.strip(): write(result.stderr.rstrip())
    except Exception as error:
        write(f"Could not run curl: {error}")

def pure_python_arp():
    write("Interface: Active Network Adapters (ARP & Local Info)")
    write("-" * 50)
    try:
        if os.name == "nt":
            res = subprocess.run(["netsh", "interface", "ipv4", "show", "neighbors"], capture_output=True, text=True, timeout=10)
            if res.stdout.strip():
                for line in res.stdout.splitlines():
                    write(line)
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        write(f"Local Hostname: {hostname}")
        write(f"Local IP Address: {local_ip}")
    except Exception as e:
        write(f"Could not retrieve network info: {e}")


# ---------------- Built-in Nano Text Editor ----------------

def open_nano(filename=""):
    if not filename:
        write("Usage: nano <filename>")
        return
    filename = os.path.expanduser(filename.strip('"'))
    nano_win = tk.Toplevel(root)
    nano_win.title(f"Nano - {filename}")
    nano_win.geometry("700x450")
    nano_win.configure(bg=PANEL_BG)
    nano_win.attributes('-alpha', 0.95)
    
    header = tk.Label(nano_win, text=f" Editing: {filename}  |  Ctrl+S to Save, Ctrl+Q to Close", bg=TITLE_BG, fg=TEXT, anchor="w", font=("Arial", 9, "bold"))
    header.pack(fill="x", padx=5, pady=5)
    
    txt_area = ScrolledText(nano_win, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT, font=FONT, padx=10, pady=10, relief="flat")
    txt_area.pack(fill="both", expand=True, padx=5, pady=5)
    
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8", errors="replace") as f:
                txt_area.insert("1.0", f.read())
        except Exception as e:
            write(f"Error opening file: {e}")
            
    def save_file(event=None):
        try:
            content = txt_area.get("1.0", "end-1c")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            write(f"File saved successfully: {filename}")
            nano_win.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save: {e}")
            
    nano_win.bind("<Control-s>", save_file)
    nano_win.bind("<Control-q>", lambda e: nano_win.destroy())
    txt_area.focus_set()


def export_session(filepath):
    if not filepath:
        filepath = "shellbridge_session.txt"
    try:
        content = output.get("1.0", "end")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        write(f"Session exported successfully to: {os.path.abspath(filepath)}")
    except Exception as e:
        write(f"Failed to export session: {e}")


# ---------------- Toolbar Buttons Configuration ----------------

add_toolbar_btn("Clear", clear_output)
add_toolbar_btn("Nano", lambda: open_nano("notes.txt"))
add_toolbar_btn("Python REPL", lambda: run_command_from_external("shell python"))
add_toolbar_btn("Serve", lambda: start_http_server("8000"))
add_toolbar_btn("Stop Serve", stop_http_server)
add_toolbar_btn("Update", check_for_updates)
add_toolbar_btn("Glass Theme", lambda: apply_theme("glass"))
add_toolbar_btn("Matrix Theme", lambda: apply_theme("matrix"))


# ---------------- Tab Autocompletion ----------------

BUILTIN_COMMANDS = [
    "help", "echo", "clear", "pwd", "ls", "dir", "cd", "drives", "subst",
    "arp", "pyinfo", "calc", "start", "history", "exit", "shell", "nano",
    "theme", "export", "touch", "rm", "curl", "hash", "serve", "stopserve", "update"
]

def handle_tab(event):
    typed = entry.get().strip()
    if not typed:
        return "break"
    parts = typed.split(" ")
    if len(parts) == 1:
        matches = [c for c in BUILTIN_COMMANDS if c.startswith(parts[0].lower())]
        if len(matches) == 1:
            entry.delete(0, "end")
            entry.insert(0, matches[0] + " ")
        elif len(matches) > 1:
            write("  ".join(matches))
    else:
        current_prefix = parts[-1]
        try:
            files = os.listdir()
            matches = [f for f in files if f.startswith(current_prefix)]
            if len(matches) == 1:
                parts[-1] = matches[0]
                entry.delete(0, "end")
                entry.insert(0, " ".join(parts))
        except Exception:
            pass
    return "break"


def run_command_from_external(cmd_text):
    entry.delete(0, "end")
    entry.insert(0, cmd_text)
    run_command()


# ---------------- Command Processor ----------------

def run_command(event=None):
    global history_index, current_drive, current_shell

    command = entry.get().strip()
    entry.delete(0, "end")

    if not command:
        return "break"

    command_history.append(command)
    history_index = len(command_history)

    write(f"{os.getcwd()}  ›  {command}")

    try:
        if command.lower().startswith("shell "):
            mode = command.split(" ", 1)[1].strip().lower()
            if mode in ("internal", "cmd", "powershell", "ps", "python", "py"):
                current_shell = "powershell" if mode in ("ps", "powershell") else ("python" if mode in ("py", "python") else mode)
                write(f"Switched shell mode to: {current_shell.upper()}")
                if current_shell == "python":
                    write("Interactive Python REPL active. Type 'exit' or 'quit' to return.")
            else:
                write("Invalid mode. Use: shell internal, shell cmd, shell powershell, or shell python")
            return "break"

        if current_shell == "cmd":
            if command.lower() == "exit":
                current_shell = "internal"
                write("Switched back to internal shell mode.")
                return "break"
            res = subprocess.run(["cmd.exe", "/c", f'cd /d "{os.getcwd()}" && {command}'], capture_output=True, text=True, errors="replace", timeout=30)
            if res.stdout.strip(): write(res.stdout.rstrip())
            if res.stderr.strip(): write(res.stderr.rstrip())
            return "break"

        if current_shell == "powershell":
            if command.lower() == "exit":
                current_shell = "internal"
                write("Switched back to internal shell mode.")
                return "break"
            ps_exe = "pwsh" if platform.system() != "Windows" else "powershell.exe"
            res = subprocess.run([ps_exe, "-NoProfile", "-Command", f'Set-Location "{os.getcwd()}"; {command}'], capture_output=True, text=True, errors="replace", timeout=30)
            if res.stdout.strip(): write(res.stdout.rstrip())
            if res.stderr.strip(): write(res.stderr.rstrip())
            return "break"

        if current_shell == "python":
            if command.lower() in ("exit", "quit"):
                current_shell = "internal"
                write("Switched back to internal shell mode.")
                return "break"
            try:
                try:
                    result = eval(command)
                    if result is not None:
                        write(repr(result))
                except SyntaxError:
                    exec(command)
            except Exception as e:
                write(f"Python Error: {e}")
            return "break"

        # Drive shortcuts (e.g. C:, D:)
        if len(command) == 2 and command[0].isalpha() and command[1] == ":":
            change_drive(command[0])
            return "break"

        # --- Internal Mode Built-ins ---
        parts = shlex.split(command, posix=False)
        if not parts:
            return "break"

        name = parts[0].lower()
        arg = command[len(parts[0]):].strip()

        if name == "help":
            write("""ShellBridge v1.0.2 Commands & Features:
  shell internal / cmd / ps / python   Switch terminal execution mode
  serve [port]                         Start built-in HTTP server in current folder
  stopserve                            Stop active HTTP server
  hash FILENAME                        Compute MD5 & SHA-256 file checksums
  update                               Check GitHub for automatic updates
  touch FILENAME                       Create empty file or update timestamp
  rm FILENAME / rm -rf PATH            Delete files or directories securely
  nano FILENAME                        Open built-in text editor
  theme glass/light/dark/matrix        Change terminal color theme
  export FILENAME.txt                  Save session history to a file
  subst F: "C:\\Path"                  Map folder to a virtual drive letter
  curl URL                             Perform HTTP requests
  arp                                  Display network & IP info
  calc EXPR                            Calculate arithmetic securely
  start TARGET                         Open file, folder, or URL
  drives                               List available drives
  pyinfo                               Show Python runtime info
  exit                                 Close ShellBridge""")

        elif name == "serve":
            start_http_server(arg)

        elif name == "stopserve":
            stop_http_server()

        elif name == "hash":
            calculate_hashes(arg)

        elif name == "update":
            check_for_updates()

        elif name == "touch":
            touch_file(arg)

        elif name == "rm":
            remove_target(arg)

        elif name == "nano":
            open_nano(arg)

        elif name == "theme":
            apply_theme(arg.lower())

        elif name == "export":
            export_session(arg)

        elif name == "curl":
            run_curl(arg)

        elif name == "arp":
            pure_python_arp()

        elif name == "echo":
            write(arg.strip('"'))

        elif name == "clear":
            clear_output()

        elif name == "pwd":
            write(os.getcwd())

        elif name in ("ls", "dir"):
            for item in sorted(os.listdir()):
                write(item)

        elif name == "drives":
            if os.name == "nt":
                for letter in string.ascii_uppercase:
                    if os.path.isdir(letter + ":\\"):
                        write(letter + ":\\")
            else:
                write("Drive listing is available on Windows only.")

        elif name == "subst":
            try:
                args = shlex.split(arg)
                if not args:
                    subst_list()
                elif args[0].lower() == "/d":
                    if len(args) == 2:
                        subst_remove(args[1])
                    else:
                        write("Usage: subst /d F:")
                elif len(args) == 2:
                    subst_add(args[0], args[1])
                else:
                    write("Invalid syntax.")
            except Exception as error:
                write(f"Invalid arguments: {error}")

        elif name == "cd":
            if not arg:
                write(os.getcwd())
            else:
                target = os.path.abspath(os.path.expanduser(arg.strip('"')))
                if os.path.isdir(target):
                    os.chdir(target)
                    write(os.getcwd())
                else:
                    write(f"Directory not found: {target}")

        elif name == "pyinfo":
            write(f"Python: {sys.version}")
            write(f"Platform: {platform.platform()}")
            write(f"Executable: {sys.executable}")
            write(f"Folder: {os.getcwd()}")

        elif name == "calc":
            tree = ast.parse(arg, mode="eval")
            write(eval(compile(tree, '<string>', '<eval>')))

        elif name == "start":
            webbrowser.open(arg) if arg.startswith("http") else os.startfile(arg)

        elif name == "history":
            for idx, h in enumerate(command_history, 1):
                write(f"{idx}: {h}")

        elif name == "exit":
            stop_http_server()
            root.destroy()

        else:
            write(f"Unknown command: {name}. Type 'help' for available commands.")

    except Exception as error:
        write(f"Error: {error}")

    return "break"


# ---------------- History & Bindings ----------------

def navigate_history(event):
    global history_index
    if not command_history:
        return "break"
    if event.keysym == "Up":
        history_index = max(0, history_index - 1)
    elif event.keysym == "Down":
        history_index = min(len(command_history), history_index + 1)
    entry.delete(0, "end")
    if history_index < len(command_history):
        entry.insert(0, command_history[history_index])
    return "break"

entry.bind("<Return>", run_command)
entry.bind("<Up>", navigate_history)
entry.bind("<Down>", navigate_history)
entry.bind("<Tab>", handle_tab)

write("Welcome to ShellBridge [v1.0.2]")
write(f"NEW: HTTP Server, Hashes, and REPL!")
write(f"Python {platform.python_version()}  •  {platform.system()}")
write(f"Current folder: {os.getcwd()}")
write("")

entry.focus_set()
root.mainloop()
