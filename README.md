<div align="center">



# 🚀 CSV → JSON Converter



### A Modern, Fast & Production-Ready CSV to JSON Web Application



Convert CSV files into clean, structured JSON with advanced parsing, validation, automatic type detection, and a beautiful responsive interface.



<p align="center">



![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)

![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask)

![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas)

![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)



</p>



---



**Built with ❤️ using Python, Flask & Vanilla JavaScript**



</div>



---



# ✨ Overview



CSV → JSON Converter is a modern Flask web application that transforms CSV files into structured JSON within seconds.



It supports automatic delimiter detection, encoding detection, intelligent data type conversion, column customization, validation, JSON formatting, downloadable output, and a responsive dark-themed interface.



Designed for developers, students, analysts, and data engineers.



---



# 🌟 Features



## 📂 File Upload



- Drag & Drop Upload

- Click to Browse

- CSV Validation

- File Size Validation



---



## 🔍 Smart CSV Detection



- Automatic Delimiter Detection

- UTF-8 Detection

- UTF-8 BOM Support

- Latin-1 Support

- Header Recognition



---



## 📊 Data Preview



- Preview Rows

- Column Statistics

- Row Count

- Column Count

- Instant Validation



---



## ⚙️ Advanced Conversion



✅ Records JSON



✅ Object JSON



✅ Automatic Integer Detection



✅ Float Detection



✅ Boolean Detection



✅ Null Detection



✅ Pretty JSON



✅ Minified JSON



---



## 🧹 Data Cleaning



- Trim Whitespace

- Rename Columns

- Reorder Columns

- Include / Exclude Columns

- Remove Duplicate Rows

- Normalize Column Names



---



## 📦 Export



- Download JSON

- Copy to Clipboard

- Pretty Print

- Safe Filename Generation



---



## 🔒 Security



- Secure File Validation

- MIME Type Checking

- Filename Sanitization

- Path Traversal Protection

- XSS Safe Templates

- Configurable Upload Limit



---



## 📱 User Interface



- Responsive Design

- Dark Theme

- Mobile Friendly

- Accessible

- Keyboard Navigation



---



# 🏗 Project Structure



```text

csv-json-converter/



│

├── app.py

├── requirements.txt

├── LICENSE

│

├── config/

│   └── config.py

│

├── routes/

│   └── converter.py

│

├── services/

│   ├── csv_parser.py

│   ├── json_converter.py

│   └── validators.py

│

├── templates/

│   ├── base.html

│   └── index.html

│

├── static/

│   ├── css/

│   └── js/

│

├── uploads/

├── output/

│

└── tests/

```



---



# ⚡ Technology Stack



| Layer | Technology |

|---------|------------|

| Backend | Flask |

| Language | Python 3.11+ |

| Frontend | HTML5 + CSS3 + Vanilla JavaScript |

| Data Processing | Pandas |

| Testing | Pytest |

| Configuration | python-dotenv |



---



# 🚀 Installation



## Clone Repository



```bash

git clone https://github.com/muhammadmoria/csv-json-converter.git



cd csv-json-converter

```



---



## Create Virtual Environment



### Windows



```bash

python -m venv venv



venv\Scripts\activate

```



### Linux / macOS



```bash

python3 -m venv venv



source venv/bin/activate

```



---



## Install Dependencies



```bash

pip install -r requirements.txt

```



---



## Run Application



```bash

python app.py

```



Application will be available at



```

http://127.0.0.1:5000

```



---



# 📡 API Endpoints



| Method | Endpoint | Description |

|----------|-------------|----------------|

| GET | / | Home Page |

| GET | /api/health | Health Check |

| POST | /api/preview | Preview CSV |

| POST | /api/convert | Convert CSV |

| GET | /api/download/<filename> | Download JSON |



---



# 📊 JSON Output



Example



```json

[

  {

    "Name": "John",

    "Age": 25,

    "City": "London"

  },

  {

    "Name": "Alice",

    "Age": 30,

    "City": "Paris"

  }

]

```



---



# 🧪 Testing



Run all tests



```bash

pytest

```



Includes tests for



- CSV Parser

- JSON Converter

- Validators

- Routes



---



# 🔐 Security Features



- Secure Upload Validation

- File Extension Validation

- MIME Validation

- Secure Filenames

- Temporary File Storage

- No External APIs

- XSS Protection

- Configurable Upload Limits



---



# 📁 Supported Formats



### Delimiters



- Comma

- Semicolon

- Pipe

- Tab



### Encodings



- UTF-8

- UTF-8 BOM

- Latin-1



---



# 📈 Performance



✔ Fast CSV Parsing



✔ Intelligent Type Detection



✔ Efficient JSON Serialization



✔ Lightweight Frontend



✔ Responsive UI



```



---



# 🤝 Contributing



Contributions are welcome!



1. Fork the repository



2. Create your feature branch



```bash

git checkout -b feature/new-feature

```



3. Commit changes



```bash

git commit -m "Added new feature"

```



4. Push



```bash

git push origin feature/new-feature

```



5. Open a Pull Request



---



# 📄 License



This project is licensed under the MIT License.



See the **LICENSE** file for details.



---



<div align="center">



### ⭐ If you found this project useful,



# Give it a ⭐ on GitHub!



Made with ❤️ using Flask & Python



</div>
