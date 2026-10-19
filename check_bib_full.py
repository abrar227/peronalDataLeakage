from pypdf import PdfReader
reader = PdfReader('Intelligent_Personal_Data_Leakage_Detection_System_Report (2).pdf')
print(reader.pages[23].extract_text())
