from pypdf import PdfReader
reader = PdfReader('Intelligent_Personal_Data_Leakage_Detection_System_Report (2).pdf')
box = reader.pages[0].mediabox
print("Width:", box.width)
print("Height:", box.height)
