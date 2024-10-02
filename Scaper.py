import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from fake_useragent import UserAgent
import logging
import concurrent.futures
import hashlib
import json
import os
from datetime import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="scraper.log",
)


class WebScraper(QThread):
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    scraping_finished = pyqtSignal()

    def __init__(self, urls):
        super().__init__()
        self.urls = urls
        self.user_agent = UserAgent()
        self.datos = []
        self.cache_dir = "cache"
        self.db_path = "scraper_data.db"
        self.setup_database()
        os.makedirs(self.cache_dir, exist_ok=True)

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS scrape_data
            (url TEXT PRIMARY KEY, title TEXT, content TEXT, 
             price REAL, category TEXT, timestamp DATETIME)
        """
        )
        conn.commit()
        conn.close()

    def get_cache_path(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")

    def load_from_cache(self, url):
        cache_path = self.get_cache_path(url)
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                cached_data = json.load(f)
                if time.time() - cached_data["timestamp"] < 86400:
                    return cached_data["data"]
        return None

    def save_to_cache(self, url, data):
        cache_path = self.get_cache_path(url)
        with open(cache_path, "w") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)

    def obtener_pagina(self, url):
        cached_data = self.load_from_cache(url)
        if cached_data:
            return cached_data
        headers = {
            "User-Agent": self.user_agent.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        }
        try:
            session = requests.Session()
            retries = 3
            for _ in range(retries):
                time.sleep(random.uniform(1, 3))
                response = session.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    self.save_to_cache(url, response.text)
                    return response.text
                elif response.status_code == 429:
                    time.sleep(30)
                else:
                    time.sleep(5)
        except requests.RequestException as e:
            logging.error(f"Error al obtener la página {url}: {e}")
        return None

    def extraer_datos(self, html, url):
        if not html:
            return
        soup = BeautifulSoup(html, "html.parser")
        try:
            products = soup.find_all("div", class_="product")
            for product in products:
                title = product.find("h2", class_="product-title").text.strip()
                price = float(
                    product.find("span", class_="price").text.strip().replace("$", "")
                )
                category = product.find("span", class_="category").text.strip()
                content = product.find("div", class_="description").text.strip()
                self.guardar_en_db(
                    {
                        "url": url,
                        "title": title,
                        "content": content,
                        "price": price,
                        "category": category,
                    }
                )
                self.datos.append(
                    {"url": url, "title": title, "price": price, "category": category}
                )
        except Exception as e:
            logging.error(f"Error al extraer datos de {url}: {e}")

    def guardar_en_db(self, data):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO scrape_data
            (url, title, content, price, category, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                data["url"],
                data["title"],
                data["content"],
                data["price"],
                data["category"],
                datetime.now(),
            ),
        )
        conn.commit()
        conn.close()

    def guardar_datos(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.getcwd(), "datos_scraping")
        os.makedirs(output_dir, exist_ok=True)
        base_filename = f"datos_scraping_{timestamp}"
        csv_filename = os.path.join(output_dir, f"{base_filename}.csv")
        excel_filename = os.path.join(output_dir, f"{base_filename}.xlsx")
        json_filename = os.path.join(output_dir, f"{base_filename}.json")
        try:
            df = pd.DataFrame(self.datos)
            df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
            df.to_excel(excel_filename, index=False)
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=4)
            logging.info(
                f"Datos guardados en {csv_filename}, {excel_filename} y {json_filename}"
            )
            return csv_filename, excel_filename, json_filename
        except Exception as e:
            logging.error(f"Error al guardar los datos: {e}")
            return None, None, None

    def procesar_url(self, url):
        self.update_status.emit(f"Procesando URL: {url}")
        html = self.obtener_pagina(url)
        if html:
            self.extraer_datos(html, url)

    def run(self):
        total_urls = len(self.urls)
        for i, url in enumerate(self.urls, 1):
            self.procesar_url(url)
            progress = int((i / total_urls) * 100)
            self.update_progress.emit(progress)
        csv_file, excel_file, json_file = self.guardar_datos()
        if csv_file and excel_file and json_file:
            self.update_status.emit(
                f"Datos guardados en:\n{csv_file}\n{excel_file}\n{json_file}"
            )
        else:
            self.update_status.emit("Error al guardar los datos")
        self.scraping_finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Scraper")
        self.setGeometry(100, 100, 600, 400)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        self.add_url_button = QPushButton("Agregar URL")
        self.add_url_button.clicked.connect(self.add_url)
        layout.addWidget(self.add_url_button)
        self.url_list = QTextEdit()
        self.url_list.setReadOnly(True)
        layout.addWidget(self.url_list)
        self.start_button = QPushButton("Iniciar Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Listo para iniciar")
        layout.addWidget(self.status_label)
        self.urls = []

    def add_url(self):
        url = self.url_input.text().strip()
        if url:
            if url not in self.urls:
                self.urls.append(url)
                self.url_list.append(url)
                self.url_input.clear()
            else:
                QMessageBox.warning(
                    self, "URL duplicada", "Esta URL ya ha sido agregada."
                )
        else:
            QMessageBox.warning(self, "URL vacía", "Por favor, ingrese una URL válida.")

    def start_scraping(self):
        if not self.urls:
            QMessageBox.warning(
                self,
                "Sin URLs",
                "Por favor, agregue al menos una URL para iniciar el scraping.",
            )
            return
        self.start_button.setEnabled(False)
        self.add_url_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.scraper = WebScraper(self.urls)
        self.scraper.update_progress.connect(self.update_progress)
        self.scraper.update_status.connect(self.update_status)
        self.scraper.scraping_finished.connect(self.scraping_finished)
        self.scraper.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, status):
        self.status_label.setText(status)

    def scraping_finished(self):
        self.start_button.setEnabled(True)
        self.add_url_button.setEnabled(True)
        QMessageBox.information(
            self, "Scraping completado", "El proceso de scraping ha finalizado."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
