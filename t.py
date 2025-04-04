import time
import tkinter as tk
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import threading
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from flask import Flask, render_template, jsonify, request
import socket
import os
from dotenv import load_dotenv
import customtkinter as ctk
from datetime import datetime
import requests
import webbrowser

driver = None
keyword_entry = None

from flask_cors import CORS

app = Flask(__name__)
CORS(app)
load_dotenv()

computer_name = socket.gethostname()
chrome_user_data_dir = os.getenv("CHROME_USER_DATA_DIR")


def start_selenium():
    """Selenium WebDriver'ı başlatır ve WhatsApp Web'i açar."""
    global driver
    print(computer_name)
    options = Options()
    options.add_argument(rf"user-data-dir={chrome_user_data_dir}")
    options.add_argument("--log-level=3")

    options.add_argument(f"{computer_name}")
    options.add_experimental_option("detach", True)
    service = Service(r"WpToHtml\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://web.whatsapp.com")
    input("QR kodunu taradıktan sonra ENTER'a bas...")


def check_messages(keywords):
    """Tüm sohbetlere tıklayıp mesajları kontrol eder."""
    if driver is None:
        print("HATA: Selenium başlatılmadı!")
        return []

    matched_messages = []

    try:
        group_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "group-filter"))
        )
        ActionChains(driver).move_to_element(group_button).click().perform()
        time.sleep(1)
        input_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )

        # İçeriği temizle (CTRL + A ve DELETE ile)
        input_bar.send_keys(Keys.CONTROL + "a")  # Tüm metni seç
        input_bar.send_keys(Keys.DELETE)  # Seçili metni sil
        input_bar.send_keys(",".join(keywords))
        input_bar.send_keys(Keys.ENTER)
        time.sleep(1)
        chat_list = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[@id='pane-side']/div[1]/div/div")
            )
        )

        for chat in chat_list:
            try:
                ActionChains(driver).move_to_element(chat).click().perform()
                time.sleep(1)

                elements = driver.find_elements(
                    By.CSS_SELECTOR, "div.x10l6tqk[role='listitem']"
                )

                if not elements:
                    elements = driver.find_elements(
                        By.CSS_SELECTOR, "div[role='listitem']"
                    )

                for element in elements:
                    try:
                        html_content = element.get_attribute("innerHTML")
                        soup = BeautifulSoup(html_content, "html.parser")

                        message_text = None
                        timestamp = None

                        # Extract message text
                        span_message = soup.find("span", class_="x78zum5 x1cy8zhl")
                        if span_message:
                            message_text = span_message.get_text()

                        if not message_text:
                            span_message = soup.find("span", class_="x1iyjqo2")
                            if span_message:
                                message_text = span_message.get_text()

                        if not message_text:
                            span_with_title = soup.find("span", attrs={"title": True})
                            if span_with_title:
                                message_text = span_with_title.get("title")

                        if not message_text:
                            message_text = element.text

                        # Extract timestamp
                        time_div = soup.find("div", class_="_ak8i")
                        if time_div:
                            timestamp = time_div.get_text()

                        if message_text and any(
                            keyword.lower() in message_text.lower()
                            for keyword in keywords
                        ):
                            matched_messages.append(
                                {"message": message_text, "timestamp": timestamp}
                            )

                    except Exception as e:
                        print(f"Mesaj ayrıştırma hatası: {e}")

            except Exception as e:
                print(f"Sohbet inceleme hatası: {e}")

    except Exception as e:
        print(f"Genel hata: {e}")

    return matched_messages


import webbrowser
import time


def start_scraping():
    """Mesajları sürekli kontrol eder ve get-messages API'sini tetikler."""
    keywords = keyword_entry.get().split(",")

    try:
        webbrowser.open(
            f"http://127.0.0.1:5000/get-messages?keywords={','.join(keywords)}", new=2
        )
        print("Automatically opening the messages page in browser...")
    except Exception as e:
        print(f"Error opening the page: {e}")

    while True:
        try:
            print(f"Checking messages for keywords: {','.join(keywords)}")
            time.sleep(60)
        except Exception as e:
            print(f"Error during scraping: {e}")


@app.route("/get-messages", methods=["GET"])
def get_messages():
    try:
        keywords = request.args.get("keywords", "").split(",")
        messages = check_messages(keywords)
        return render_template("t.html", messages=messages)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    return render_template("t.html")


def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True, use_reloader=False)


def run_gui():
    global keyword_entry

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("WhatsApp Otomatik Mesaj Takip")
    root.geometry("500x250")
    root.resizable(False, False)

    # Call start_selenium() here to open WhatsApp Web automatically
    threading.Thread(target=start_selenium, daemon=True).start()

    frame = ctk.CTkFrame(root, corner_radius=10)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    ctk.CTkLabel(
        frame, text="Anahtar Kelimeler (Virgülle Ayırın):", font=("Arial", 12, "bold")
    ).pack(pady=5)

    keyword_entry = ctk.CTkEntry(frame, width=300, font=("Arial", 12))
    keyword_entry.pack(pady=5)

    btn_update = ctk.CTkButton(
        frame,
        text="Mesajları Güncelle",
        width=200,
        corner_radius=15,
        fg_color="#4CAF50",
        hover_color="#45A049",
        command=start_scraping,
    )
    btn_update.pack(pady=5)

    btn_start = ctk.CTkButton(
        frame,
        text="WhatsApp Web Aç",
        width=200,
        corner_radius=15,
        fg_color="#008CBA",
        hover_color="#007BB5",
        command=start_selenium,
    )
    btn_start.pack(pady=5)

    btn_auto = ctk.CTkButton(
        frame,
        text="Otomatik Takibi Başlat",
        width=200,
        corner_radius=15,
        fg_color="#FF9800",
        hover_color="#E68900",
        command=lambda: threading.Thread(target=start_scraping, daemon=True).start(),
    )
    btn_auto.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_gui()
    app.run(debug=True)
