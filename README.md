# 📊 PSE Volume Monitor

A Python desktop application that scrapes Philippine Stock Exchange (PSE) market data from Filgit, calculates average trade volumes, and exports results to Excel — all inside a sleek dark-mode GUI built with CustomTkinter.

---

## 🚀 Features

- Scrapes all PSE-listed stocks  
- Extracts Market Capitalization  
- Calculates:
  - 30-day average trade value
  - 252-day (1-year) average trade value  
- Displays results in a desktop GUI  
- Automatically exports formatted Excel files  
- Multithreaded scraping (non-blocking UI)  
- Retry logic for network stability  
- Smart parsing for values with:
  - K (thousands)
  - M (millions)
  - B (billions)
  - ₱ symbol handling  

---

## 🧠 How It Works

### 1. Stock List Scraping

The app scrapes:

```
https://filgit.com/pse-stocks
https://filgit.com/pse-stocks?page=2
https://filgit.com/pse-stocks?page=3
```

It extracts:
- Ticker
- Company name
- Market capitalization

---

### 2. Trade Volume Calculation

For each ticker:

```
https://filgit.com/{ticker}-stock-price-history-pse
```

It computes:
- Average trade value (last 30 trading days)
- Average trade value (last 252 trading days)

---

### 3. Data Output

Results are:
- Displayed inside the GUI
- Automatically saved as:

```
PSE_Market_Data_YYYY-MM-DD_HH-MM-SS.xlsx
```

Excel file includes:
- Frozen header row
- Auto-adjusted column widths
- Filters enabled
- Clean formatting

---

## 🖥️ UI Design

- Dark mode interface  
- Neon green terminal-style text  
- Live progress percentage indicator  
- Background threaded scraping  

---

## 🛠️ Tech Stack

- Python 3.x  
- CustomTkinter  
- Tkinter  
- requests  
- BeautifulSoup4  
- pandas  
- openpyxl  
- threading  

---

## 📦 Installation

```bash
pip install customtkinter requests beautifulsoup4 pandas openpyxl
```

---

## ▶️ Run The App

```bash
python your_script_name.py
```

Click:

```
FETCH FULL MARKET DATA
```

Wait for scraping to complete.  
The Excel file will be generated automatically.

---

## 🧩 Project Structure

```
FilgitScraper
 ├── get_stock_list()
 ├── get_trade_volume()
 └── fetch_all()

PSEApp (GUI)
 ├── load_data()
 ├── display_data()
 └── save_to_excel()
```

---

## 📊 Example Output

```python
{
  "ticker": "ALI",
  "name": "Ayala Land Inc.",
  "market_cap_pesos": 523000000000.0,
  "month_volume_pesos": 14500000.32,
  "year_volume_pesos": 12800000.11
}
```

---

## 🎯 Use Cases

- Market liquidity analysis  
- Volume screening  
- Fundamental research  
- Portfolio analysis groundwork  
- Data collection for AI/ML models  

---

## ⚠️ Disclaimer

This tool scrapes publicly available data from Filgit.  
It is intended for educational and research purposes only.  
Always verify financial data from official sources before making investment decisions.
