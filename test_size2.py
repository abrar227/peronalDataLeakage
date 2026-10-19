from pypdf import PdfReader
reader = PdfReader('Combined_Report_With_Headers.pdf')
box = reader.pages[0].mediabox
print("Combined Width:", box.width)
print("Combined Height:", box.height)
