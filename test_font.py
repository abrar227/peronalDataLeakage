from pypdf import PdfReader
reader = PdfReader('Chapter5_System_Design_updated.pdf')
page = reader.pages[1]
if "/Resources" in page and "/Font" in page["/Resources"]:
    fonts = page["/Resources"]["/Font"]
    for key in fonts:
        font = fonts[key].get_object()
        print(font.get("/BaseFont"))
