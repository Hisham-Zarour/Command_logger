# Incident Report — Detection of Training Command-Logger

**Report ID:** IR-2026-001
**Classification:** Internal / Educational
**Author:** Hisham Zarour
**Date:** 2026-11-17
**Status:** Closed — threat contained
**Related project:** Detection Engineering Lab (`command_logger` → `detector`)

---

## 1. Executive Summary

A console input-logger ("command_logger"), built in-house as a red-team
training artifact, was deployed into a controlled test host. Its purpose
is to capture input typed into its own console and persist that capture to
disk using the same stealth techniques real malware uses: hidden/system
file attributes, timestamp backdating, disguised filenames, and writes to
multiple fallback locations.

A custom detection tool (`detector.py`) was run against the host to
determine whether these evasion techniques could be caught. **The detector
identified both planted logger-output files at HIGH confidence (scores 10/10
and 7/10), while correctly ignoring benign decoy files**, including the
classic false-positive trap of a file merely containing the word "STOP".

No true positives were missed and no benign file was misclassified as HIGH.
The incident is considered contained. This report documents the detection
methodology, the evidence, the MITRE ATT&CK techniques observed, and the
YARA + Sigma detection content produced to catch these techniques in a real
environment.

---

## 2. Scope & Environment

| Item | Value |
|------|-------|
| Host role | Isolated test / lab host |
| Threat artifact | `command_logger` (console input recorder, educational) |
| Detection tool | `detector.py` v2 (feature/score pipeline) |
| Detection content | `rules.yar` (YARA), `sigma/*.yml` (4 Sigma rules) |
| Scan locations | current dir, `./logs`, `/tmp`, user cache/temp |
| Sentinel marker | `===SESSION_END_7f3a9c===` |

---

## 3. Timeline (Detection Run)

All times host-local, 2026-11-17.

| Time | Event |
|------|-------|
| 11:37 | Test scene staged: 2 logger-output files + 2 benign decoys planted in `./logs` |
| 11:37 | One logger file (`thumb_cache.jpg`) backdated ~120 days to simulate timestomping |
| 11:37 | `detector.py` executed against 4 locations |
| 11:37 | Scan complete — 3 files scored above threshold, 2 confirmed as logger output |
| 11:37 | Quarantine offered; declined for evidence preservation (no files moved) |

---

## 4. Detection Methodology

The detector uses a four-stage pipeline with a deliberate separation
between **collecting facts** and **judging them**:

1. **Enumerate** — walk target locations, skipping the detector's own files.
2. **Collect features** — per file, gather raw facts: SHA-256 hash, Shannon
   entropy, timestamps (mtime age, MACE anomaly, future-dating), hidden/
   system attributes, extension-vs-content mismatch, filename style, path
   location, and presence of the unique sentinel string.
3. **Score** — a pure, unit-tested function applies weighted signals and
   produces a 0–10 confidence score and a threat level.
4. **Report / Act** — rank findings, print indicators, optionally quarantine
   with a SHA-256-backed forensic report.

### Scoring weights

| Signal | Weight | Rationale |
|--------|-------:|-----------|
| Unique sentinel string match | +6 | Near-unforgeable content proof |
| MACE anomaly (ctime vs mtime) | +3 | Backdating that forgot creation time |
| Hidden / system attribute | +2 | Active concealment |
| Timestamp anomaly (future / very old) | +2 | Clumsy timestomping |
| Extension / content mismatch | +2 | Disguise (text posing as `.jpg`) |
| Suspicious location (temp/appdata) | +1 | Weak corroborating signal |
| Obfuscated filename (GUID/hex) | +1 | Weak corroborating signal |
| High entropy | +1 | Possible encoding/packing |

**Design principle:** no single weak signal (+1) can convict a file. A HIGH
rating requires the strong content signal, or several independent signals
stacking.

---

## 5. Findings & Evidence

### Finding 1 — `thumb_cache.jpg` — CONFIRMED (10/10, HIGH)

| Field | Value |
|-------|-------|
| Path | `./logs/thumb_cache.jpg` |
| Size | 59 bytes |
| SHA-256 | `a90c4d59b7f3fc191e1b9e0827d43584e5e2536591d76cefe5fdd8937bf222c3` |
| Indicators | sentinel match (+6); MACE anomaly (+3); extension/content mismatch (+2); suspicious location (+1) |

A text file disguised with a `.jpg` extension, backdated ~120 days, located
in `logs`, and containing the logger sentinel. This is the strongest
possible finding — four independent indicators, capped at 10.

### Finding 2 — `update_cache.dat` — CONFIRMED (7/10, HIGH)

| Field | Value |
|-------|-------|
| Path | `./logs/update_cache.dat` |
| Size | 116 bytes |
| SHA-256 | `222f3b30a0012f32768b8662131cd3907a39804f47f045bd41a2575390e5789f` |
| Indicators | sentinel match (+6); suspicious location (+1) |

