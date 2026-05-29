import re
import os
import base64
import subprocess

def get_image_base64_uri(img_path):
    # Strip file:// prefix if present
    if img_path.startswith("file://"):
        img_path = img_path[7:]
        
    doc_dir = '/home/jchrisso/Documentos/Examen_GitHub_Actions/docs'
    workspace_dir = '/home/jchrisso/Documentos/Examen_GitHub_Actions'
    
    # Resolve relative paths
    resolved_path = img_path
    if not os.path.isabs(img_path):
        for base in [doc_dir, workspace_dir]:
            p = os.path.abspath(os.path.join(base, img_path))
            if os.path.exists(p):
                resolved_path = p
                break
                
    if os.path.exists(resolved_path):
        print(f"Embedding image: {resolved_path}")
        with open(resolved_path, 'rb') as f:
            data = f.read()
        encoded = base64.b64encode(data).decode('utf-8')
        # Determine mime type
        mime = "image/png"
        if resolved_path.lower().endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        elif resolved_path.lower().endswith(".gif"):
            mime = "image/gif"
        return f"data:{mime};base64,{encoded}"
    else:
        print(f"Warning: Image not found at {img_path} (Resolved to: {resolved_path})")
        return img_path

def md_to_html(md_content):
    html_lines = []
    lines = md_content.split('\n')
    
    in_code_block = False
    in_list = False
    in_ordered_list = False
    in_table = False
    table_header = True
    
    for line in lines:
        stripped = line.strip()
        
        # Code block toggle
        if stripped.startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                lang = stripped[3:].strip()
                html_lines.append(f'<pre><code class="language-{lang}">')
                in_code_block = True
            continue
            
        if in_code_block:
            # Escape HTML characters inside code block
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(escaped)
            continue

        # Close list tags if no longer in a list
        if in_list and not (stripped.startswith('* ') or stripped.startswith('- ') or stripped.startswith('    * ') or stripped.startswith('    - ')):
            html_lines.append('</ul>')
            in_list = False
            
        if in_ordered_list and not re.match(r'^\d+\.\s', stripped):
            html_lines.append('</ol>')
            in_ordered_list = False
            
        # Close table if no longer in a table
        if in_table and not stripped.startswith('|'):
            html_lines.append('</tbody></table>')
            in_table = False
            table_header = True

        # Headers
        if stripped.startswith('# '):
            html_lines.append(f'<h1>{stripped[2:]}</h1>')
        elif stripped.startswith('## '):
            html_lines.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('#### '):
            html_lines.append(f'<h4>{stripped[5:]}</h4>')
            
        # Horizontal Rule
        elif stripped == '---':
            html_lines.append('<hr/>')
            
        # Unordered list
        elif stripped.startswith('* ') or stripped.startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            content = stripped[2:]
            html_lines.append(f'  <li>{content}</li>')
            
        # Sub-list items (indented by 4 spaces)
        elif line.startswith('    * ') or line.startswith('    - '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            content = stripped[2:]
            html_lines.append(f'  <li style="margin-left: 20px;">{content}</li>')
            
        # Ordered list
        elif re.match(r'^\d+\.\s', stripped):
            if not in_ordered_list:
                html_lines.append('<ol>')
                in_ordered_list = True
            m = re.match(r'^\d+\.\s(.*)', stripped)
            content = m.group(1)
            html_lines.append(f'  <li>{content}</li>')
            
        # Tables
        elif stripped.startswith('|'):
            if not in_table:
                html_lines.append('<table>')
                in_table = True
                table_header = True
            
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            
            # Skip separator line (e.g. |:---|:---:|)
            if all(re.match(r'^:?-+:?$', c) for c in cells):
                continue
                
            if table_header:
                html_lines.append('<thead><tr>')
                for cell in cells:
                    html_lines.append(f'  <th>{cell}</th>')
                html_lines.append('</tr></thead><tbody>')
                table_header = False
            else:
                html_lines.append('<tr>')
                for cell in cells:
                    html_lines.append(f'  <td>{cell}</td>')
                html_lines.append('</tr>')
                
        # Empty line
        elif not stripped:
            html_lines.append('<br/>')
            
        # Normal paragraph
        else:
            html_lines.append(f'<p>{line}</p>')

    # Close any open tags
    if in_code_block:
        html_lines.append('</code></pre>')
    if in_list:
        html_lines.append('</ul>')
    if in_ordered_list:
        html_lines.append('</ol>')
    if in_table:
        html_lines.append('</tbody></table>')
        
    html_text = '\n'.join(html_lines)
    
    # Process inline formatting:
    # 1. Bold: **text** -> <strong>text</strong>
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    # 2. Inline code: `code` -> <code>code</code>
    html_text = re.sub(r'`(.*?)`', r'<code>\1</code>', html_text)
    
    # 3. Images with Base64 embedding: ![caption](path) -> img with base64 src
    def repl_img(match):
        caption = match.group(1)
        path = match.group(2)
        base64_uri = get_image_base64_uri(path)
        return f'<img src="{base64_uri}" alt="{caption}" /><div class="caption">{caption}</div>'
    
    html_text = re.sub(r'!\[(.*?)\]\((.*?)\)', repl_img, html_text)
    
    # 4. Links: [text](url) -> standard HTML links
    html_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html_text)
    
    return html_text

