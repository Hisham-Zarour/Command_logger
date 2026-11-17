"""
features.py
-----------
STAGE 2 of the pipeline: COLLECT FEATURES.

This module does exactly one thing: look at a single file and gather
raw facts about it. It makes NO judgement about whether the file is
suspicious. That is the scorer's job (scoring.py).

Keeping "collect facts" and "decide meaning" separate is the whole
point of the redesign: it means scoring.py is a pure function we can
unit-test with fake dictionaries, without ever touching a real disk.
"""

import os
import re
import math
import hashlib
import time

# How many bytes to read when hashing / measuring entropy.
# We cap it so a huge file doesn't freeze the scan. 1 MB is plenty
# to characterise a text log.
READ_CAP_BYTES = 1024 * 1024  # 1 MB

# Locations we treat as "suspicious to hide data in".
SUSPICIOUS_PATH_HINTS = ("temp", "tmp", "appdata", "cache")


# ---------- individual feature collectors ----------

def sha256_of(filepath):
    """
    Return the SHA-256 hash of the file's contents, or None on failure.

    WHY: a hash is a fingerprint. It lets a forensic report PROVE
    exactly which bytes were found, and lets you confirm a quarantined
    file wasn't altered afterward. Real IR tooling always records this.
    """
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # read in chunks so we never load a giant file fully into RAM
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def shannon_entropy(filepath):
    """
    Return Shannon entropy (0.0 - 8.0) of the first READ_CAP_BYTES bytes.

    WHY: entropy measures randomness per byte. Plain text (your logger
    output) sits low, roughly 3-5. Encrypted or packed data pushes
    toward 8.0. It is only a WEAK signal, because zip/jpg files are
    legitimately high-entropy too — so it hints "encoded", never "bad".
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read(READ_CAP_BYTES)
    except OSError:
        return 0.0

    if not data:
        return 0.0

    # count how often each byte value (0-255) appears
    counts = [0] * 256
    for b in data:
        counts[b] += 1

    length = len(data)
    entropy = 0.0
    for c in counts:
        if c:
            p = c / length
            entropy -= p * math.log2(p)
    return entropy


def is_hidden_or_system(filepath):
    """
    True if the file carries the Windows HIDDEN or SYSTEM attribute.

    WHY the os.name guard: ctypes.windll only exists on Windows.
    On Linux/macOS, ctypes has no 'windll' at all, so touching it
    raises AttributeError. We check the platform FIRST and bail out
    cleanly, instead of relying on a bare except to swallow the crash.
    (On Unix we return False here; a dot-file check lives separately.)
    """
    if os.name != "nt":
        return False
    try:
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
        if attrs == -1:
            return False
        FILE_ATTRIBUTE_HIDDEN = 0x2
        FILE_ATTRIBUTE_SYSTEM = 0x4
        return bool(attrs & FILE_ATTRIBUTE_HIDDEN or attrs & FILE_ATTRIBUTE_SYSTEM)
    except (OSError, AttributeError):
        return False


def is_unix_dotfile(filepath):
    """True if the file is a Unix hidden file (name starts with '.')."""
    name = os.path.basename(filepath)
    return name.startswith(".") and name not in (".", "..")


def timestamp_facts(filepath):
    """
    Return (mtime_age_days, mace_anomaly, future_dated).

    - mtime_age_days: how old the file claims to be (modified time).
    - future_dated:   mtime is in the future — impossible normally,
                      a strong sign of clumsy timestamp spoofing.
    - mace_anomaly:   mtime is significantly EARLIER than ctime, i.e.
                      the file was created on this system just now but
                      claims it was last modified long ago. Spoofers
                      fake the modified time and forget the creation
                      time, so this mismatch is a loud red flag.

    NOTE (portability): os.path.getctime means true creation time on
    Windows/macOS, but 'inode change time' on Linux. The check still
    has value on Linux but the semantics differ — worth knowing.
    """
    now = time.time()
    try:
        mtime = os.path.getmtime(filepath)
        ctime = os.path.getctime(filepath)
    except OSError:
        return 0.0, False, False

    mtime_age_days = (now - mtime) / 86400.0
    future_dated = mtime > now + 60  # allow 60s of clock slack

    # mtime more than 1 day before ctime => claims to predate its own creation
    mace_anomaly = (ctime - mtime) > 86400

    return mtime_age_days, mace_anomaly, future_dated


# filename "style" patterns, used as a weak obfuscation signal
_GUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_LONG_HEX_RE = re.compile(r"^[0-9a-fA-F]{16,}$")


def looks_obfuscated(filepath):
    """
    True if the filename looks machine-generated (GUID / long hex).

    WHY weak: plenty of legitimate cache files use GUID names too.
    So this only nudges the score — it never convicts on its own.
    """
    stem = os.path.splitext(os.path.basename(filepath))[0]
    if _GUID_RE.search(stem):
        return True
    if _LONG_HEX_RE.match(stem):
        return True
    return False


# minimal magic-byte signatures: extension -> expected header bytes
_MAGIC = {
    ".png": b"\x89PNG",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".gif": b"GIF8",
    ".pdf": b"%PDF",
    ".zip": b"PK\x03\x04",
}


def extension_mismatch(filepath):
    """
    True if the extension promises a binary type but the header doesn't match.

    WHY: a '.jpg' that is really a text log is a classic disguise.
    This is a lightweight header check (no external dependency); a real
    tool would use libmagic, but the idea is identical.
    """
    ext = os.path.splitext(filepath)[1].lower()
    expected = _MAGIC.get(ext)
    if not expected:
        return False  # we only check types we have a signature for
    try:
        with open(filepath, "rb") as f:
            head = f.read(len(expected))
        return head != expected
    except OSError:
        return False


def in_suspicious_location(filepath):
    """True if the file lives under a temp/appdata/cache-style path."""
    low = filepath.lower()
    return any(hint in low for hint in SUSPICIOUS_PATH_HINTS)


def contains_sentinel(filepath, sentinel):
    """
    True if the file contains the distinctive sentinel string.

    WHY a sentinel and not a plain word: searching for "STOP" or "test"
    matches countless legitimate files. A long, unique marker that only
    your logger writes makes a content hit almost unforgeable — so it
    earns the highest weight in the scorer.
    """
    if not sentinel:
        return False
    needle = sentinel.lower().encode("utf-8", errors="ignore")
    try:
        with open(filepath, "rb") as f:
            data = f.read(READ_CAP_BYTES).lower()
        return needle in data
    except OSError:
        return False


# ---------- the one function the pipeline calls ----------

def collect_features(filepath, sentinel=None):
    """
    Gather every raw fact about one file into a plain dict.

    Returns None if the path isn't a readable regular file.
    The returned dict is the ONLY thing the scorer ever sees.
    """
    try:
        if not os.path.isfile(filepath):
            return None
        size = os.path.getsize(filepath)
    except OSError:
        return None

    mtime_age_days, mace_anomaly, future_dated = timestamp_facts(filepath)

    return {
        "path": filepath,
        "filename": os.path.basename(filepath),
        "size": size,
        "sha256": sha256_of(filepath),
        "entropy": shannon_entropy(filepath),
        "hidden_or_system": is_hidden_or_system(filepath) or is_unix_dotfile(filepath),
        "mtime_age_days": mtime_age_days,
        "timestamp_future": future_dated,
        "timestamp_very_old": mtime_age_days > 365,
        "mace_anomaly": mace_anomaly,
        "extension_mismatch": extension_mismatch(filepath),
        "suspicious_location": in_suspicious_location(filepath),
        "obfuscated_filename": looks_obfuscated(filepath),
        "sentinel_match": contains_sentinel(filepath, sentinel),
    }