A file with a legitimate-looking cache name containing captured commands
(`whoami`, `net user`, `ipconfig /all`) and the sentinel.

### Finding 3 — `/tmp/code-sign` — UNRELATED (6/10, MEDIUM)

| Field | Value |
|-------|-------|
| Path | `/tmp/code-sign` |
| SHA-256 | `0b8e33ad4fd7c011b212ed59dde957d8aff06e63a7e9fe052ffd29bfa5da6a5c` |
| Indicators | MACE anomaly (+3); timestamp anomaly (+2); suspicious location (+1) |

A pre-existing system file that tripped weak signals but **lacked the
sentinel**, so it stayed at MEDIUM and was not confirmed. This is the
weighting working as designed: suspicious circumstance without content proof
does not reach HIGH.

### True negatives (correctly ignored)

| File | Why it was correctly not flagged |
|------|----------------------------------|
| `logs/notes.txt` | Benign text, no indicators — scored 0 |
| `logs/directions.txt` | Contains the word "STOP" but not the sentinel — **the v1 false-positive trap, now defeated** |

---

## 6. MITRE ATT&CK Mapping

| Technique | ID | Observed behaviour |
|-----------|----|--------------------|
| Indicator Removal: Timestomp | T1070.006 | `thumb_cache.jpg` mtime backdated 120 days |
| Hide Artifacts: Hidden Files | T1564.001 | Logger sets hidden/system attributes (Windows) |
| Masquerading: Match Legitimate Name | T1036.005 | `update_cache.dat`, `thumb_cache.jpg` disguised names |
| Data Staged: Local Data Staging | T1074.001 | Writes to temp/appdata fallback locations |
| Input Capture: Keylogging | T1056.001 | Console input capture (core logger function) |

---

## 7. Detection Coverage Produced

This incident produced reusable, portable detection content so the same
techniques are caught in a real SIEM/EDR, not just by the local scanner.

### YARA — `rules.yar`
Content signature matching the unique sentinel and supporting markers.
Portable to any YARA-capable scanner or EDR (e.g. Wazuh).

### Sigma — `sigma/*.yml`
| Rule | Technique | Log source |
|------|-----------|------------|
| `01_timestomping.yml` | T1070.006 | Sysmon EID 2 (file_change) |
| `02_hidden_system_attribute.yml` | T1564.001 | process_creation (attrib.exe) |
| `03_masqueraded_file_in_temp.yml` | T1036.005 / T1074.001 | Sysmon EID 11 (file_event) |
| `04_multi_location_write.yml` | T1056.001 / T1074.001 | Sysmon EID 11 (correlation) |

All four validated as well-formed Sigma (required fields + condition present)
and can be converted to Splunk/Elastic/Sentinel queries via `sigma convert`.

---

## 8. Gaps & Limitations

- **On-disk only.** The detector inspects files that already exist; it
  cannot name the process that created them. Attributing creation to
  `python.exe` vs `cmd.exe` requires live telemetry (Sysmon / EDR) — this
  is exactly what the Sigma rules cover, and why both layers exist.
- **Sentinel dependency.** Content detection relies on a known sentinel.
  A logger variant using a different marker would drop to the weak-signal
  path (MACE, attributes, mismatch) and likely land at MEDIUM, not HIGH.
- **MACE semantics on Linux.** `ctime` is inode-change time on Linux, not
  true creation time; the anomaly check is strongest on Windows/macOS.
- **Size cap.** Files above the read cap are hashed but not fully content-
  scanned; a very large logger output could evade the content signal.

---

## 9. Recommendations

1. **Deploy the Sigma rules to the SIEM** and confirm Sysmon EID 2 and 11
   are being collected; without them, rules 01/03/04 have no data source.
2. **Add behavioural (process-context) detection** as a follow-on project —
   a live monitor that flags *which* process writes to temp/appdata, closing
   the on-disk gap in Section 8.
3. **Tune false positives** on rules 01 and 04 against a week of baseline
   telemetry before raising their level from `medium`/`high` to alerting.
4. **Rotate the sentinel** between logger versions and update `rules.yar`
   and `03`'s regex accordingly, so detection tracks the offense.

---

## 10. Appendix — Reproduction

```bash
# stage scene
mkdir -p ir_scene/logs && cd ir_scene
printf '...captured commands...\n===SESSION_END_7f3a9c===\n' > logs/update_cache.dat
printf '...\n===SESSION_END_7f3a9c===\n' > logs/thumb_cache.jpg
touch -d "120 days ago" logs/thumb_cache.jpg      # simulate timestomp

# run detector (press Enter for default sentinel, 'no' to preserve evidence)
python3 detector.py

# validate Sigma rules
python3 - <<'PY'
import yaml, glob
for p in glob.glob("sigma/*.yml"):
    d = yaml.safe_load(open(p))
    assert {"title","logsource","detection"} <= set(d) and "condition" in d["detection"]
    print("valid:", p)
PY
```

---
*End of report. Project 1 (Detection Engineering Lab) closed.*
