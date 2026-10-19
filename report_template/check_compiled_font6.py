from pypdf import PdfReader
reader = PdfReader('test_font_compile6.pdf')
page = reader.pages[0]
if "/Resources" in page and "/Font" in page["/Resources"]:
    fonts = page["/Resources"]["/Font"]
    for key in fonts:
        font = fonts[key].get_object()
        print("Compiled Font:", font.get("/BaseFont"))
