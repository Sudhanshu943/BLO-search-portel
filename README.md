# Hindi PDF Search

A full-stack application for searching and indexing Hindi PDF documents with OCR capabilities.

## Features

- Hindi text recognition from PDF files
- Full-text search functionality
- Backend API for PDF processing
- Frontend user interface built with Next.js

## Tech Stack

- **Frontend**: Next.js, React
- **Backend**: Python (Flask/FastAPI)
- **OCR**: Hindi text recognition

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
cd backend
pip install -r requirements.txt
python main.py
```

## Project Structure

```
.
├── backend/
│   ├── converter.py      # PDF to text conversion
│   ├── main.py           # Backend API server
│   └── pdf_database.csv  # Indexed PDF data
├── frontend/
│   ├── src/
│   │   └── app/          # Next.js app directory
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

## License

MIT
