import os
if os.path.exists("logs/activity_log.csv"):
    os.remove("logs/activity_log.csv")

from detectors.anomaly import check_anomaly

sample_text = """John Doe works at Google.
Email: john@gmail.com
Phone: +1 987-654-3210
Location: New York
SSN: 123-45-6789
Bank Account: 0099887766
Credit Card: 4111 1111 1111 1111
Passport No: X1234567"""

text_length = len(sample_text)
risk_score = 210

result = check_anomaly("brand_new_user_xyz", {
    "text_length": text_length,
    "risk_score": risk_score
})
print(result)