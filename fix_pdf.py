import pypdf

reader = pypdf.PdfReader('Combined_Report_With_Headers.pdf')
writer = pypdf.PdfWriter()

title_reader = pypdf.PdfReader('gen_title.pdf')
writer.add_page(title_reader.pages[0])

mask_reader = pypdf.PdfReader('mask.pdf')
mask_page = mask_reader.pages[0]

lists_reader = pypdf.PdfReader('gen_lists.pdf')
ov24_reader = pypdf.PdfReader('overlay_24.pdf')
ov25_reader = pypdf.PdfReader('overlay_25.pdf')
ov28_reader = pypdf.PdfReader('overlay_28.pdf')
ov29_reader = pypdf.PdfReader('overlay_29.pdf')

for i in range(2, 8):
    if i == 6:
        writer.add_page(lists_reader.pages[0])
        writer.add_page(lists_reader.pages[1])
    else:
        page = reader.pages[i]
        page.merge_page(mask_page)
        writer.add_page(page)

for i in range(8, len(reader.pages)):
    if i == 24:
        writer.add_page(ov24_reader.pages[0])
    elif i == 25:
        writer.add_page(ov25_reader.pages[0])
    elif i == 27:
        writer.add_page(ov28_reader.pages[0])
    elif i == 28:
        writer.add_page(ov29_reader.pages[0])
    else:
        writer.add_page(reader.pages[i])

with open('Combined_Report_With_Headers - Copy.pdf', 'wb') as f:
    writer.write(f)
print('PDF fixed entirely!')
