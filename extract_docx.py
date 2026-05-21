import zipfile
import xml.etree.ElementTree as ET
import os

def docx_to_txt(docx_path, txt_path):
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml')
        root = ET.fromstring(xml_content)
        
        paragraphs = []
        # Find all paragraph elements
        for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            # For each paragraph, find all text elements
            texts = []
            for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if node.text:
                    texts.append(node.text)
            paragraphs.append(''.join(texts))
            
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(paragraphs))

if __name__ == '__main__':
    docx_path = '/Users/edley/Documents/ANT2/SBXPC OCX Reference Manual v3.12 - Neutral.docx'
    txt_path = '/Users/edley/Documents/ANT2/manual.txt'
    if os.path.exists(docx_path):
        print(f"Extracting {docx_path}...")
        docx_to_txt(docx_path, txt_path)
        print(f"Extracted to {txt_path}")
    else:
        print(f"File not found: {docx_path}")
