import os
import time
import shutil
from datetime import datetime

# ========== CONFIGURATION ==========
QUARANTINE_BASE = os.path.join(os.path.expanduser("~"), "Desktop")

# ========== HELPER FUNCTIONS ==========
def normalize_path(path):
    """Convert path to consistent format for comparison"""
    try:
        # Convert to absolute path and normalize separators
        abs_path = os.path.abspath(path)
        norm_path = os.path.normpath(abs_path)
        # Windows: case-insensitive, Unix: case-sensitive
        if os.name == 'nt':
            return norm_path.lower()
        return norm_path
    except:
        return path

# ========== DETECTION ==========
def detect_keylogger_files():
    """Scan for files that might be from a keylogger"""
    
    # Define locations (normalized to avoid overlaps)
    raw_locations = [
        ".", 
        "./logs/",
        os.path.expandvars("%TEMP%"),
        os.path.expandvars("%APPDATA%\\Microsoft\\"),
        os.path.expanduser("~/AppData/Local/Temp/")
    ]
    
    # Normalize and deduplicate locations
    locations_to_check = []
    seen_locations = set()
    
    for loc in raw_locations:
        norm_loc = normalize_path(loc)
        if norm_loc not in seen_locations:
            seen_locations.add(norm_loc)
            locations_to_check.append(loc)
    
    suspicious_patterns = ["log.txt", "system_log.txt", "tmp_log.txt", "keyboard.log"]
    
    print("🔍 Starting detection scan...")
    
    found_files = []
    seen_files = set()  # Track files we've already found
    
    for location in locations_to_check:
        if os.path.exists(location):
            print(f"\nChecking: {location}")
            
            try:
                # Get actual files in directory
                for filename in os.listdir(location):
                    filepath = os.path.join(location, filename)
                    norm_path = normalize_path(filepath)
                    
                    # Skip if we've already seen this file
                    if norm_path in seen_files:
                        continue
                    
                    # Check if it matches suspicious patterns
                    for pattern in suspicious_patterns:
                        if pattern in filename.lower():
                            # Verify it's actually a file and exists
                            if os.path.isfile(filepath):
                                # Get file info
                                size = os.path.getsize(filepath)
                                modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                                
                                print(f"⚠️  SUSPICIOUS: {filename}")
                                print(f"   Size: {size} bytes | Modified: {modified}")
                                
                                # Add to found files
                                found_files.append({
                                    'path': filepath,
                                    'norm_path': norm_path,  # For duplicate checking
                                    'name': filename,
                                    'size': size,
                                    'modified': modified,
                                    'found_in': location
                                })
                                
                                seen_files.add(norm_path)
                                break  # No need to check other patterns for this file
                            
            except PermissionError:
                print(f"   ⚠️  Permission denied: {location}")
            except FileNotFoundError:
                print(f"   ⚠️  Directory changed during scan: {location}")
            except Exception as e:
                print(f"   ⚠️  Could not scan: {e}")
        else:
            print(f"\nSkipping (doesn't exist): {location}")
    
    # Debug: Show what we found
    print(f"\n📊 Found {len(found_files)} unique suspicious files")
    return found_files

# ========== QUARANTINE ==========
def quarantine_detected_files(found_files, quarantine_location=None):
    """Move suspicious files to quarantine"""
    
    # Use provided location or default
    if quarantine_location:
        quarantine_base = quarantine_location
    else:
        quarantine_base = QUARANTINE_BASE
    
    # Create quarantine folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine_folder = os.path.join(quarantine_base, f"Quarantine_{timestamp}")
    os.makedirs(quarantine_folder, exist_ok=True)
    
    moved_files = []
    failed_files = []
    
    print(f"\n📁 Quarantine folder: {quarantine_folder}")
    
    for file_info in found_files:
        filepath = file_info['path']
        filename = file_info['name']
        
        try:
            # Double-check file exists before trying to move
            if os.path.exists(filepath):
                # Create safe filename
                original_folder = os.path.basename(os.path.dirname(filepath))
                if original_folder == ".":
                    original_folder = "current"
                
                # Replace problematic characters
                safe_name = filename
                for char in [':', '\\', '/', '*', '?', '"', '<', '>', '|']:
                    safe_name = safe_name.replace(char, '_')
                
                destination = os.path.join(quarantine_folder, f"{original_folder}_{safe_name}")
                
                # Move the file
                shutil.move(filepath, destination)
                moved_files.append({
                    'original': filepath,
                    'quarantined': destination,
                    'info': file_info
                })
                
                print(f"✅ Quarantined: {filename}")
            else:
                print(f"❌ File no longer exists: {filename}")
                failed_files.append(file_info)
                
        except PermissionError:
            print(f"❌ Permission denied: {filename} (may be in use)")
            failed_files.append(file_info)
        except FileNotFoundError:
            print(f"❌ File not found: {filename} (may have been deleted)")
            failed_files.append(file_info)
        except Exception as e:
            print(f"❌ Failed to quarantine {filename}: {e}")
            failed_files.append(file_info)
    
    # Create detailed report
    create_quarantine_report(quarantine_folder, moved_files, failed_files)
    
    return moved_files, failed_files, quarantine_folder

