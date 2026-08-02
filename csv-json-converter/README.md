# CSV to JSON Converter

A polished, production-ready web application for converting CSV files into clean, structured JSON. Built with Python, Flask, and vanilla JavaScript.

## Features

- **Drag & drop or click** CSV file upload
- **Automatic delimiter detection** (comma, semicolon, tab, pipe)
- **Automatic encoding detection** (UTF-8, UTF-8 BOM, Latin-1)
- **CSV data preview** with row/column statistics
- **Multiple JSON orientations**: Records (array) or Object (keyed)
- **Automatic type detection**: integers, floats, booleans, nulls
- **Configurable null handling**: keep, replace with empty string, or custom value
- **Column management**: include/exclude, reorder, rename, trim whitespace, normalize names
- **Duplicate row handling**: keep or remove
- **Pretty or minified JSON** with configurable indentation
- **Syntax-highlighted JSON output** with line numbers
- **Copy to clipboard** with fallback for older browsers
- **Download JSON** files with safe, automatic naming
- **Conversion statistics**: rows, columns, processing time, output size
- **Comprehensive validation** and human-readable error messages
- **Responsive design** — works on desktop, tablet, and mobile
- **Accessible** — keyboard navigation, ARIA labels, semantic HTML
- **Dark developer-themed interface**

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask |
| Data Processing | pandas, Python json module |
| Frontend | HTML5, CSS3, Tailwind CSS, Vanilla JS |
| Testing | pytest |
| Configuration | python-dotenv |

## Project Structure

```
csv-json-converter/
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore
├── LICENSE
│
├── config/
│   └── config.py           # Centralized configuration
│
├── services/
│   ├── __init__.py
│   ├── csv_parser.py       # CSV reading, delimiter/encoding detection
│   ├── json_converter.py   # DataFrame to JSON conversion
│   └── validators.py       # File and options validation
│
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Utility functions
│
├── routes/
│   ├── __init__.py
│   └── converter.py        # Flask route definitions
│
├── templates/
│   ├── base.html            # Base template
│   └── index.html           # Main page
│
├── static/
│   ├── css/
│   │   └── style.css        # Custom styles
│   └── js/
│       └── app.js           # Frontend application logic
│
├── tests/
│   ├── __init__.py
│   ├── test_csv_parser.py
│   ├── test_json_converter.py
│   ├── test_validators.py
│   └── test_routes.py
│
├── uploads/                # Temporary upload storage
│   └── .gitkeep
└── output/                 # Temporary output storage
    └── .gitkeep
```

## Installation

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

> PowerShell users: activation works the same with `.venv\Scripts\Activate.ps1`

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

The application will start at **http://127.0.0.1:5000**.

## Testing

```bash
# Activate the virtual environment first, then:
pytest -q
```

The test suite includes 94 tests covering CSV parsing, JSON conversion, validation, and API routes.

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Set to `development` to enable debug mode |
| `SECRET_KEY` | `change-this-in-production` | Flask secret key |
| `MAX_FILE_SIZE_MB` | `16` | Maximum upload file size in MB |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main page |
| GET | `/api/health` | Health check |
| POST | `/api/preview` | Upload and preview CSV |
| POST | `/api/convert` | Convert CSV to JSON |
| GET | `/api/download/<filename>` | Download generated JSON |

### Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE",
    "message": "Please upload a valid CSV file."
  }
}
```

## Security

- Uploaded files are treated as untrusted input
- Secure filename sanitization (no path traversal)
- File extension and MIME type validation
- Configurable maximum file size
- No executable file handling
- XSS protection via template escaping
- Production-safe error messages (no stack traces)
- Temporary files are server-side only, never sent to third parties

## Privacy

This application works entirely locally. No data is sent to external APIs or third-party services. Uploaded files are processed on the server and stored temporarily in the `uploads/` directory.

## Supported CSV Formats

- **Delimiters**: comma (`,`), semicolon (`;`), tab (`\t`), pipe (`|`)
- **Encodings**: UTF-8, UTF-8 with BOM, Latin-1
- **Max file size**: Configurable (default 16 MB)

## Production Deployment

```bash
pip install gunicorn
gunicorn app:app
```

## Troubleshooting

- **"The uploaded file is empty"**: Ensure the file has content and is saved as a proper CSV.
- **"We couldn't decode this file"**: Re-save the file as UTF-8 CSV.
- **"The CSV contains inconsistent columns"**: Check for rows with different numbers of columns.
- **"The file exceeds the maximum allowed size"**: Increase `MAX_FILE_SIZE_MB` in `.env`.

## License

MIT License — see [LICENSE](LICENSE) for details.
