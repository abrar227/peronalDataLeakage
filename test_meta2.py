from pypdf import PdfReader
reader = PdfReader('Intelligent_Personal_Data_Leakage_Detection_System_Report (2).pdf')
info = reader.metadata
print("Creator:", info.get('/Creator', 'Unknown'))
print("Producer:", info.get('/Producer', 'Unknown'))
if "/Resources" in reader.pages[1] and "/Font" in reader.pages[1]["/Resources"]:
    fonts = reader.pages[1]["/Resources"]["/Font"]
    for key in fonts:
        font = fonts[key].get_object()
        print(font.get("/BaseFont"))
