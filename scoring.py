"""
scoring.py
----------
STAGE 3 of the pipeline: SCORE.

This is a PURE function. It takes a dictionary of features and returns
a number plus the reasons behind it. It never reads the disk, never
prints, never moves files. That purity is what makes it unit-testable:
test_scoring.py feeds it hand-made dictionaries and asserts the result.

Every weight here is a design choice you can and should tune. The
guiding rule: no single WEAK signal should convict a file. A conviction
should require either the strong content signal, or several weak ones
stacking up.
"""

# signal name -> (points, human-readable reason)
WEIGHTS = {
    "sentinel_match":      (6, "Contains the logger's unique sentinel string"),
    "mace_anomaly":        (3, "Creation/modification time mismatch (MACE)"),
    "hidden_or_system":    (2, "Hidden or system file"),
    "timestamp_anomaly":   (2, "Timestamp is future-dated or implausibly old"),
    "extension_mismatch":  (2, "File extension does not match its real content"),
    "suspicious_location": (1, "Lives in a temp/appdata-style location"),
    "obfuscated_filename": (1, "Machine-generated / obfuscated filename"),
    "high_entropy":        (1, "High entropy (possibly encoded or packed)"),
}

SCORE_CAP = 10

# entropy above this counts as "high". ~7.2 catches encrypted/packed
# data while leaving normal text (3-5) comfortably below the line.
HIGH_ENTROPY_THRESHOLD = 7.2


def score_file(features):
    """
    Turn a feature dict into (score, reasons, threat_level).

    score:        integer 0-10 (capped)
    reasons:      list of strings explaining each point awarded
    threat_level: "HIGH" (7-10), "MEDIUM" (4-6), "LOW" (1-3), "NONE" (0)
    """
    # Derive the two "combined" signals the raw features don't store directly.
    timestamp_anomaly = bool(features.get("timestamp_future")
                             or features.get("timestamp_very_old"))
    high_entropy = features.get("entropy", 0.0) >= HIGH_ENTROPY_THRESHOLD

    # Map every scorable condition to a boolean in one place.
    active = {
        "sentinel_match":      bool(features.get("sentinel_match")),
        "mace_anomaly":        bool(features.get("mace_anomaly")),
        "hidden_or_system":    bool(features.get("hidden_or_system")),
        "timestamp_anomaly":   timestamp_anomaly,
        "extension_mismatch":  bool(features.get("extension_mismatch")),
        "suspicious_location": bool(features.get("suspicious_location")),
        "obfuscated_filename": bool(features.get("obfuscated_filename")),
        "high_entropy":        high_entropy,
    }

    score = 0
    reasons = []
    for signal, is_on in active.items():
        if is_on:
            points, reason = WEIGHTS[signal]
            score += points
            reasons.append(f"(+{points}) {reason}")

    score = min(score, SCORE_CAP)
    return score, reasons, threat_level(score)


def threat_level(score):
    """Bucket a numeric score into a human label."""
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    if score >= 1:
        return "LOW"
    return "NONE"
