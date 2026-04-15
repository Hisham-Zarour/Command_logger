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
        print("⚠️  Note: pywin32 not installed. Install with: pip install pywin32")
        print("   Windows stealth features will be limited.\n")
else:
    print(f"✅ Running on {platform.system()} - Using native stealth methods\n")

# ========== RANDOM FILENAME GENERATORS ==========

def random_string(length=8):
    """Generate random alphanumeric string"""
    letters_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters_digits) for _ in range(length))

def random_hex_string(length=8):
    """Generate random hex string (looks like hash)"""
    hex_chars = string.hexdigits.lower()
    return ''.join(random.choice(hex_chars) for _ in range(length))

def random_guid_style():
    """Generate GUID/UUID style filename"""
    sections = [8, 4, 4, 4, 12]
    parts = []
    for section in sections:
        parts.append(''.join(random.choice(string.hexdigits.lower()) for _ in range(section)))
    return '{' + '-'.join(parts) + '}'

def random_legitimate_name():
    """Generate filename that looks like legitimate software file"""
    
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
    else:
        return f"{prefix}{suffix}"

def random_system_mimic():
    """Generate filename that mimics system files"""
    
    if IS_WINDOWS:
        system_patterns = [
            f"win{random.randint(10, 32)}.log",
            f"event{random.randint(100, 999)}.evtx",
            f"app{random.hexdigits.lower()[:4]}.dat",
            f"ms{random.randint(1, 9)}0{random.randint(1, 9)}.tmp",
            f"~${random_string(4)}.tmp",
            f".{random_string(6)}.cache"
        ]
    else:  # Linux/Mac
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
    """
    Get random filename in various styles
    
    Styles:
        - "random": Simple random string (a1b2c3d4.txt)
        - "hex": Hex characters (f3a8c2b1.txt)  
        - "guid": GUID format ({a1b2c3d4-...}.txt)
        - "legit": Looks like legitimate software (chrome_cache.log)
        - "system": Mimics system files
        - "timestamp": Uses timestamp + random (20260122_143022_a1b2.txt)
    """
    
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
        if '.' in name:
            return name
        return name + ext
    elif style == "system":
        name = random_system_mimic()
        if '.' in name:
            return name
        return name + ext
    elif style == "timestamp":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_part = random_string(4)
        name = f"{timestamp}_{random_part}"
    else:
        name = random_string(8)
    
    return name + ext

# ========== CROSS-PLATFORM STEALTH FUNCTIONS ==========

