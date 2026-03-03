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

DATABASE_FILE = "pdf_database.csv"
TEMP_PDF_FILE = "temp_uploaded.pdf"

progress_status = {
    "is_processing": False,
    "current_page": 0,
    "total_pages": 0,
    "message": "Idle"
}

COLUMN_PATTERNS = {
    'serial': ['fu-dz- la[;k', 'fu-dz la[;k', 'la[;k'],
    'name': ['edku la[;k', 'edku la['],
    'father_name': ['fuokZpd dk uke', 'fuokZpd dk uke'],
    'relation': ['lEcU/k'],
    'relative_name': ['lEcU/kh dk uke'],
    'age': ['fyax'],
    'gender': ['vk;q'],
    'voter_id': ['QksVks igpku i= la[;k']
}

HINDI_GENDER = {
    'e-': 'F',
    'iq-': 'M', 
    'fi-': 'M',
    'nkl': 'F',
    'i-': 'F',  # Husband relation marker
}

def detect_columns_from_text(text_lines):
    columns = {}
    for line in text_lines:
        line_lower = line.strip().lower()
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
    line = line.strip()
    if not line:
        return None
    
    match = re.match(r'^(\d+)\s+(.+)$', line)
    if not match:
        return None
    
    serial = match.group(1).strip()
    rest = match.group(2).strip()
    
    if not rest or len(rest) < 2:
        return None
    
    # Handle "i-" relation pattern (husband relation)
    # Example: "deys'k i- uUnyky e- 30 UP/123"
    # Should be: name="deys'k", relation="i-", relative_name="uUnyky", gender="F", age="30", voter_id="UP/123"
    i_pattern_match = re.match(r'^(.+?)\s+i-\s+(.+)$', rest)
    if i_pattern_match:
        name_part = i_pattern_match.group(1).strip()
        relative_part = i_pattern_match.group(2).strip()
        
        parts = name_part.split()
        
        result = {
            'serial': serial,
            'name': '',
            'father_name': '',
            'relation': 'i-',  # Set i- as relation
            'relative_name': '',
            'age': '',
            'gender': 'F',  # i- relation means female (wife)
            'voter_id': ''
        }
        
        # Collect name
        collected_name = []
        for part in parts:
            collected_name.append(part)
        
        result['name'] = ' '.join(collected_name)
        
        # Parse relative_part to extract: relative_name, age, gender, voter_id
        rel_parts = relative_part.split()
        
        for part in rel_parts:
            if part in HINDI_GENDER:
                result['gender'] = HINDI_GENDER[part]
                if result['relation'] != 'i-':
                    result['relation'] = part
            elif re.match(r'^\d+$', part):
                result['age'] = part
            else:
                if not result['relative_name']:
                    result['relative_name'] = part
                else:
                    if not result['voter_id']:
                        result['voter_id'] = part
                    else:
                        result['voter_id'] += ' ' + part
        
        if not result['name']:
            return None
        
        return result
    
    # Original parsing for other cases
    parts = rest.split()
    
    result = {
        'serial': serial,
        'name': '',
        'father_name': '',
        'relation': '',
        'relative_name': '',
        'age': '',
        'gender': '',
        'voter_id': ''
    }
    
    if len(parts) == 0:
        return None
    
    collected_name = []
    collected_father = []
    i = 0
    
    # Collect name
    while i < len(parts):
        part = parts[i]
        
        if part in HINDI_GENDER:
            result['gender'] = HINDI_GENDER[part]
            result['relation'] = part
            i += 1
            break
        
        if re.match(r'^\d+$', part):
            result['age'] = part
            i += 1
            break
        
        collected_name.append(part)
        i += 1
    
    result['name'] = ' '.join(collected_name)
    
    # Collect father's name
    while i < len(parts):
        part = parts[i]
        
        if part in HINDI_GENDER:
            result['gender'] = HINDI_GENDER[part]
            result['relation'] = part
            i += 1
            break
        
        if re.match(r'^\d+$', part):
            result['age'] = part
            i += 1
            break
        
        collected_father.append(part)
        i += 1
    
    result['father_name'] = ' '.join(collected_father)
    
    # Get remaining fields
    while i < len(parts):
        part = parts[i]
        
        if part in HINDI_GENDER:
            result['gender'] = HINDI_GENDER[part]
            result['relation'] = part
        elif re.match(r'^\d+$', part):
            result['age'] = part
        else:
            if not result['voter_id']:
                result['voter_id'] = part
            else:
                result['voter_id'] += ' ' + part
        
        i += 1
    
    if not result['name']:
        return None
    
    return result