# ========== REPORTING ==========
def create_quarantine_report(quarantine_folder, moved_files, failed_files):
    """Create detailed report of quarantine operation"""
    
    report_file = os.path.join(quarantine_folder, "QUARANTINE_REPORT.txt")
    
    with open(report_file, "w") as f:
        f.write("="*60 + "\n")
        f.write("           MALWARE QUARANTINE REPORT\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Quarantine Time: {datetime.now()}\n")
        f.write(f"Quarantine Location: {quarantine_folder}\n")
        f.write(f"Files Successfully Quarantined: {len(moved_files)}\n")
        f.write(f"Files Failed to Quarantine: {len(failed_files)}\n")
        f.write("-"*60 + "\n\n")
        
        # Successful quarantines
        if moved_files:
            f.write("SUCCESSFULLY QUARANTINED FILES:\n")
            f.write("-"*40 + "\n")
            for i, item in enumerate(moved_files, 1):
                info = item['info']
                f.write(f"\n{i}. {info['name']}\n")
                f.write(f"   Original Path: {item['original']}\n")
                f.write(f"   Quarantined At: {item['quarantined']}\n")
                f.write(f"   Found In: {info['found_in']}\n")
                f.write(f"   File Size: {info['size']:,} bytes\n")
                f.write(f"   Last Modified: {info['modified']}\n")
        
        # Failed quarantines
        if failed_files:
            f.write("\n\nFAILED TO QUARANTINE:\n")
            f.write("-"*40 + "\n")
            for i, info in enumerate(failed_files, 1):
                f.write(f"\n{i}. {info['name']}\n")
                f.write(f"   Path: {info['path']}\n")
                f.write(f"   Reason: File may be in use, protected, or deleted\n")
    
    print(f"📄 Detailed report: {report_file}")

# ========== MAIN PROGRAM ==========
def main():
    """Main detection and quarantine program"""
    
    print("🛡️  Keylogger Detection & Quarantine Tool")
    print("="*50)
    
    # Step 1: Detect files
    found_files = detect_keylogger_files()
    
    if not found_files:
        print("\n✅ No suspicious files found.")
        return
    
    # Step 2: Show what was found
    print(f"\n{'='*50}")
    print(f"📊 DETECTION RESULTS:")
    print(f"   Found {len(found_files)} unique suspicious files")
    
    for i, file_info in enumerate(found_files, 1):
        print(f"\n{i}. {file_info['name']}")
        print(f"   Location: {file_info['path']}")
        print(f"   Size: {file_info['size']:,} bytes")
    
    # Step 3: Ask for quarantine
    print(f"\n{'='*50}")
    print("Quarantine will move files to:")
    print(f"  {QUARANTINE_BASE}\\Quarantine_YYYYMMDD_HHMMSS")
    
    response = input("\nQuarantine these files? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("Quarantine cancelled.")
        return
    
    # Step 4: Optional custom location
    custom = input(f"Use default location ({QUARANTINE_BASE})? (yes/no): ").lower()
    quarantine_location = None
    
    if custom in ['no', 'n']:
        new_location = input("Enter quarantine folder path: ").strip()
        if os.path.isdir(os.path.dirname(new_location)):
            quarantine_location = new_location
        else:
            print("Invalid path. Using default.")
    
    # Step 5: Perform quarantine
    print(f"\n{'='*50}")
    print("🚨 QUARANTINING FILES...")
    
    moved, failed, quarantine_folder = quarantine_detected_files(
        found_files, quarantine_location
    )
    
    # Step 6: Results
    print(f"\n{'='*50}")
    print("📋 QUARANTINE COMPLETE")
    print(f"✅ Successfully quarantined: {len(moved)} files")
    if failed:
        print(f"❌ Failed to quarantine: {len(failed)} files")
    print(f"📁 Quarantine folder: {quarantine_folder}")
    
    # Show where files went
    if moved:
        print("\n📦 Quarantined files location:")
        for item in moved:
            print(f"  • {item['info']['name']}")
            print(f"    → {item['quarantined']}")

# ========== RUN PROGRAM ==========
if __name__ == "__main__":
    main()