def hide_file_windows(filepath):
    """Hide file using Windows attributes (Hidden + System)"""
    if not HAS_WIN32:
        return False
    
    try:
        attrs = win32api.GetFileAttributes(filepath)
        win32api.SetFileAttributes(filepath, 
            attrs | win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        return True
    except Exception as e:
        print(f"      ⚠️  Could not hide: {e}")
        return False

def hide_file_unix(filepath):
    """Hide file on Linux/Unix by renaming to dot-file"""
    try:
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        if not basename.startswith('.'):
            new_path = os.path.join(dirname, '.' + basename)
            os.rename(filepath, new_path)
            return True
        return True  # Already hidden
    except Exception as e:
        print(f"      ⚠️  Could not hide: {e}")
        return False

def hide_file_mac(filepath):
    """Hide file on macOS using chflags"""
    try:
        subprocess.run(['chflags', 'hidden', filepath], capture_output=True, check=False)
        return True
    except:
        # Fallback to dot-file method
        return hide_file_unix(filepath)

def hide_file(filepath):
    """Cross-platform file hiding"""
    if IS_WINDOWS and HAS_WIN32:
        return hide_file_windows(filepath)
    elif IS_WINDOWS and not HAS_WIN32:
        # Try attrib command as fallback
        try:
            subprocess.run(['attrib', '+h', '+s', filepath], shell=True, capture_output=True)
            return True
        except:
            return False
    elif IS_MAC:
        return hide_file_mac(filepath)
    elif IS_LINUX:
        return hide_file_unix(filepath)
    return False

def unhide_file_windows(filepath):
    """Remove hidden/system attributes from file (Windows)"""
    if not HAS_WIN32:
        try:
            subprocess.run(['attrib', '-h', '-s', filepath], shell=True, capture_output=True)
            return True
        except:
            return False
    
    try:
        attrs = win32api.GetFileAttributes(filepath)
        win32api.SetFileAttributes(filepath, attrs & ~(2 | 4))
        return True
    except:
        return False

def unhide_file_unix(filepath):
    """Unhide file on Unix by removing dot prefix"""
    try:
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        if basename.startswith('.'):
            new_path = os.path.join(dirname, basename[1:])
            os.rename(filepath, new_path)
            return True
        return True
    except:
        return False

def unhide_file(filepath):
    """Cross-platform unhide"""
    if IS_WINDOWS:
        return unhide_file_windows(filepath)
    else:
        return unhide_file_unix(filepath)

def spoof_timestamp(filepath):
    """Make file appear older (30-180 days old) - works on all platforms"""
    try:
        days_old = random.randint(30, 180)
        old_time = time.time() - (days_old * 86400)
        os.utime(filepath, (old_time, old_time))
        return days_old
    except Exception as e:
        print(f"      ⚠️  Could not spoof timestamp: {e}")
        return None

def make_file_stealthy(filepath):
    """Apply all stealth techniques to a file"""
    print(f"    🕵️  Applying stealth:")
    
    # 1. Hide file (platform-specific)
    if hide_file(filepath):
        if IS_WINDOWS:
            print(f"      ✓ Hidden + System attributes applied")
        elif IS_MAC:
            print(f"      ✓ Hidden flag + dot-file applied")
        else:
            print(f"      ✓ Hidden (dot-file) applied")
    else:
        print(f"      ⚠️  Could not hide file")
    
    # 2. Spoof timestamp (works on all platforms)
    days = spoof_timestamp(filepath)
    if days:
        print(f"      ✓ Timestamp spoofed: {days} days old")
    
    print(f"    ✅ Stealth complete")

# ========== LOCATION GENERATION ==========

def get_stealth_locations():
    """
    Generate stealthy save locations with random filenames
    Each location gets a different style of random name
    """
    
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
        
        if style == "legit":
            filename = get_random_filename(style)
            if not os.path.dirname(filename):
                full_path = os.path.join(base, filename)
            else:
                full_path = filename
        else:
            filename = get_random_filename(style)
            full_path = os.path.join(base, filename)
        
        stealth_locations.append({
            'path': full_path,
            'style': style,
            'base': base,
            'filename': os.path.basename(full_path)
        })
    
    return stealth_locations

# ========== MAIN LOGGER ==========

def main():
    print("="*70)
    print("🔐 ENHANCED STEALTH COMMAND LOGGER (Cross-Platform)")
    print("="*70)
    print("⚠️  EDUCATIONAL PURPOSE ONLY - Test on your own systems")
    print("="*70)
    print(f"🖥️  Platform: {platform.system()}")
    print("\n📝 Type your input. Type 'STOP' to end session.")
    print("\n🕵️  STEALTH FEATURES:")
    print("   • Random filenames (6 different styles)")
    print("   • Different style per location")
    if IS_WINDOWS:
        print("   • Hidden + System file attributes")
    elif IS_MAC:
        print("   • Hidden flags + dot-file naming")
    else:
        print("   • Hidden dot-file naming")
    print("   • Spoofed timestamps (30-180 days old)")
    print("   • Multiple persistence locations")
    print("="*70)
    
    saved_words = []
    
    while True:
        user_input = input()
        
        if user_input == "STOP":
            print("\n💾 Saving data with stealth techniques...")
            print("-"*70)
            
            stealth_locations = get_stealth_locations()
            success_count = 0
            failed_locations = []
            
            for i, location_info in enumerate(stealth_locations, 1):
                location = location_info['path']
                style = location_info['style']
                filename = location_info['filename']
                folder = os.path.dirname(location)
                
                print(f"\n[{i}/{len(stealth_locations)}] Processing...")
                print(f"    Filename: {filename}")
                print(f"    Style: {style}")
                print(f"    Folder: {folder or '.'}")
                
                try:
                    # Create folder if needed
                    if folder:
                        os.makedirs(folder, exist_ok=True)
                    
                    # Save the file
                    with open(location, "w", encoding='utf-8') as f:
                        for item in saved_words:
                            f.write(item + "\n")
                    
                    print(f"    ✓ File saved")
                    
                    # Apply stealth
                    make_file_stealthy(location)
                    success_count += 1
                    
                except PermissionError:
                    print(f"    ✗ FAILED: Permission denied")
                    failed_locations.append(location_info['base'])
                except Exception as e:
                    print(f"    ✗ FAILED: {type(e).__name__}: {e}")
                    failed_locations.append(location_info['base'])
            
            # Summary
            print("\n" + "="*70)
            print("📊 SESSION SUMMARY")
            print("="*70)
            print(f"    Words captured: {len(saved_words)}")
            print(f"    Files saved: {success_count}/{len(stealth_locations)}")
            if saved_words:
                print(f"    Preview: {', '.join(saved_words[:3])}{'...' if len(saved_words)>3 else ''}")
            if failed_locations:
                print(f"    Failed locations: {len(failed_locations)}")
            print("="*70)
            
            if IS_WINDOWS:
                print("\n🔍 To find these files, enable 'Show hidden files' in File Explorer")
            else:
                print("\n🔍 To find these files, use 'ls -la' to show hidden files")
            break
            
        else:
            saved_words.append(user_input)
            print(f"  [+] Captured: {user_input[:50]}{'...' if len(user_input)>50 else ''}")

# ========== RUN ==========
if __name__ == "__main__":
    main()
