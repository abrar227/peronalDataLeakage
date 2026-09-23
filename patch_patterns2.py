import re

file_path = r'c:\Users\ADMIN\peronalDataLeakage\detectors\rule_based.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

insert_patterns = """
    "driver_license": re.compile(
        r'(?i)\\b(?:driver\\'?s?\\s+license)(?:\\s+number)?\\s*[:=is]*\\s*([A-Z0-9]{5,20})\\b'
    ),
    "security_question": re.compile(
        r'(?i)\\b(?:security\\s+question|maiden\\s+name|first\\s+pet|city\\s+of\\s+birth)\\b'
    ),
"""

content = content.replace(
    r'"address": re.compile(',
    insert_patterns.lstrip() + '    "address": re.compile('
)

content = content.replace(
    r'"medical": 0.85,',
    r'"medical": 0.85,' + '\n    "driver_license": 0.90,\n    "security_question": 0.80,'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('rule_based.py updated again!')

risk_file = r'c:\Users\ADMIN\peronalDataLeakage\detectors\risk_scoring.py'
with open(risk_file, 'r', encoding='utf-8') as f:
    risk_content = f.read()

risk_content = risk_content.replace(
    r'"medical": 30,',
    r'"medical": 30,' + '\n    "driver_license": 40,\n    "security_question": 20,'
)
with open(risk_file, 'w', encoding='utf-8') as f:
    f.write(risk_content)

print('risk_scoring.py updated again!')
