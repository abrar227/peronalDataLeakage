from detector import detect_sensitive_data

text = "My email is abrar@gmail.com and phone is 9876543210"

result = detect_sensitive_data(text)

print("Detected Data:")
print(result)