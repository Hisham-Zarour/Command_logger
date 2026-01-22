# Cybersecurity Learning Project: From Basic Logger to Advanced Detector

## 👋 About Me
Hello! I'm **Hisham Zarour**, a Computer Science student with a passion for cybersecurity. This project represents my hands-on journey from building simple tools to creating sophisticated security systems. Through iterative development, I explored both offensive techniques and defensive countermeasures.

## 📁 Project Evolution & Files

### **Phase 1: Foundation** (`command_logger.py`)
- **Purpose**: Understand basic input/output and file operations
- **Features**: Simple line-by-line input capture, saves to visible text file
- **Complexity**: Beginner - ~15 lines of code

### **Phase 2: Persistence** (`saving_files.py`)
- **Purpose**: Learn file system operations and error handling
- **Features**: Saves to multiple locations, automatic fallback if primary fails, creates necessary directories
- **Complexity**: Intermediate - ~40 lines of code

### **Phase 3: Evasion** (`stealth.py`)
- **Purpose**: Explore anti-forensics and stealth techniques
- **Features**: Hidden/system file attributes, timestamp spoofing (30-180 days old), mimics legitimate system files
- **Complexity**: Advanced - ~80 lines of code

### **Phase 4: Defense** (`detector.py`)
- **Purpose**: Build defensive security tools and incident response
- **Features**: Scans common persistence locations, detects hidden/stealth files, automatic quarantine, generates forensic reports
- **Complexity**: Expert - ~200 lines of code

### **Utilities** (`stealth_functions.py`)
- Reusable functions for file attribute manipulation and timestamp operations

## 🎯 What I Learned

### **Technical Skills:**
- **Python Programming**: From basic syntax to Windows API integration
- **File System Mastery**: Path manipulation, attributes, permissions, cross-platform considerations
- **Error Handling**: Robust try/except patterns, graceful degradation
- **System Integration**: Working with Windows file attributes and commands

### **Cybersecurity Concepts:**
- **Persistence**: How malware maintains presence across system reboots
- **Evasion**: Techniques like timestamp spoofing and file hiding
- **Detection**: Pattern recognition in suspicious file locations and attributes
- **Incident Response**: Safe quarantine procedures and forensic reporting
- **Defense-in-Depth**: Multiple detection layers and verification

### **Development Methodology:**
- Iterative development from simple to complex
- Building complementary offensive/defensive tools
- Documentation and forensic logging
- Ethical considerations in security tool development

## 🚀 How to Use (Educational Purposes Only)

### **Testing the Progression:**
```bash
# Start with basics
python command_logger_v1.py
# Type some input, then "STOP"
# Check for simple_log.txt in current folder

# Test file operations
python command_logger_v2_save.py
# Files will be saved to multiple locations

# Experience stealth techniques
python command_logger_v3_stealth.py
# Files will be hidden - try to find them in File Explorer

# Run the detector
python detector.py
# Will scan, detect, and offer to quarantine all files
