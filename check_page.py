from pypdf import PdfReader
import re
reader = PdfReader('Chapter5_System_Design_updated.pdf')
last_page_text = reader.pages[-1].extract_text()
# Try to find the page number at the bottom. Usually it's isolated or at the end.
lines = last_page_text.strip().split('\n')
print("Last 5 lines of Chapter 5:")
for line in lines[-5:]:
    print(repr(line))
