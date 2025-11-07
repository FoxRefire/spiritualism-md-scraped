#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path

# Allan Kardec (カルデック) books
ALLAN_BASE_URL = "https://www.asahi-net.or.jp/~lv2k-sgw/spir/search/big3/allan/"
ALLAN_BOOKS = [
    ("soul.html", "霊の書", "soul"),
    ("psychic.html", "霊媒の書", "psychic"),
    ("dialog.html", "霊との対話-天国と地獄", "dialog"),
    ("heavenHell2.html", "天国と地獄Ⅱ", "heaven_hell_2"),
]

# Stainton Moses (モーゼス) books
STAINTON_BASE_URL = "https://www.asahi-net.or.jp/~lv2k-sgw/spir/search/big3/"
STAINTON_BOOKS = [
    ("staintonU.html", "霊訓(完訳・上)", "stainton_upper"),
    ("staintonL.html", "霊訓(完訳・下)", "stainton_lower"),
]

def html_to_markdown(html_content):
    """Convert HTML content to Markdown format"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main content div
    content_div = soup.find('div', id='content')
    if not content_div:
        return ""
    
    # Get the inner HTML as string
    content_html = str(content_div)
    
    # Remove HTML comments
    content_html = re.sub(r'<!--.*?-->', '', content_html, flags=re.DOTALL)
    
    # Replace <br> and <br /> with newlines before parsing
    content_html = re.sub(r'<br\s*/?>', '\n', content_html)
    
    # Parse the modified HTML
    soup2 = BeautifulSoup(content_html, 'html.parser')
    content_div2 = soup2.find('div', id='content')
    
    if not content_div2:
        return ""
    
    markdown_lines = []
    
    def process_node(node):
        """Process a node recursively and return markdown text"""
        if isinstance(node, str):
            text = node.strip()
            return text if text else ""
        
        if node.name is None:
            return ""
        
        result_parts = []
        
        # Handle font tags with blue color as headings
        if node.name == 'font':
            color = node.get('color', '').lower()
            size = node.get('size', '')
            text = node.get_text().strip()
            if text:
                # Check for blue colors (various shades)
                if color in ['#0064ff', '#0064ff', '#0066ff', '#0066ff', '#0000ff', '#0000ff']:
                    # Determine heading level
                    # Priority: 1) Check if text contains 節 (section) -> level 2
                    #           2) Check font size -> size="3" or larger -> level 1
                    #           3) Default -> level 2
                    if '節' in text:
                        # Section: level 2
                        return f"\n## {text}\n"
                    elif size == '3' or size == '4' or size == '5':
                        # Large font: level 1
                        return f"\n# {text}\n"
                    else:
                        # Default: level 2
                        return f"\n## {text}\n"
                return text
            return ""
        
        # Handle bold
        if node.name in ['b', 'strong']:
            text = node.get_text().strip()
            return f"**{text}**" if text else ""
        
        # Handle center
        if node.name == 'center':
            text = node.get_text().strip()
            return f"\n{text}\n" if text else ""
        
        # Handle headings
        if node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = node.get_text().strip()
            if text:
                level = int(node.name[1])
                return f"\n{'#' * level} {text}\n"
            return ""
        
        # For other elements, process children
        for child in node.children:
            child_result = process_node(child)
            if child_result:
                result_parts.append(child_result)
        
        return ''.join(result_parts)
    
    # Process the content
    markdown_text = process_node(content_div2)
    
    # Split into lines and clean up
    lines = markdown_text.split('\n')
    markdown_lines = []
    
    # First pass: detect table of contents
    # A TOC is typically a sequence of headings with little or no content between them
    heading_indices = []
    content_lengths = []  # Length of content after each heading
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('#') or re.match(r'^第[０-９一二三四五六七八九十]+[部章巻節]', line_stripped):
            heading_indices.append(i)
            # Count content length after this heading (until next heading or end)
            content_len = 0
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                if next_line.startswith('#') or re.match(r'^第[０-９一二三四五六七八九十]+[部章巻節]', next_line):
                    break
                content_len += len(next_line)
            content_lengths.append(content_len)
    
    # Identify TOC section: consecutive headings with minimal content
    toc_start = None
    toc_end = None
    if len(heading_indices) >= 3:
        consecutive_count = 0
        for i in range(len(heading_indices) - 1):
            if content_lengths[i] < 50:  # Less than 50 characters after heading
                consecutive_count += 1
                if consecutive_count >= 3 and toc_start is None:
                    toc_start = heading_indices[i - 2]  # Start 2 headings back
            else:
                if consecutive_count >= 3 and toc_end is None:
                    toc_end = heading_indices[i]
                consecutive_count = 0
        
        # If we found a TOC start but no end, check if there's substantial content later
        if toc_start is not None and toc_end is None:
            # Look for first heading with substantial content after it
            for i in range(len(heading_indices)):
                if heading_indices[i] > toc_start and content_lengths[i] > 100:
                    toc_end = heading_indices[i]
                    break
    
    # Second pass: process lines
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            # Empty line - only add if previous line wasn't empty
            if markdown_lines and markdown_lines[-1]:
                markdown_lines.append('')
            continue
        
        # Check if this line is in TOC section
        is_in_toc = (toc_start is not None and toc_end is not None and 
                     toc_start <= i < toc_end)
        
        # Check if this is a heading (starts with #)
        if line_stripped.startswith('#'):
            if is_in_toc:
                # In TOC: remove heading markers, treat as plain text
                heading_text = re.sub(r'^#+\s*', '', line_stripped)
                markdown_lines.append(heading_text)
            else:
                # Not in TOC: adjust heading level based on content
                # Extract heading text (remove # markers)
                heading_text = re.sub(r'^#+\s*', '', line_stripped)
                
                # Determine correct heading level
                if re.match(r'^第[０-９一二三四五六七八九十]+[部章巻]', heading_text):
                    # Chapter/Part/Volume: level 1
                    final_heading = f"# {heading_text}"
                elif re.match(r'^第[０-９一二三四五六七八九十]+節', heading_text):
                    # Section: level 2
                    final_heading = f"## {heading_text}"
                else:
                    # Keep original heading level
                    final_heading = line_stripped
                
                if markdown_lines and markdown_lines[-1] and not markdown_lines[-1].startswith('#'):
                    markdown_lines.append('')
                markdown_lines.append(final_heading)
                # Ensure blank line after heading
                if not (markdown_lines and markdown_lines[-1] == ''):
                    markdown_lines.append('')
        # Check for heading patterns (第○部、第○章など) that might not have been detected
        elif re.match(r'^第[０-９一二三四五六七八九十]+[部章巻節]', line_stripped):
            if is_in_toc:
                # In TOC: treat as plain text
                markdown_lines.append(line_stripped)
            else:
                # Not in TOC: format as heading
                # Determine heading level: 章/部/巻 -> level 1, 節 -> level 2
                if markdown_lines and markdown_lines[-1] and not markdown_lines[-1].startswith('#'):
                    markdown_lines.append('')
                
                # Check if it's a section (節) or chapter (章/部/巻)
                if '節' in line_stripped:
                    # Section: level 2
                    markdown_lines.append(f"## {line_stripped}")
                else:
                    # Chapter/Part/Volume: level 1
                    markdown_lines.append(f"# {line_stripped}")
                markdown_lines.append('')
        else:
            markdown_lines.append(line_stripped)
    
    # Join lines
    markdown = '\n'.join(markdown_lines)
    
    # Clean up excessive blank lines (more than 2 consecutive)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # Remove any "Start content" text
    markdown = re.sub(r'^Start content\s*\n?', '', markdown, flags=re.MULTILINE)
    
    return markdown.strip()

def scrape_book(base_url, filename, title, output_name, output_dir):
    """Scrape a single book"""
    url = f"{base_url}{filename}"
    print(f"Scraping {title} from {url}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        # Convert to markdown
        markdown_content = html_to_markdown(response.text)
        
        if markdown_content:
            output_file = output_dir / f"{output_name}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Saved {title} to {output_file}")
            return True
        else:
            print(f"Failed to scrape {title}: No content found")
            return False
    except Exception as e:
        print(f"Error scraping {title}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Create output directories
    allan_dir = Path("allan_kardec_volumes")
    allan_dir.mkdir(exist_ok=True)
    
    stainton_dir = Path("stainton_moses_volumes")
    stainton_dir.mkdir(exist_ok=True)
    
    # Scrape Allan Kardec books
    print("=" * 60)
    print("Scraping Allan Kardec (アラン・カルデック) books...")
    print("=" * 60)
    for filename, title, output_name in ALLAN_BOOKS:
        scrape_book(ALLAN_BASE_URL, filename, title, output_name, allan_dir)
    
    # Scrape Stainton Moses books
    print("\n" + "=" * 60)
    print("Scraping Stainton Moses (ステイントン・モーゼス) books...")
    print("=" * 60)
    for filename, title, output_name in STAINTON_BOOKS:
        scrape_book(STAINTON_BASE_URL, filename, title, output_name, stainton_dir)
    
    print("\n" + "=" * 60)
    print("Scraping completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

