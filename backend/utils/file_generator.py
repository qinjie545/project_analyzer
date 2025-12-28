import os
import markdown2
import base64
import re
import requests
import logging
import json
import zlib
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None
from htmldocx import HtmlToDocx
import htmldocx.h2d
from docx import Document
from bs4 import BeautifulSoup

# Monkey patch htmldocx.h2d.is_url to support data URIs
# This fixes [Errno 63] File name too long when using data URIs in DOCX
original_is_url = htmldocx.h2d.is_url
def patched_is_url(url):
    if url.startswith('data:'):
        return True
    return original_is_url(url)
htmldocx.h2d.is_url = patched_is_url

def replace_mermaid_with_images(markdown_text):
    """
    Replace mermaid code blocks with embedded images from mermaid.ink
    """
    def replacer(match):
        code = match.group(1).strip()
        # Common LLM mistake: repeating 'mermaid' inside the block
        if code.startswith('mermaid'):
            code = code[7:].strip()
            
        try:
            # Use Pako (Deflate) encoding for better compatibility (especially with Chinese characters)
            json_obj = {"code": code, "mermaid": {"theme": "default"}}
            json_str = json.dumps(json_obj)
            compressed = zlib.compress(json_str.encode('utf-8'))
            # Use URL-safe Base64 and strip padding
            code_b64 = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')
            url = f"https://mermaid.ink/img/pako:{code_b64}"
            
            # Fetch the image to embed it (avoids network issues during PDF/Docx gen)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                img_b64 = base64.b64encode(response.content).decode('ascii')
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                data_uri = f"data:{content_type};base64,{img_b64}"
                return f"![Mermaid Diagram]({data_uri})"
            else:
                return f"> **Mermaid Diagram Error**: Failed to generate image (Status {response.status_code}). Please check the diagram syntax."
        except Exception as e:
            return f"> **Mermaid Diagram Error**: {str(e)}"
    
    # Regex for fenced code blocks with mermaid
    pattern = r"```mermaid\s+(.*?)```"
    return re.sub(pattern, replacer, markdown_text, flags=re.DOTALL)

def generate_files(article_id, title, content, output_dir):
    """
    Generates HTML, PDF, and DOCX files for the given article content.
    Returns a dictionary with the paths (relative to output_dir) of the generated files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sanitize title for filename
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
    # Truncate title to avoid "File name too long" errors (limit to 50 chars)
    if len(safe_title) > 50:
        safe_title = safe_title[:50]
    base_filename = f"{article_id}_{safe_title}"

    # Pre-process content to replace Mermaid diagrams with images for ALL formats
    # This ensures consistency and solves offline/compatibility issues
    content_with_images = replace_mermaid_with_images(content)

    # 1. Generate HTML
    html_body = markdown2.markdown(content_with_images, extras=["fenced-code-blocks", "tables", "break-on-newline"])
    
    # Rich CSS (GitHub-like) + Font support for PDF
    # We try to locate the font file first
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy-microhei/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy-zenhei/wqy-zenhei.ttc",
    ]
    
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc" # Default
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            logging.info(f"PDF Generator using font: {font_path}")
            break
    
    # Common CSS for both Web and PDF (Base styles)
    base_css = f"""
        @font-face {{
            font-family: "WenQuanYi Micro Hei";
            src: url("file://{font_path}");
        }}
        body {{
            font-family: "WenQuanYi Micro Hei", Helvetica, Arial, sans-serif;
            color: #24292f;
            line-height: 1.5;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
        h3 {{ font-size: 1.25em; }}
        p {{ margin-top: 0; margin-bottom: 10px; }}
        code {{
            background-color: #f6f8fa;
            padding: .2em .4em;
            border-radius: 6px;
            font-family: "WenQuanYi Micro Hei", monospace;
            font-size: 85%;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow: auto;
            line-height: 1.45;
            margin-bottom: 16px;
            font-family: "WenQuanYi Micro Hei", monospace;
        }}
        blockquote {{
            border-left: .25em solid #dfe2e5;
            color: #6a737d;
            padding: 0 1em;
            margin: 0 0 16px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }}
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }}
        tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
    """

    # Web-specific CSS (Centered layout, larger padding)
    web_css = base_css + """
        body {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
            font-size: 16px;
        }
        a { color: #0969da; text-decoration: none; }
        a:hover { text-decoration: underline; }
    """

    # PDF-specific CSS (Full width, page margins, specific font sizes for print)
    # xhtml2pdf specific: @page rule
    pdf_css = base_css + """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-size: 12pt; /* Explicit pt size for PDF */
            padding: 0 20px 0 0; /* Add right padding to prevent overflow */
            margin: 0;
        }
        /* Ensure pre/code blocks don't overflow or look too small */
        pre {
            white-space: pre-wrap; /* Wrap long lines in PDF */
            word-wrap: break-word;
            word-break: break-all; /* Force break for long strings/code */
            font-size: 10pt;
            overflow-wrap: break-word;
            max-width: 100%;
        }
        /* Adjust headings for PDF */
        h1 { font-size: 24pt; margin-top: 0; }
        h2 { font-size: 18pt; }
        h3 { font-size: 14pt; }
        /* Fix image sizing in PDF */
        img {
            width: 100%; /* Force images to fit width */
            height: auto;
        }
    """

    styled_html_web = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
        {web_css}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="markdown-body">
        {html_body}
        </div>
    </body>
    </html>
    """
    
    styled_html_doc = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
        {pdf_css}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="markdown-body">
        {html_body}
        </div>
    </body>
    </html>
    """
    
    html_filename = f"{base_filename}.html"
    html_path = os.path.join(output_dir, html_filename)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(styled_html_web)

    # 2. Generate PDF
    pdf_filename = f"{base_filename}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    
    if pisa:
        with open(pdf_path, "wb") as f:
            # pisa needs the font to be available. 
            # We rely on the @font-face src url pointing to the local file in the container.
            pisa_status = pisa.CreatePDF(styled_html_doc, dest=f, encoding='utf-8')
        
        if pisa_status.err:
            print(f"Error generating PDF for article {article_id}: {pisa_status.err}")
    else:
        print(f"Skipping PDF generation for article {article_id}: xhtml2pdf not installed")

    # 3. Generate DOCX
    docx_filename = f"{base_filename}.docx"
    docx_path = os.path.join(output_dir, docx_filename)
    
    try:
        doc = Document()
        doc.add_heading(title, 0)
        
        new_parser = HtmlToDocx()
        # Parse the HTML body content. 
        new_parser.add_html_to_document(html_body, doc)
        
        doc.save(docx_path)
    except Exception as e:
        print(f"Error generating DOCX for article {article_id}: {e}")

    # 4. Generate Markdown
    md_filename = f"{base_filename}.md"
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}")

    return {
        "html": html_filename,
        "pdf": pdf_filename,
        "docx": docx_filename,
        "md": md_filename
    }