def process_chunk(args):
    """Process a single page - returns list of parsed records"""
    filepath, page_num = args
    chunk_results = []
    
    with pdfplumber.open(filepath) as pdf:
        if page_num >= len(pdf.pages):
            return chunk_results
        
        page = pdf.pages[page_num]
        text = page.extract_text(layout=True)
        
        if text:
            lines = text.split('\n')
            
            columns_detected = {}
            header_candidates = []
            
            for line in lines:
                line_upper = line.upper()
                if any(kw in line_upper for kw in ['LA[;K', 'FU-DZ', 'EDKU', 'FUOKZPD', 'LEC', 'FYAX', 'VK;Q', 'QKSVKS']):
                    header_candidates.append(line)
                    columns_detected = detect_columns_from_text(header_candidates)
                    if columns_detected:
                        break
            
            for line in lines:
                parsed = parse_data_row(line, columns_detected)
                if parsed:
                    parsed['page_number'] = page_num + 1
                    chunk_results.append(parsed)
        
        page.flush_cache()
    
    return chunk_results


def process_structured_pdf(filepath):
    """Process PDF file page by page and save to CSV"""
    global progress_status
    progress_status = {"is_processing": True, "current_page": 0, "total_pages": 0, "message": "Warming up..."}
    
    try:
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)
        progress_status["total_pages"] = total_pages
        progress_status["message"] = "Extracting structured data..."

        # Process page by page (one at a time)
        page_tasks = [(filepath, i) for i in range(total_pages)]
        
        with open(DATABASE_FILE, "w", encoding="utf-8", newline="") as db:
            writer = csv.writer(db)
            writer.writerow(["serial_number", "name", "father_name", "relation", "relative_name", "age", "gender", "voter_id", "page_number"])
            
            with ProcessPoolExecutor() as executor:
                for i, chunk_data in enumerate(executor.map(process_chunk, page_tasks)):
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
                    
                    # Update progress - one page completed
                    progress_status["current_page"] = i + 1
                    db.flush()
                        
        progress_status["message"] = "Processing complete!"
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
def search(query: str, relative_name: str = ""):
    """
    Search voter list.
    - query: Search in voter name column
    - relative_name: Search in father/husband name column
    """
    if not os.path.exists(DATABASE_FILE):
        return {"error": "No CSV database found. Please upload a PDF first."}

    # Convert search terms to Kruti Dev for searching
    k_query = unicode_to_krutidev(query) if query else ""
    k_relative = unicode_to_krutidev(relative_name) if relative_name else ""
    
    results = []
    
    with open(DATABASE_FILE, "r", encoding="utf-8") as db:
        reader = csv.reader(db)
        header = next(reader, None)
        
        is_structured = len(header) >= 5 if header else False
        
        if is_structured:
            # New structured format: search in specific columns
            for row_data in reader:
                if len(row_data) < 9:
                    continue
                
                voter_name = row_data[1]
                father_name = row_data[2]
                page_num = row_data[8]
                
                name_match = not k_query or k_query in voter_name
                relative_match = not k_relative or k_relative in father_name
                
                if name_match and relative_match:
                    unicode_name = krutidev_to_unicode(voter_name)
                    unicode_father = krutidev_to_unicode(father_name)
                    unicode_relation = krutidev_to_unicode(row_data[3]) if row_data[3] else ""
                    unicode_relative = krutidev_to_unicode(row_data[4]) if row_data[4] else ""
                    unicode_voter_id = krutidev_to_unicode(row_data[7]) if row_data[7] else ""
                    
                    results.append({
                        "page_number": int(page_num) if page_num else 0,
                        "serial_number": row_data[0],
                        "voter_name": unicode_name,
                        "father_name": unicode_father,
                        "relation": unicode_relation,
                        "relative_name": unicode_relative,
                        "age": row_data[5],
                        "gender": row_data[6],
                        "voter_id": unicode_voter_id
                    })
        else:
            # Old raw format
            for row_data in reader:
                if len(row_data) < 2: 
                    continue
                    
                page_num = row_data[0]
                row_text = row_data[1]
                
                if k_query in row_text and (not k_relative or k_relative in row_text):
                    hindi_row = krutidev_to_unicode(row_text)
                    hindi_row = re.sub(r'(^|\s)ष', r'\1श', hindi_row)
                    hindi_row = re.sub(r'(^|\s)ष्', r'\1श्', hindi_row)
                    
                    parts = re.split(r'\s*(पि\.|प\.|मा\.)\s*', hindi_row)
                    
                    voter_name_col = parts[0].strip() if parts else hindi_row
                    voter_name_col = re.sub(r'^[\d\s\-\/]+', '', voter_name_col)
                    
                    relation_type = parts[1].strip() if len(parts) >= 3 else ""
                    relative_name_col = parts[2].strip() if len(parts) >= 3 else ""
                    
                    query_match = not query or query in voter_name_col
                    relative_match = not relative_name or relative_name in relative_name_col
                    
                    if query_match and relative_match:
                        results.append({
                            "page_number": int(page_num),
                            "voter_name": voter_name_col,
                            "relative_name": relative_name_col,
                            "relation_type": relation_type
                        })
                        
    return {"total_matches": len(results), "results": results}
