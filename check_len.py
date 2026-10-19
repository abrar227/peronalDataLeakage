from pypdf import PdfReader
reader = PdfReader('Intelligent_Personal_Data_Leakage_Detection_System_Report (2).pdf')
print("Total pages:", len(reader.pages))
