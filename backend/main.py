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

# Structured CSV file
DATABASE_FILE = "pdf_database.csv"
TEMP_PDF_FILE = "temp_uploaded.pdf"

progress_status = {
    "is_processing": False,
    "current_page": 0,
    "total_pages": 0,
    "message": "Idle"
}

# Column header patterns in Kruti Dev
COLUMN_PATTERNS = {
    'serial': ['fu-dz- la[;k', 'fu-dz la[;k', 'la[;k', 'serial'],
    'name': ['edku la[;k', 'edku la[', 'name', 'vuq'],
    'father_name': ['fuokZpd dk uke', 'fuokZpd dk uke', 'father'],
    'relation': ['lEcU/k', 'lEcU/k'],
    'relative_name': ['lEcU/kh dk uke', 'lEcU/kh dk uke'],
    'age': ['fyax', 'age'],
    'gender': ['vk;q', 'gender'],
    'voter_id': ['QksVks igpku i= la[;k', 'voter id']
}


def detect_columns_from_text(text_lines):
    """Detect column positions from header row."""
    columns = {}
    
    for line in text_lines:
        line_lower = line.strip().lower()
        
        # Check each column pattern
        for col_name, patterns in COLUMN_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in line_lower or pattern in line:
                    pos = line.find(pattern)
                    if pos >= 0 and col_name not in columns:
                        columns[col_name] = pos
        
        if len(columns) >= 3:
            break
    
    return columns


def parse_data_row(line, columns_detected):
    """Parse a single data row based on detected columns."""
    line = line.strip()
    if not line:
        return None
    
    # Try to match data row pattern - starts with serial number (digit or unicode digit)
    match = re.match(r'^\s*(\d+)\s+(.+)', line)
    if not match:
        # Try unicode digits (Hindi digits)
        match = re.match(r'^\s*([à-æ])\s+(.+)', line)
    
    if not match:
        return None
    
    serial = match.group(1).strip()
    rest = match.group(2).strip()
    
    if not rest:
        return None
    
    # Split remaining data by whitespace
    parts = rest.split()
    
    result = {
        'serial': serial,
        'name': '',
        'father_name': '',
        'age': '',
        'gender': '',
        'voter_id': ''
    }
    
    if len(parts) >= 1:
        result['name'] = parts[0]
    if len(parts) >= 2:
        # Check if it's a number (age) or name
        if re.match(r'^\d+$', parts[1]):
            result['age'] = parts[1]
        else:
            result['father_name'] = parts[1]
    if len(parts) >= 3:
        if re.match(r'^\d+$', parts[2]):
            result['age'] = parts[2]
        else:
            result['father_name'] = parts[2]
    if len(parts) >= 4:
        # Check for gender (M/F or unicode)
        if parts[3].upper() in ['M', 'F', 'À', 'Á', 'Â', 'Ã', 'º']:
            result['gender'] = parts[3]
        else:
            result['father_name'] = parts[3]
    if len(parts) >= 5:
        result['voter_id'] = parts[4]
    
    return result


def process_chunk(args):
    """Processes a small chunk of pages and extracts structured data."""
    filepath, start_page, end_page = args
    chunk_results = []
    
    with pdfplumber.open(filepath) as pdf:
        for i in range(start_page, end_page):
            if i >= len(pdf.pages): break
            
            page = pdf.pages[i]
            text = page.extract_text(layout=True)
            
            if text:
                lines = text.split('\n')
                
                # First pass: detect columns from header lines
                columns_detected = {}
                header_candidates = []
                
                for line in lines:
                    line_upper = line.upper()
                    # Check for column header indicators
                    if any(kw in line_upper for kw in ['LA[;K', 'FU-DZ', 'EDKU', 'FUOKZPD', 'LEC', 'FYAX', 'VK;Q', 'QKSVKS']):
                        header_candidates.append(line)
                        columns_detected = detect_columns_from_text(header_candidates)
                        if columns_detected:
                            break
                
                # Second pass: extract data rows
                for line in lines:
                    parsed = parse_data_row(line, columns_detected)
                    if parsed:
                        parsed['page_number'] = i + 1
                        chunk_results.append(parsed)
            
            page.flush_cache()
    
    return chunk_results


