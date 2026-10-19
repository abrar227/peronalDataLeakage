import PyPDF2
reader_combined = PyPDF2.PdfReader('Combined_Report_With_Headers.pdf')
reader_new = PyPDF2.PdfReader('report_template/build_chapters.pdf')
writer = PyPDF2.PdfWriter()
for i in range(30):
    writer.add_page(reader_combined.pages[i])
for i in range(len(reader_new.pages)):
    writer.add_page(reader_new.pages[i])
with open('Combined_Report_With_Headers_Updated.pdf', 'wb') as f:
    writer.write(f)
