import customtkinter as ctk
import tkinter as tk
import requests
import time
import threading
import re
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# ---------------- CONFIG ---------------- #
APP_TITLE = "PSE VOLUME MONITOR"
FONT_FAMILY = "Fixedsys"


# ---------------- SCRAPER ---------------- #
class FilgitScraper:
    BASE_URL = "https://filgit.com"

    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        self.session.mount("https://", adapter)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def _clean_and_parse(self, text):
        if not text:
            return 0.0

        t = text.replace("₱", "").replace(",", "").strip().upper()

        if t in ["", "-", "—", "N/A"]:
            return 0.0

        multiplier = 1

        if "B" in t:
            multiplier = 1_000_000_000
        elif "M" in t:
            multiplier = 1_000_000
        elif "K" in t:
            multiplier = 1_000

        match = re.search(r"\d+(\.\d+)?", t)
        if not match:
            return 0.0

        return float(match.group()) * multiplier

    def get_stock_list(self):
        all_stocks = []
        pages = [
            f"{self.BASE_URL}/pse-stocks",
            f"{self.BASE_URL}/pse-stocks?page=2",
            f"{self.BASE_URL}/pse-stocks?page=3"
        ]

        for url in pages:
            try:
                res = self.session.get(url, headers=self.headers, timeout=15)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "html.parser")
                table = soup.find("table")
                if not table:
                    continue

                headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]

                market_cap_index = None
                for i, header in enumerate(headers):
                    if "market" in header and "cap" in header:
                        market_cap_index = i
                        break

                rows = table.find_all("tr")[1:]

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) < 2:
                        continue

                    ticker_tag = row.find("a")
                    if not ticker_tag:
                        continue

                    ticker = ticker_tag.get_text(strip=True)
                    name = cols[0].get_text(" ", strip=True).replace(ticker, "").strip()

                    market_cap = 0.0
                    if market_cap_index is not None and market_cap_index < len(cols):
                        market_cap = self._clean_and_parse(
                            cols[market_cap_index].get_text()
                        )

                    all_stocks.append({
                        "ticker": ticker,
                        "name": name,
                        "market_cap_pesos": market_cap
                    })

                time.sleep(0.5)

            except Exception as e:
                print(f"Error scraping {url}: {e}")

        return all_stocks

    def get_trade_volume(self, ticker, days):
        try:
            url = f"{self.BASE_URL}/{ticker.lower()}-stock-price-history-pse"
            res = self.session.get(url, headers=self.headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table")
            if not table:
                return 0.0, 0

            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]

            trade_value_index = None
            for i, header in enumerate(headers):
                if "trade" in header and "value" in header:
                    trade_value_index = i
                    break

            if trade_value_index is None:
                return 0.0, 0

            total_value = 0.0
            rows = table.find_all("tr")[1:days + 1]

            for row in rows:
                cols = row.find_all("td")
                if trade_value_index < len(cols):
                    total_value += self._clean_and_parse(
                        cols[trade_value_index].get_text()
                    )

            return round(total_value, 2), len(rows)

        except:
            return 0.0, 0

    def fetch_all(self, progress_callback=None):
        data = []
        stocks = self.get_stock_list()
        total = len(stocks)

        for i, stock in enumerate(stocks):
            ticker = stock["ticker"]

            if progress_callback:
                progress_callback(i + 1, total, ticker)

            total_month, month_days = self.get_trade_volume(ticker, 30)
            total_year, year_days = self.get_trade_volume(ticker, 252)

            m_vol = round(total_month / month_days, 2) if month_days else 0
            y_vol = round(total_year / year_days, 2) if year_days else 0

            data.append({
                "ticker": ticker,
                "name": stock["name"],
                "market_cap_pesos": stock["market_cap_pesos"],
                "month_volume_pesos": m_vol,
                "year_volume_pesos": y_vol
            })

            time.sleep(0.2)

        return data


# ---------------- UI APP ---------------- #
class PSEApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title(APP_TITLE)
        self.geometry("900x600")

        self.stock_data = []
        self.scraper = FilgitScraper()

        self._load_font()
        self._build_ui()

    def _load_font(self):
        try:
            self.font = ctk.CTkFont(family=FONT_FAMILY, size=14)
        except:
            self.font = ctk.CTkFont(size=14)

    def _build_ui(self):
        self.header = ctk.CTkLabel(
            self,
            text="PSE STOCK VOLUME TRACKER",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color="#00ff88"
        )
        self.header.pack(pady=15)

        self.refresh_btn = ctk.CTkButton(
            self,
            text="FETCH FULL MARKET DATA",
            command=self.load_data,
            fg_color="#003300",
            hover_color="#005500",
            font=self.font
        )
        self.refresh_btn.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            self,
            text="READY TO FETCH",
            font=(FONT_FAMILY, 12),
            text_color="#888888"
        )
        self.status_label.pack(pady=5)

        self.table = tk.Text(
            self,
            bg="#001a00",
            fg="#00ff88",
            insertbackground="#00ff88",
            font=(FONT_FAMILY, 11),
            relief="flat"
        )
        self.table.pack(expand=True, fill="both", padx=15, pady=15)
        self.table.config(state="disabled")

    def _update_status(self, current, total, ticker):
        percent = (current / total) * 100
        msg = f"[{percent:.1f}%] SCRAPING {ticker} ({current}/{total})..."
        self.after(0, lambda: self.status_label.configure(text=msg, text_color="#ffff00"))

    def load_data(self):
        threading.Thread(target=self._load_data_thread, daemon=True).start()

    def _load_data_thread(self):
        self.stock_data = self.scraper.fetch_all(
            progress_callback=self._update_status
        )

        self.display_data()

        self.status_label.configure(
            text="FETCH COMPLETE",
            text_color="#00ff88"
        )

        self.save_to_excel()

    def display_data(self):
        self.table.config(state="normal")
        self.table.delete("1.0", tk.END)

        for stock in self.stock_data:
            self.table.insert(tk.END, f"{stock}\n")

        self.table.config(state="disabled")

    # ---------------- EXCEL EXPORT ---------------- #
    def save_to_excel(self):
        if not self.stock_data:
            return

        df = pd.DataFrame(self.stock_data)

        filename = f"PSE_Market_Data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="MarketData")

            worksheet = writer.sheets["MarketData"]

            # Freeze header row
            worksheet.freeze_panes = "A2"

            # Auto column width
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

            # Enable filters
            worksheet.auto_filter.ref = worksheet.dimensions

        print(f"Excel file saved as {filename}")


if __name__ == "__main__":
    app = PSEApp()
    app.mainloop()
