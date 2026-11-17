"""
detector.py
-----------
STAGES 1 and 4: ENUMERATE and REPORT/ACT (the orchestrator).

This is the only file with side effects: it walks the disk, calls the
feature collector, calls the pure scorer, prints findings, and offers
quarantine with a forensic report. All the "thinking" lives in
features.py and scoring.py; this file just wires them together.

Run:  python detector.py
"""

import os
import shutil
from datetime import datetime

import features as feat
import scoring

# The detector's own files contain the sentinel (in code/rules), so we must
# never flag ourselves. Build a set of our own absolute paths to skip.
# WHY: a scanner that detects its own source is the textbook self-reference
# false positive. Excluding known-good paths is also how real AV handles its
# own binaries and signature files.
_SELF_FILES = {
    os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), name)))
    for name in ("detector.py", "features.py", "scoring.py",
                 "rules.yar", "test_scoring.py")
}

# YARA is optional. If yara-python isn't installed we degrade gracefully
# and rely on the Python sentinel check instead of crashing.
try:
    import yara  # type: ignore
    _YARA_AVAILABLE = True
except ImportError:
    _YARA_AVAILABLE = False


# Where to look. Built per-OS so we don't hand Windows paths to Linux.
def default_locations():
    locs = [".", os.path.join(".", "logs")]
    if os.name == "nt":
        locs += [
            os.path.expandvars(r"%TEMP%"),
            os.path.expandvars(r"%APPDATA%"),
            os.path.expanduser(r"~\AppData\Local\Temp"),
        ]
    else:
        locs += ["/tmp", os.path.expanduser("~/.cache")]
    # keep only ones that actually exist, drop duplicates, preserve order
    seen, out = set(), []
    for l in locs:
        n = os.path.normpath(os.path.abspath(l))
        if n not in seen and os.path.isdir(n):
            seen.add(n)
            out.append(l)
    return out


QUARANTINE_BASE = os.path.join(os.path.expanduser("~"), "Desktop")


# ---------- STAGE 1: ENUMERATE ----------

def enumerate_files(locations):
    """Yield every regular file path in the given locations (non-recursive)."""
    seen = set()
    for location in locations:
        try:
            for name in os.listdir(location):
                path = os.path.join(location, name)
                norm = os.path.normpath(os.path.abspath(path))
                if norm in seen:
                    continue
                seen.add(norm)
                if norm in _SELF_FILES:
                    continue  # never scan our own program files
                if os.path.isfile(path):
                    yield path
        except OSError as e:
            # report, don't hide — a bare 'except: pass' would mask bugs
            print(f"   [skip] could not read {location}: {e}")


# ---------- optional YARA matching ----------

def load_yara(rules_path="rules.yar"):
    if not _YARA_AVAILABLE or not os.path.isfile(rules_path):
        return None
    try:
        return yara.compile(filepath=rules_path)
    except yara.Error as e:
        print(f"   [yara] rule compile failed, continuing without it: {e}")
        return None


def yara_hit(compiled_rules, filepath):
    if compiled_rules is None:
        return False
    try:
        return bool(compiled_rules.match(filepath))
    except yara.Error:
        return False


# ---------- STAGE 4a: SCAN + SCORE ----------

def scan(locations, sentinel, min_score=4):
    """Return a list of findings (feature dict + score info) at/above min_score."""
    rules = load_yara()
    findings = []

    for path in enumerate_files(locations):
        features = feat.collect_features(path, sentinel=sentinel)
        if features is None:
            continue

        # Let a YARA hit count as a sentinel match too (high-weight signal).
        if yara_hit(rules, path):
            features["sentinel_match"] = True

        score, reasons, level = scoring.score_file(features)
        if score >= min_score:
            features["score"] = score
            features["reasons"] = reasons
            features["threat_level"] = level
            findings.append(features)

    # strongest first
    findings.sort(key=lambda f: f["score"], reverse=True)
    return findings


# ---------- STAGE 4b: REPORT ----------

def print_findings(findings):
    bar = "=" * 70
    print("\n" + bar)
    print(f" SCAN COMPLETE — {len(findings)} file(s) above threshold")
    print(bar)
    for i, f in enumerate(findings, 1):
        print(f"\n[{i}] {f['filename']}  "
              f"— score {f['score']}/10  ({f['threat_level']})")
        print(f"    path:   {f['path']}")
        print(f"    size:   {f['size']:,} bytes")
        print(f"    sha256: {f['sha256']}")
        for r in f["reasons"]:
            print(f"    {r}")


def write_report(folder, moved):
    path = os.path.join(folder, "DETECTION_REPORT.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("CONTENT DETECTION REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Scan time: {datetime.now()}\n")
        f.write(f"Files quarantined: {len(moved)}\n\n")
        for i, m in enumerate(moved, 1):
            info = m["info"]
            f.write(f"{i}. {info['filename']}\n")
            f.write(f"   original : {info['path']}\n")
            f.write(f"   sha256   : {info['sha256']}\n")
            f.write(f"   score    : {info['score']}/10 ({info['threat_level']})\n")
            f.write(f"   size     : {info['size']:,} bytes\n")
            f.write("   indicators:\n")
            for r in info["reasons"]:
                f.write(f"     - {r}\n")
            f.write("\n")
    print(f"\n Report written: {path}")


# ---------- STAGE 4c: QUARANTINE ----------

def quarantine(findings):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(QUARANTINE_BASE, f"Quarantine_{stamp}")
    os.makedirs(folder, exist_ok=True)

    moved = []
    for f in findings:
        src = f["path"]
        try:
            safe = "CONFIRMED_" + "".join(
                c for c in f["filename"] if c.isalnum() or c in "._- "
            )
            dst = os.path.join(folder, safe)
            shutil.move(src, dst)
            moved.append({"original": src, "quarantined": dst, "info": f})
            print(f"   moved: {f['filename']}")
        except (OSError, shutil.Error) as e:
            print(f"   FAILED: {f['filename']} — {e}")

    write_report(folder, moved)
    return folder, moved


# ---------- entry point ----------

def main():
    print("=" * 70)
    print(" LOGGER-OUTPUT DETECTOR  (defensive / educational)")
    print("=" * 70)
    print(f" YARA engine: {'available' if _YARA_AVAILABLE else 'NOT installed (using Python fallback)'}")

    sentinel = input("\n Sentinel string your logger writes "
                     "(press Enter to use rule default): ").strip()
    if not sentinel:
        sentinel = "===SESSION_END_7f3a9c==="

    locations = default_locations()
    print(f"\n Scanning {len(locations)} location(s):")
    for l in locations:
        print(f"   - {l}")

    findings = scan(locations, sentinel)
    if not findings:
        print("\n No files scored above the threshold. Clean.")
        return

    print_findings(findings)

    answer = input("\n Quarantine these files? (yes/no): ").strip().lower()
    if answer in ("yes", "y"):
        folder, moved = quarantine(findings)
        print(f"\n Done — {len(moved)} file(s) secured in {folder}")
    else:
        print(" Quarantine cancelled. Nothing moved.")


if __name__ == "__main__":
    main()
