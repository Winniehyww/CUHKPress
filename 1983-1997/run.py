import os
import shutil
import re

def group_pdfs_by_year(source_folder):
    if not os.path.exists(source_folder):
        print("The specified folder does not exist.")
        return
    
    files = [f for f in os.listdir(source_folder) if f.endswith(".pdf")]
    year_pattern = re.compile(r"(\d{4})")
    
    for file in files:
        match = year_pattern.search(file)
        if match:
            year = match.group(1)
        else:
            year = "Others"
        
        year_folder = os.path.join(source_folder, year)
        os.makedirs(year_folder, exist_ok=True)
        
        source_path = os.path.join(source_folder, file)
        destination_path = os.path.join(year_folder, file)
        shutil.move(source_path, destination_path)
        print(f"Moved {file} to {year}/")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing PDF files: ")
    group_pdfs_by_year(folder_path)