def run():
    doc_dir = '/home/jchrisso/Documentos/Examen_GitHub_Actions/docs'
    evidencias_dir = '/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias'
    
    md_path = os.path.join(doc_dir, 'Examen_GitHub_Actions_Enterprise.md')
    html_path = os.path.join(doc_dir, 'Examen_GitHub_Actions_Enterprise.html')
    odt_path = os.path.join(doc_dir, 'Examen_GitHub_Actions_Enterprise.odt')
    
    print(f"Reading {md_path}...")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    html_body = md_to_html(md_content)
    
    # Styled HTML Template
    html_full = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Liberation Sans', Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }}
  h1 {{ color: #1a365d; border-bottom: 2px solid #1a365d; padding-bottom: 8px; margin-top: 35px; font-size: 24px; }}
  h2 {{ color: #2b6cb0; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-top: 30px; font-size: 20px; }}
  h3 {{ color: #4a5568; margin-top: 25px; font-size: 16px; }}
  h4 {{ color: #718096; margin-top: 20px; font-size: 14px; font-style: italic; }}
  p {{ margin-bottom: 12px; font-size: 14px; text-align: justify; }}
  code {{ font-family: 'Courier New', Courier, monospace; background-color: #f7fafc; padding: 2px 4px; border-radius: 4px; font-size: 13px; }}
  pre {{ background-color: #f7fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 5px; overflow-x: auto; margin-bottom: 15px; }}
  pre code {{ background-color: transparent; padding: 0; font-size: 12px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 13px; }}
  th, td {{ border: 1px solid #cbd5e0; padding: 8px; text-align: left; }}
  th {{ background-color: #edf2f7; color: #2d3748; font-weight: bold; }}
  tr:nth-child(even) {{ background-color: #f8fafc; }}
  ul, ol {{ margin-bottom: 15px; padding-left: 20px; font-size: 14px; }}
  li {{ margin-bottom: 6px; }}
  img {{ max-width: 90%; height: auto; display: block; margin: 20px auto; border: 1px solid #cbd5e0; }}
  .caption {{ text-align: center; font-style: italic; color: #718096; font-size: 12px; margin-top: -10px; margin-bottom: 25px; }}
  hr {{ border: 0; border-top: 1px solid #cbd5e0; margin: 35px 0; }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    
    print(f"Writing {html_path}...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_full)
        
    # Perform LibreOffice conversions
    print("Converting HTML to ODT...")
    subprocess.run([
        'libreoffice', '--headless', 
        '--convert-to', 'odt', 
        html_path, 
        '--outdir', doc_dir
    ], check=True)
    
    print("Converting ODT to DOCX...")
    subprocess.run([
        'libreoffice', '--headless', 
        '--convert-to', 'docx', 
        odt_path, 
        '--outdir', evidencias_dir
    ], check=True)
    
    # We will also create a copy of the generated docx file under target names to satisfy all potential requests
    generated_docx = os.path.join(evidencias_dir, 'Examen_GitHub_Actions_Enterprise.docx')
    lab7_docx = os.path.join(evidencias_dir, 'lab7.docx')
    
    if os.path.exists(generated_docx):
        print(f"Success! Generated: {generated_docx} ({os.path.getsize(generated_docx)} bytes)")
        # Copy to lab7.docx in case the user prefers that name
        subprocess.run(['cp', generated_docx, lab7_docx], check=True)
        print(f"Copied to: {lab7_docx}")
    else:
        print("Failed to generate DOCX file.")

if __name__ == '__main__':
    run()