def process_structured_pdf(filepath: str):
    """Process PDF and extract structured data to CSV."""
    global progress_status
    progress_status = {"is_processing": True, "current_page": 0, "total_pages": 0, "message": "Warming up CPU cores..."}
    
    try:
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)
        progress_status["total_pages"] = total_pages
        progress_status["message"] = "Extracting structured data to CSV..."

        chunk_size = 20
        chunks = [(filepath, i, i + chunk_size) for i in range(0, total_pages, chunk_size)]
        
        # Open CSV file for writing structured data
        with open(DATABASE_FILE, "w", encoding="utf-8", newline="") as db:
            writer = csv.writer(db)
            # Write structured header row
            writer.writerow(["serial_number", "name", "father_name", "relation", "relative_name", "age", "gender", "voter_id", "page_number"])
            
            with ProcessPoolExecutor() as executor:
                for i, chunk_data in enumerate(executor.map(process_chunk, chunks)):
                    # Write all parsed records from this chunk
                    for record in chunk_data:
                        writer.writerow([
                            record.get('serial', ''),
                            record.get('name', ''),
                            record.get('father_name', ''),
                            record.get('relation', ''),
                            record.get('relative_name', ''),
                            record.get('age', ''),
                            record.get('gender', ''),
                            record.get('voter_id', ''),
                            record.get('page_number', '')
                        ])
                    
                    pages_completed = min((i + 1) * chunk_size, total_pages)
                    progress_status["current_page"] = pages_completed
                    db.flush()
                        
        progress_status["message"] = "Processing complete! Structured data saved."
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
    background_tasks.add_task(process_structured_pdf, TEMP_PDF_FILE)
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
        header = next(reader, None)
        
        # Check if it's the new structured format (9 columns) or old format (2 columns)
        is_structured = len(header) >= 5 if header else False
        
        if is_structured:
            # New structured format: serial_number, name, father_name, relation, relative_name, age, gender, voter_id, page_number
            for row_data in reader:
                if len(row_data) < 9:
                    continue
                
                name = row_data[1]
                father = row_data[2]
                page_num = row_data[8]
                
                # Search in name column
                if k_query in name:
                    if not father_name or k_father in father:
                        results.append({
                            "page_number": int(page_num) if page_num else 0,
                            "serial_number": row_data[0],
                            "name": name,
                            "father_name": father,
                            "relation": row_data[3],
                            "relative_name": row_data[4],
                            "age": row_data[5],
                            "gender": row_data[6],
                            "voter_id": row_data[7]
                        })
        else:
            # Old raw format: page_number, raw_text
            for row_data in reader:
                if len(row_data) < 2: 
                    continue
                    
                page_num = row_data[0]
                row_text = row_data[1]
                
                # 1. FAST PRE-FILTER
                if k_query in row_text and (not k_father or k_father in row_text):
                    
                    # 2. Convert to Hindi for splitting into exact columns
                    hindi_row = krutidev_to_unicode(row_text)
                    hindi_row = re.sub(r'(^|\s)ष', r'\1श', hindi_row)
                    hindi_row = re.sub(r'(^|\s)ष्', r'\1श्', hindi_row)
                    
                    # 3. Split row into logical Columns
                    parts = re.split(r'\s*(पि\.|प\.|मा\.)\s*', hindi_row)
                    
                    voter_name_col = parts[0].strip() if parts else hindi_row
                    voter_name_col = re.sub(r'^[\d\s\-\/]+', '', voter_name_col)
                    
                    relation_type = parts[1].strip() if len(parts) >= 3 else ""
                    relative_name_col = parts[2].strip() if len(parts) >= 3 else ""
                    
                    # 4. STRICT COLUMN CHECK
                    if query in voter_name_col:
                        if not father_name or father_name in relative_name_col:
                            
                            results.append({
                                "page_number": int(page_num),
                                "voter_name": voter_name_col,
                                "relative_name": relative_name_col,
                                "relation_type": relation_type
                            })
                    
    return {"total_matches": len(results), "results": results}
