from pypdf import PdfReader
reader = PdfReader('Chapter5_System_Design_updated.pdf')
info = reader.metadata
print("Creator:", info.get('/Creator', 'Unknown'))
print("Producer:", info.get('/Producer', 'Unknown'))
