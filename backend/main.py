from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ProcessPoolExecutor
import pdfplumber
import csv
import os
import shutil
import re
from converter import unicode_to_krutidev, krutidev_to_unicode

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Changed from .jsonl to .csv
DATABASE_FILE = "pdf_database.csv"
TEMP_PDF_FILE = "temp_uploaded.pdf"

progress_status = {
    "is_processing": False,
    "current_page": 0,
    "total_pages": 0,
    "message": "Idle"
}

def process_chunk(args):
    """Processes a small chunk of pages and formats them for CSV."""
    filepath, start_page, end_page = args
    chunk_results = []
    
    with pdfplumber.open(filepath) as pdf:
        for i in range(start_page, end_page):
            if i >= len(pdf.pages): break
            
            page = pdf.pages[i]
            text = page.extract_text(layout=True)
            
            if text:
                # Append each line as a CSV row: [page_number, text_line]
                for line in text.split('\n'):
                    if line.strip():
                        chunk_results.append([i + 1, line.strip()])
            
            page.flush_cache()
            
    return chunk_results

def process_raw_pdf(filepath: str):
    global progress_status
    progress_status = {"is_processing": True, "current_page": 0, "total_pages": 0, "message": "Warming up CPU cores..."}
    
    try:
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)
        progress_status["total_pages"] = total_pages
        progress_status["message"] = "Extracting raw text to CSV at high speed..."

        chunk_size = 20
        chunks = [(filepath, i, i + chunk_size) for i in range(0, total_pages, chunk_size)]
        
        # Open CSV file for writing
        with open(DATABASE_FILE, "w", encoding="utf-8", newline="") as db:
            writer = csv.writer(db)
            # Write Header Row
            writer.writerow(["page_number", "raw_text"])
            
            with ProcessPoolExecutor() as executor:
                for i, chunk_data in enumerate(executor.map(process_chunk, chunks)):
                    # Write all lines from this chunk into the CSV
                    if chunk_data:
                        writer.writerows(chunk_data)
                    
                    pages_completed = min((i + 1) * chunk_size, total_pages)
                    progress_status["current_page"] = pages_completed
                    db.flush()
                        
        progress_status["message"] = "Processing complete! Ready to search."
    except Exception as e:
        progress_status["message"] = f"Error: {str(e)}"
    finally:
        progress_status["is_processing"] = False
        if os.path.exists(filepath): 
            os.remove(filepath)

@app.post("/api/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    with open(TEMP_PDF_FILE, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    background_tasks.add_task(process_raw_pdf, TEMP_PDF_FILE)
    return {"message": "Processing started in background"}

@app.get("/api/progress")
def get_progress(): 
    return progress_status

@app.get("/api/convert")
def convert_text(text: str = ""):
    if not text:
        return {"kruti_text": ""}
    
    kruti_result = unicode_to_krutidev(text)
    return {"kruti_text": kruti_result}

@app.get("/api/search")
def search(query: str, father_name: str = ""):
    if not os.path.exists(DATABASE_FILE):
        return {"error": "No CSV database found. Please upload a PDF first."}

    # Kruti dev versions for lightning-fast pre-filtering
    k_query = unicode_to_krutidev(query)
    k_father = unicode_to_krutidev(father_name) if father_name else ""
    
    results = []
    
    with open(DATABASE_FILE, "r", encoding="utf-8") as db:
        reader = csv.reader(db)
        next(reader, None) # Skip header row
        
        for row_data in reader:
            if len(row_data) < 2: 
                continue
                
            page_num = row_data[0]
            row_text = row_data[1]
            
            # 1. FAST PRE-FILTER: Sirf wahi rows process karo jisme names exist karte hain
            if k_query in row_text and (not k_father or k_father in row_text):
                
                # 2. Convert to Hindi for splitting into exact columns
                hindi_row = krutidev_to_unicode(row_text)
                hindi_row = re.sub(r'(^|\s)ष', r'\1श', hindi_row)
                hindi_row = re.sub(r'(^|\s)ष्', r'\1श्', hindi_row)
                
                # 3. Split row into logical Columns (Voter Column & Relative Column)
                parts = re.split(r'\s*(पि\.|प\.|मा\.)\s*', hindi_row)
                
                voter_name_col = parts[0].strip() if parts else hindi_row
                voter_name_col = re.sub(r'^[\d\s\-\/]+', '', voter_name_col) # Remove serial numbers
                
                relation_type = parts[1].strip() if len(parts) >= 3 else ""
                relative_name_col = parts[2].strip() if len(parts) >= 3 else ""
                
                # 4. STRICT COLUMN CHECK:
                # Query strictly Voter Column mein honi chahiye
                if query in voter_name_col:
                    # Agar father name diya hai, toh wo strictly Relative Column mein hona chahiye
                    if not father_name or father_name in relative_name_col:
                        
                        results.append({
                            "page_number": int(page_num),
                            "voter_name": voter_name_col,
                            "relative_name": relative_name_col,
                            "relation_type": relation_type
                        })
                    
    return {"total_matches": len(results), "results": results}