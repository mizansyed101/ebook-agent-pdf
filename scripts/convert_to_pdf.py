import os
import re
from fpdf import FPDF


class EbookPDF(FPDF):
    """Custom PDF class with headers and footers for the eBook."""
    
    def __init__(self, book_title="eBook", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._book_title = book_title

    def header(self):
        if self.page_no() > 2:
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, self._book_title, new_x="RIGHT", new_y="TOP", align='R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        if self.page_no() > 1:
            self.cell(0, 10, f'Page {self.page_no()}', new_x="RIGHT", new_y="TOP", align='C')

    def chapter_title(self, title):
        self.ln(10)
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(25, 25, 25)
        self.write(12, title)
        self.ln(8)
        # Decorative line under chapter title
        self.set_draw_color(80, 80, 80)
        self.set_line_width(0.5)
        x = self.get_x()
        y = self.get_y()
        self.line(x, y, x + 50, y)
        self.ln(10)

    def section_title(self, title):
        self.ln(6)
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(40, 40, 40)
        self.write(9, title)
        self.ln(8)

    def body_text(self, text):
        self.set_font('helvetica', '', 11)
        self.set_text_color(30, 30, 30)
        self._write_rich_text(text, 7)
        self.ln(6)

    def bullet_item(self, text):
        self.set_font('helvetica', '', 11)
        self.set_text_color(30, 30, 30)
        self.cell(8, 7, chr(149), new_x="END", new_y="TOP")
        self._write_rich_text(text, 7)
        self.ln(6)

    def numbered_item(self, text):
        self.set_font('helvetica', '', 11)
        self.set_text_color(30, 30, 30)
        self._write_rich_text(text, 7)
        self.ln(6)

    def _write_rich_text(self, text, line_height):
        """Write text with inline bold (**bold**) support."""
        parts = re.split(r'\*\*(.+?)\*\*', text)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                part = re.sub(r'\*(.+?)\*', r'\1', part)
                self.set_font('helvetica', '', 11)
                self.write(line_height, part)
            else:
                self.set_font('helvetica', 'B', 11)
                self.write(line_height, part)
        self.set_font('helvetica', '', 11)


def sanitize_content(content):
    """Replace Unicode characters with ASCII equivalents."""
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2014': '--', '\u2013': '-',
        '\u2026': '...',
        '\u00a0': ' ',
        '\u2022': '-',
        '\u00e9': 'e', '\u00e8': 'e',
        '\u00e0': 'a',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    content = content.encode('ascii', 'ignore').decode('ascii')
    return content


def create_pdf(input_file, output_file, book_title=None):
    """
    Convert a Markdown eBook file to a professionally formatted PDF.
    
    Args:
        input_file: Path to the markdown source file
        output_file: Path for the output PDF file
        book_title: Optional title override. If None, extracted from content.
    """
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    content = sanitize_content(content)

    # Extract title from content if not provided
    if not book_title:
        for line in content.split('\n'):
            if line.startswith('# '):
                book_title = line[2:].strip()
                break
        if not book_title:
            book_title = "Untitled eBook"

    pdf = EbookPDF(book_title=book_title)
    pdf.set_margins(25, 20, 25)
    pdf.set_auto_page_break(auto=True, margin=25)

    # ===========================
    # TITLE PAGE
    # ===========================
    pdf.add_page()
    pdf.ln(50)

    # Decorative top line
    pdf.set_draw_color(60, 60, 60)
    pdf.set_line_width(0.8)
    pdf.line(25, 55, 185, 55)

    pdf.set_font('helvetica', 'B', 26)
    pdf.set_text_color(20, 20, 20)
    
    # Word-wrap long titles
    title_lines = _wrap_title(book_title, max_chars=35)
    pdf.multi_cell(0, 14, '\n'.join(title_lines), align='C')
    pdf.ln(8)

    # Decorative line under title
    pdf.set_draw_color(60, 60, 60)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(70, y, 140, y)

    pdf.ln(10)
    pdf.set_font('helvetica', 'I', 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, 'ultimate guide', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(60)
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, 'Created by Mizan', new_x="LMARGIN", new_y="NEXT", align='C')

    # ===========================
    # TABLE OF CONTENTS
    # ===========================
    chapters_split = content.split('---')
    toc_entries = []
    for chapter in chapters_split:
        lines = chapter.strip().split('\n')
        for line in lines:
            if line.startswith('## '):
                toc_entries.append(line[3:].strip())
                break

    pdf.add_page()
    pdf.set_font('helvetica', 'B', 22)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 15, 'Table of Contents', new_x="LMARGIN", new_y="NEXT", align='L')
    pdf.ln(3)

    # Decorative line
    pdf.set_draw_color(80, 80, 80)
    pdf.set_line_width(0.3)
    y = pdf.get_y()
    pdf.line(25, y, 185, y)
    pdf.ln(8)

    pdf.set_font('helvetica', '', 12)
    pdf.set_text_color(30, 30, 30)
    for title in toc_entries:
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align='L')

    # ===========================
    # BODY CONTENT
    # ===========================
    chapters_split = content.split('---')

    for chapter in chapters_split:
        if not chapter.strip():
            continue

        pdf.add_page()
        lines = chapter.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(3)
                continue

            # Skip the book title (H1)
            if line.startswith('# ') and not line.startswith('## '):
                continue

            if line.startswith('## '):
                pdf.chapter_title(line[3:].strip())
            elif line.startswith('### '):
                pdf.section_title(line[4:].strip())
            elif line.startswith('- '):
                pdf.bullet_item(line[2:])
            elif len(line) > 2 and line[0].isdigit() and line[1] == '.':
                pdf.numbered_item(line)
            else:
                pdf.body_text(line)

    pdf.output(output_file)
    print(f"PDF successfully created: {output_file}")
    print(f"Total pages: {pdf.page_no()}")
    return pdf.page_no()


def _wrap_title(title, max_chars=35):
    """Wrap a long title into multiple lines."""
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 > max_chars and current_line:
            lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line += word + " "
    if current_line.strip():
        lines.append(current_line.strip())
    return lines


if __name__ == "__main__":
    input_path = r"C:\ANTIGRAVITY\EBOOK AGENT MAIN\content\ebook_content.md"
    output_path = r"C:\ANTIGRAVITY\EBOOK AGENT MAIN\Your_Fear_is_Arrogance.pdf"
    create_pdf(input_path, output_path)
