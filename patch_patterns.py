import re

file_path = r'c:\Users\ADMIN\peronalDataLeakage\detectors\rule_based.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add passport and medical patterns to PATTERNS
insert_patterns = """
    "passport": re.compile(
        r'(?i)\\b(?:passport(?:\\s+no\\.?|\\s+number)?\\s*[:=is]*\\s*)([a-z0-9]{7,9})\\b'
    ),
    "medical": re.compile(
        r'(?i)\\b(?:medical leave|surgery|diagnosis|medical record|prescription|hospitalized)\\b'
    ),
"""

# Find the end of PATTERNS dict
content = content.replace(
    r'"address": re.compile(',
    insert_patterns.lstrip() + '    "address": re.compile('
)

# Also update FIXED_CONFIDENCE
content = content.replace(
    r'"ssn": 0.85,',
    r'"ssn": 0.85,' + '\n    "passport": 0.90,\n    "medical": 0.85,'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('rule_based.py updated!')

risk_file = r'c:\Users\ADMIN\peronalDataLeakage\detectors\risk_scoring.py'
with open(risk_file, 'r', encoding='utf-8') as f:
    risk_content = f.read()

risk_content = risk_content.replace(
    r'"ssn": 40,',
    r'"ssn": 40,' + '\n    "passport": 40,\n    "medical": 30,'
)
with open(risk_file, 'w', encoding='utf-8') as f:
    f.write(risk_content)

print('risk_scoring.py updated!')
