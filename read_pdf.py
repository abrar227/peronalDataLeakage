import pypdf
reader = pypdf.PdfReader('C:/Users/ADMIN/peronalDataLeakage/presentation/presentation.pdf')
for i, page in enumerate(reader.pages):
    print('Slide', i+1, page.extract_text()[:60].strip().replace('\n', ' '))
