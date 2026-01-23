# UNIOVI Schedule Scraper 🕒

A Python web scraper built with Playwright to extract class schedules from the University of Oviedo's Computer Science degree planning system. This tool retrieves personalized class schedules based on student UO identifiers.

## 📋 Description

This scraper automates the process of fetching your class schedule from the UNIOVI government portal. Simply provide your UO (student identifier) and receive a structured JSON response with all your enrolled classes.

**Perfect for:**
- CS students at Universidad de Oviedo
- Developers integrating UNIOVI schedules into their applications
- Backend services that need automated schedule retrieval

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

1. **Clone or download this repository**
   
2. **Install uv (if not already installed):**
  ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or with pip
   pip install uv
  ```

3. **Install dependencies and activate virtual environment:**
   ```bash
   # uv will automatically create a virtual environment and install dependencies
   uv sync
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## 💻 Usage

There are **two ways** to use this scraper:

### Method 1: Interactive Mode

Run the script without arguments and it will prompt you for input:

```bash
python main.py
```

Then enter your UO when prompted:
```
Ingresa el valor del UO:
UO287577
```

### Method 2: Command Line Arguments

Pass the UO directly as a command-line argument:

```bash
python main.py UO287577
```

### Output Format

Both methods return a JSON response with your class schedule:

```json
{
  "success": true,
  "uo": "Uo287577",
  "classes": [
    "Alg.T.2",
    "Alg.S.1",
    "Alg.L.3",
    "SO.T.1",
    "SO.L.1",
    "TPP.T.2",
    "TPP.L.5"
  ]
}
```

In case of error:
```json
{
  "success": false,
  "error": "Error message here"
}
```

## 🔌 Integration with Node.js/JavaScript Backend

You can easily integrate this scraper into your Node.js backend:

```javascript
const { spawn } = require('child_process');

function getHorarios(uo) {
  return new Promise((resolve, reject) => {
    const python = spawn('python', ['main.py', uo]);
    
    let stdout = '';
    let stderr = '';
    
    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Error: ${stderr}`));
        return;
      }
      
      try {
        const result = JSON.parse(stdout);
        if (result.success) {
          resolve(result);
        } else {
          reject(new Error(result.error));
        }
      } catch (e) {
        reject(new Error('Error parsing response'));
      }
    });
  });
}

// Usage example
getHorarios('UO287577')
  .then(result => {
    console.log('Classes:', result.classes);
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

### Express.js API Example

```javascript
const express = require('express');
const app = express();

app.get('/api/schedule/:uo', async (req, res) => {
  try {
    const result = await getHorarios(req.params.uo);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

## 📦 Project Structure

```
python-horarios/
├── main.py              # Main scraper script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🛠️ Functions

### `get_element_by_uo(page, uo_value)`
Navigates to the UNIOVI planning page and selects the schedule for the specified UO.

### `getListClass(page)`
Extracts and returns the list of enrolled classes from the schedule page.

## ⚙️ Configuration

The scraper is configured for:
- **Academic Year:** 2025-2026 (`y=25-26`)
- **Semester:** Second semester (`t=s2`)

To modify these parameters, edit the URL in the `get_element_by_uo()` function:
```python
page.goto("https://gobierno.ingenieriainformatica.uniovi.es/grado/gd/?y=25-26&t=s2")
```

## 🐛 Troubleshooting

**Browser not found:**
```bash
playwright install chromium
```

**ModuleNotFoundError:**
```bash
pip install playwright
```

**Permission denied:**
Make sure Python is added to your system PATH.

## 📄 License

Free to use for UNIOVI students and developers.

## 🤝 Contributing

Feel free to fork, improve, and submit pull requests!
