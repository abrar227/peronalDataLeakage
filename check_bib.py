from pypdf import PdfReader
reader = PdfReader('Intelligent_Personal_Data_Leakage_Detection_System_Report (2).pdf')
# Print text from the last 2 pages
for i in range(max(0, len(reader.pages)-2), len(reader.pages)):
    print(f"--- Page {i} ---")
    print(reader.pages[i].extract_text()[:500]) # Print first 500 chars to see if it says Bibliography
