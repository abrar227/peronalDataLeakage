from pypdf import PdfReader
reader = PdfReader('test_overlay.pdf')
text = reader.pages[0].extract_text()
print("--- PAGE 1 of test ---")
print(text[:200])
