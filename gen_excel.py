import os
import sys
import email
from email import policy
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from PIL import Image
import io
from paddleocr import PaddleOCR, draw_ocr
import matplotlib.pyplot as plt
from pdf2image import convert_from_path
import numpy as np
from tqdm import tqdm

# Initialize the PaddleOCR model
ocr = PaddleOCR(det_model_dir='E:/models/det', 
                rec_model_dir='E:/models/rec', 
                use_angle_cls=True, 
                use_gpu=True)

def extract_html_from_mhtml(mhtml_path):
    """
    Extracts the HTML content from an MHTML file.
    """
    try:
        with open(mhtml_path, 'rb') as file:
            msg = email.message_from_binary_file(file, policy=policy.default)
        
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='ignore')
    except Exception as e:
        print(f"Error reading MHTML file: {e}")
    
    return None

def parse_table(html_content):
    """
    Parses the HTML content to extract article metadata.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    
    if not table:
        print("No table found in the HTML content.")
        return []
    
    data = []
    for row in table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            continue
        
        title = cells[0].get_text(strip=True)
        date = cells[1].get_text(strip=True)
        
        data.append({
            'Article Title': title,
            'Date': date,
            'Image Preview': '',
            'Content': ''
        })
    
    return data

def extract_text_and_images_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PaddleOCR and saves the first page as a preview image.
    Also computes and prints the average OCR confidence for the PDF.
    """
    text = ""
    image_path = ""
    all_confidences = []
    
    try:
        pages = convert_from_path(pdf_path, dpi=200)
        
        for i, page in enumerate(pages):
            page_np = np.array(page)
            result = ocr.ocr(page_np, cls=True)
            
            if result and len(result) > 0:
                for line in result[0]:
                    text += line[1][0] + "\n"
                    all_confidences.append(line[1][1])
            
            if i == 0:
                image_path = pdf_path.replace(".pdf", "_preview.jpg")
                page.save(image_path, "JPEG")
                
    except Exception as e:
        print(f"Error processing PDF '{pdf_path}': {e}")
    
    if all_confidences:
        avg_confidence = sum(all_confidences) / len(all_confidences)
        print(f"OCR Accuracy for '{pdf_path}': {avg_confidence:.2%}")
    else:
        print(f"No OCR results for '{pdf_path}'")
    
    return text.strip(), image_path

def process_pdf_for_entry(entry, pdf_path):
    """
    Processes a PDF file for a specific article entry.
    Returns updated entry with content and image preview.
    """
    updated_entry = entry.copy()  # Create a copy to avoid modifying the original directly
    
    if pdf_path and os.path.exists(pdf_path):
        text, image = extract_text_and_images_from_pdf(pdf_path)
        updated_entry['Content'] = text
        updated_entry['Image Preview'] = image
    else:
        updated_entry['Content'] = "No content available (PDF missing)."
        updated_entry['Image Preview'] = ""
        
    return updated_entry

def split_and_save_to_markdown(data, pdf_files, pdf_folder, year):
    """
    Splits articles into Markdown files with ~30 articles each and generates markdown only.
    Does not modify the original data.
    """
    articles_per_file = 30
    total_articles = len(data)
    # Calculate the required number of files
    num_files = (total_articles + articles_per_file - 1) // articles_per_file
    
    for file_num in range(num_files):
        start_idx = file_num * articles_per_file
        end_idx = min((file_num + 1) * articles_per_file, total_articles)
        
        if start_idx >= total_articles:
            break
            
        md_content = f"# Articles Compilation {year} - Part {file_num + 1}\n\n"
        md_file_path = os.path.join(pdf_folder, f"articles_{year}_part_{file_num + 1}.md")
        
        for idx in range(start_idx, end_idx):
            entry = data[idx]
            
            md_content += f"## {entry['Article Title']}\n\n"
            md_content += f"**Date:** {entry['Date']}\n\n"
            md_content += "### Content\n\n"
            
            if entry['Content']:
                md_content += f"{entry['Content']}\n\n"
            else:
                md_content += "No content available.\n\n"
                
            md_content += "---\n\n"
        
        try:
            with open(md_file_path, 'w', encoding='utf-8') as md_file:
                md_file.write(md_content)
            print(f"Saved Markdown content to '{md_file_path}'")
        except Exception as e:
            print(f"Error saving Markdown file '{md_file_path}': {e}")

def match_articles_with_pdfs(data, pdf_folder, year):
    """
    Matches articles with PDFs, processes PDF content, and returns updated data.
    Also saves markdown files.
    """
    pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf')])
    processed_data = []
    
    for idx, entry in enumerate(tqdm(data, desc="Processing articles", unit="article")):
        pdf_path = None
        
        # Try to find a matching PDF file
        if idx < len(pdf_files):
            pdf_path = os.path.join(pdf_folder, pdf_files[idx])
            pdf_filename = pdf_files[idx]
        else:
            pdf_filename = ""
        
        # Calculate which markdown file this entry will be in
        markdown_file_number = (idx // 30) + 1
        
        # Process PDF content for this entry
        updated_entry = process_pdf_for_entry(entry, pdf_path)
        
        # Add PDF filename and markdown file number to the entry
        updated_entry['PDF Filename'] = pdf_filename
        updated_entry['Markdown File'] = f"articles_{year}_part_{markdown_file_number}.md"
        
        # Get page count for the PDF if it exists
        if pdf_path and os.path.exists(pdf_path):
            try:
                pages = convert_from_path(pdf_path)
                updated_entry['Pages'] = len(pages)
            except Exception:
                updated_entry['Pages'] = 0
        else:
            updated_entry['Pages'] = 0
            
        processed_data.append(updated_entry)
    
    # Save to markdown files after all data has been processed
    split_and_save_to_markdown(processed_data, pdf_files, pdf_folder, year)
    
    return processed_data

def save_to_excel(data, output_path):
    """
    Saves the extracted data to an Excel file with selected fields only.
    """
    if not data:
        print("No data to save.")
        return
    
    # Create a new list with only the required fields
    excel_data = []
    for entry in data:
        excel_entry = {
            'Article Title': entry.get('Article Title', ''),
            'Date': entry.get('Date', ''),
            'Pages': entry.get('Pages', 0),
            'Image Name': os.path.basename(entry.get('Image Preview', '')) if entry.get('Image Preview') else '',
            'Markdown File': entry.get('Markdown File', '')
        }
        excel_data.append(excel_entry)
    
    # Convert to DataFrame and save to Excel    
    df = pd.DataFrame(excel_data)
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        print(f"Data successfully saved to '{output_path}'.")
        print(f"Total articles saved: {len(data)}")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

def main():
    """
    Main function to process MHTML and PDFs for a specific year.
    """
    year = "1997"  # You can modify this or make it a parameter
    mhtml_path = f"F:/data/1983-1997/{year}/{year}.mhtml"
    pdf_folder = f"F:/data/1983-1997/{year}/"
    
    if not os.path.isfile(mhtml_path):
        print(f"The file '{mhtml_path}' does not exist.")
        sys.exit(1)
    
    html_content = extract_html_from_mhtml(mhtml_path)
    if not html_content:
        sys.exit(1)
    
    articles_data = parse_table(html_content)
    if not articles_data:
        sys.exit(1)
    
    # Process PDFs and get enriched data
    enriched_data = match_articles_with_pdfs(articles_data, pdf_folder, year)
    save_to_excel(enriched_data, output_path=f"F:/data/1983-1997/{year}/{year}articles.xlsx")

if __name__ == "__main__":
    main()