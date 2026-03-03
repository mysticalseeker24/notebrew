import fitz  # PyMuPDF
import re
from typing import Dict, List, Tuple
import pdfplumber
from pathlib import Path

class PDFParser:
    """Enhanced PDF parser with LaTeX extraction and structure recognition"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def extract_full_text(self) -> str:
        """Extract all text from PDF"""
        text = ""
        for page in self.doc:
            text += page.get_text()
        return text
    
    def extract_latex_equations(self) -> List[str]:
        """Extract LaTeX equations from PDF"""
        equations = []
        text = self.extract_full_text()
        
        # Pattern for inline equations
        inline_patterns = [
            r'\$([^\$]+)\$',
            r'\\\((.+?)\\\)',
        ]
        
        # Pattern for display equations
        display_patterns = [
            r'\$\$(.+?)\$\$',
            r'\\\[(.+?)\\\]',
            r'\\begin\{equation\}(.+?)\\end\{equation\}',
            r'\\begin\{align\}(.+?)\\end\{align\}',
            r'\\begin\{gather\}(.+?)\\end\{gather\}',
        ]
        
        for pattern in inline_patterns + display_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            equations.extend(matches)
        
        return [eq.strip() for eq in equations if eq.strip()]
    
    def extract_sections(self) -> Dict[str, str]:
        """Extract paper sections (Abstract, Introduction, Methods, etc.)"""
        text = self.extract_full_text()
        sections = {}
        
        # Common section headers in research papers
        section_patterns = [
            r'(?i)abstract\s*\n(.*?)(?=\n\d+\s+[A-Z]|\nI{1,3}\.|$)',
            r'(?i)introduction\s*\n(.*?)(?=\n\d+\s+[A-Z]|\nI{1,3}\.|$)',
            r'(?i)(?:methodology|methods)\s*\n(.*?)(?=\n\d+\s+[A-Z]|\nI{1,3}\.|$)',
            r'(?i)(?:experiments?|results?)\s*\n(.*?)(?=\n\d+\s+[A-Z]|\nI{1,3}\.|$)',
            r'(?i)conclusion\s*\n(.*?)(?=\n\d+\s+[A-Z]|\nI{1,3}\.|references|$)',
        ]
        
        for i, pattern in enumerate(section_patterns):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                section_name = ['abstract', 'introduction', 'methodology', 'experiments', 'conclusion'][i]
                sections[section_name] = match.group(1).strip()
        
        return sections
    
    def extract_metadata(self) -> Dict:
        """Extract paper metadata"""
        metadata = {
            'num_pages': len(self.doc),
            'title': self.doc.metadata.get('title', ''),
            'author': self.doc.metadata.get('author', ''),
            'subject': self.doc.metadata.get('subject', ''),
            'creator': self.doc.metadata.get('creator', ''),
        }
        
        # Try to extract title from first page if not in metadata
        if not metadata['title']:
            first_page = self.doc[0].get_text()
            lines = first_page.split('\n')
            if lines:
                metadata['title'] = lines[0].strip()
        
        return metadata
    
    def extract_tables(self) -> List[List[List[str]]]:
        """Extract tables from PDF using pdfplumber"""
        tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        return tables
    
    def extract_figures(self) -> List[Dict]:
        """Extract figure information (positions and references)"""
        figures = []
        for page_num, page in enumerate(self.doc):
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                figures.append({
                    'page': page_num + 1,
                    'index': img_index,
                    'xref': img[0],
                })
        return figures
    
    def get_complete_structure(self) -> Dict:
        """Get complete paper structure"""
        return {
            'metadata': self.extract_metadata(),
            'text': self.extract_full_text(),
            'sections': self.extract_sections(),
            'equations': self.extract_latex_equations(),
            'tables': self.extract_tables(),
            'figures': self.extract_figures(),
        }
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'doc'):
            self.doc.close()
