# Cybersecurity Learning Project: From Basic Logger to Advanced Detector

## 👋 About Me

Hello! I'm **Hisham Zarour**, a Computer Science student with a passion for cybersecurity. This project represents my hands-on journey from building simple tools to creating sophisticated security systems. Through iterative development, I explored both offensive techniques and defensive countermeasures.

---

## 📁 Project Evolution & Files

### Phase 1: Foundation (`command_logger_v1.py`)

| Aspect | Details |
|--------|---------|
| **Purpose** | Understand basic input/output and file operations |
| **Features** | Simple line-by-line input capture, saves to visible text file |
| **Complexity** | Beginner - ~15 lines of code |

### Phase 2: Persistence (`saving_files.py`)

| Aspect | Details |
|--------|---------|
| **Purpose** | Learn file system operations and error handling |
| **Features** | Saves to multiple locations, automatic fallback if primary fails, creates necessary directories |
| **Complexity** | Intermediate - ~40 lines of code |

### Phase 3: Evasion (`stealth.py`)

| Aspect | Details |
|--------|---------|
| **Purpose** | Explore anti-forensics and stealth techniques |
| **Features** | Hidden/system file attributes, timestamp spoofing (30-180 days old), mimics legitimate system files |
| **Complexity** | Advanced - ~80 lines of code |

### Phase 4: Advanced Stealth Logger (`final_command_logger.py`) 🆕

| Aspect | Details |
|--------|---------|
| **Purpose** | Implement production-level evasion techniques used by real malware |
| **Features** | 6 different random filename styles, per-location evasion strategy, GUID/hex/timestamp naming, legitimate software mimicry, Windows system file mimicry, cross-platform fallback |
| **Complexity** | Expert - ~250 lines of code |

**What makes this version special:**
- **No predictable patterns** - Each save location uses a different naming style
- **Social engineering evasion** - Files named like `chrome_cache.log` or `win32.log`
- **Hash-style evasion** - Files named like `7f3a9c2b.txt` (hex only)
- **Registry-style evasion** - Files named like `{a1b2c3d4-e5f6-...}.txt` (GUID format)
- **Timestamp-based evasion** - Files named like `20260122_143022_a1b2.txt`
- **True randomness** - Files named like `jk3n9s2.txt` (alphanumeric random)

### Phase 5: Advanced Detector (`detector_v2.py`) 🆕

| Aspect | Details |
|--------|---------|
| **Purpose** | Detect sophisticated evasion techniques that Phase 4 implements |
| **Features** | 8 detection heuristics, confidence scoring (1-10), threat level classification (HIGH/MEDIUM/LOW), filename style analysis (GUID/hex/timestamp/random/legit/system mimic), attribute checking, timestamp anomaly detection, detailed forensic reporting |
| **Complexity** | Expert - ~300 lines of code |

**What makes this version special:**
- **Heuristic detection** - Finds unknown variants, not just known filenames
- **Confidence scoring** - Prioritizes real threats over false positives
- **Style analysis** - Identifies WHICH evasion technique was used
- **Threat classification** - HIGH (7-10), MEDIUM (4-6), LOW (1-3)
- **Comprehensive reporting** - Full forensic analysis of each detected file

### Utilities (`stealth_functions.py`)

Reusable functions for file attribute manipulation, timestamp operations, and random filename generation.

---

## 📊 Feature Comparison

| Feature | v1 | v2 | v3 | Final Logger | Detector v2 |
|---------|:--:|:--:|:--:|:--:|:--:|
| Basic input capture | ✅ | ✅ | ✅ | ✅ | - |
| Single file save | ✅ | - | - | - | - |
| Multi-location save | - | ✅ | ✅ | ✅ | - |
| Error handling | - | ✅ | ✅ | ✅ | - |
| Hidden file attribute | - | - | ✅ | ✅ | ✅ |
| System file attribute | - | - | ✅ | ✅ | ✅ |
| Timestamp spoofing | - | - | ✅ | ✅ | ✅ |
| Random filenames | - | - | - | ✅ | ✅ |
| GUID format names | - | - | - | ✅ | ✅ |
| Hex-only names | - | - | - | ✅ | ✅ |
| Legitimate software mimicry | - | - | - | ✅ | ✅ |
| Windows system mimicry | - | - | - | ✅ | ✅ |
| Confidence scoring | - | - | - | - | ✅ |
| Threat classification | - | - | - | - | ✅ |
| Forensic reporting | - | - | - | - | ✅ |
| Quarantine | - | - | - | - | ✅ |

---

## 🎯 What I Learned

### Technical Skills:
- **Python Programming**: From basic syntax to Windows API integration
- **File System Mastery**: Path manipulation, attributes, permissions, cross-platform considerations
- **Error Handling**: Robust try/except patterns, graceful degradation
- **System Integration**: Working with Windows file attributes and commands
- **Pattern Recognition**: Building heuristic detection for unknown variants
- **Threat Scoring**: Confidence-based prioritization systems

### Cybersecurity Concepts:
- **Persistence**: How malware maintains presence across system reboots
- **Evasion**: 6 different filename obfuscation techniques
- **Social Engineering**: Mimicking legitimate software to avoid suspicion
- **Anti-Forensics**: GUID/hex/timestamp naming to defeat pattern matching
- **Detection**: Heuristic analysis for unknown evasion techniques
- **Incident Response**: Safe quarantine procedures and forensic reporting
- **Defense-in-Depth**: Multiple detection layers and verification
- **Threat Intelligence**: Confidence scoring and prioritization

### Development Methodology:
- Iterative development from simple to complex
- Building complementary offensive/defensive tools
- Documentation and forensic logging
- Ethical considerations in security tool development
- Real-world evasion vs detection feedback loop

---

## 🚀 How to Use (Educational Purposes Only)

### Testing the Progression:

```bash
# Phase 1: Start with basics
python command_logger_v1.py
# Type some input, then "STOP"
# Check for simple_log.txt in current folder

# Phase 2: Test file operations
python saving_files.py
# Files will be saved to multiple locations

# Phase 3: Experience basic stealth
python stealth.py
# Files will be hidden - try to find them in File Explorer

# Phase 4: Advanced evasion (6 filename styles)
python final_command_logger.py
# Files will have RANDOM names in 6 different styles
# Each location gets a different evasion technique
# Try to find them - they're designed to be hard!

# Phase 5: Advanced detection
python detector_v2.py
# Will scan, detect ALL evasion techniques
# Shows confidence scores and threat levels
# Offers quarantine with forensic report
