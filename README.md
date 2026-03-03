# Hindi PDF Search Portal (BLO Search Portal)

A full-stack application for searching and indexing Hindi PDF documents (Voter List PDFs) with KrutiDev to Unicode conversion capabilities.

## Features

- Hindi text recognition from PDF files
- Full-text search functionality
- Backend API for PDF processing
- Frontend user interface built with Next.js

## Tech Stack

- **Frontend**: Next.js, React
- **Backend**: Python (FastAPI)
- **OCR**: Hindi KrutiDev to Unicode conversion
- **Database**: CSV-based text indexing
- **Search**: Fast bilingual search (Hindi Unicode & KrutiDev)

## Getting Started

### Prerequisites

- Node.js (v18+)
- Python (v3.8+)
- pip

### Installation

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Backend

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (Windows)
python -m venv venv

# Activate the virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn main:app --reload
```

> **Note**: For macOS/Linux, use `venv/bin/activate` instead of `venv\Scripts\activate`

## Project Structure

```
.
├── backend/
│   ├── venv/               # Virtual environment (created by python -m venv venv)
│   ├── converter.py        # KrutiDev to Unicode conversion
│   ├── main.py             # FastAPI backend server
│   ├── requirements.txt    # Python dependencies
│   └── pdf_database.csv    # Indexed PDF data (generated after upload)
├── frontend/
│   ├── src/
│   │   └── app/            # Next.js app directory
│   ├── package.json
│   └── next.config.mjs
├── .gitignore
└── README.md
```

## Usage

1. Start the backend server
2. Start the frontend development server
3. Upload Hindi PDF files through the interface
4. Search for text within the PDFs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload PDF file for indexing |
| `/api/progress` | GET | Get PDF processing progress |
| `/api/search` | GET | Search for text in indexed PDF |
| `/api/convert` | GET | Convert Hindi text between KrutiDev and Unicode |

### API Examples

```bash
# Search for a voter
curl "http://localhost:8000/api/search?query=राम&father_name=श्याम"

# Convert text
curl "http://localhost:8000/api/convert?text=नमस्ते"

# Check processing progress
curl "http://localhost:8000/api/progress"
```

## License

MIT
