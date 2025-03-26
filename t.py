import time
import tkinter as tk
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from flask import Flask, render_template, jsonify, request
import socket
import customtkinter as ctk


driver = None
keyword_entry = None

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

computer_name = socket.gethostname()

def start_selenium():
    """Selenium WebDriver'ı başlatır ve WhatsApp Web'i açar."""
    global driver
    options = Options()
    options.add_experimental_option("detach", True)
    
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://web.whatsapp.com")
    
    print("QR kodunu taradıktan sonra ENTER'a bas...")
    input()

    time.sleep(5)
    driver.refresh()

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
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='side']/div[1]/div/div[2]/div/div/div[1]/p")
            )
        )
        input_bar.send_keys(",".join(keywords))
        time.sleep(2)

        chat_list = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[@id='pane-side']/div/div/div")
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

                        if message_text and any(
                            keyword.lower() in message_text.lower()
                            for keyword in keywords
                        ):
                            matched_messages.append(message_text)
                    except Exception as e:
                        print(f"Mesaj ayrıştırma hatası: {e}")

            except Exception as e:
                print(f"Sohbet inceleme hatası: {e}")

        input_bar.clear()
    except Exception as e:
        print(f"Genel hata: {e}")

    return matched_messages


def update_messages():
    """GUI ile eşleşen mesajları günceller."""
    global driver, keyword_entry
    if driver is None:
        print("HATA: Selenium başlatılmadı!")
        return

    keywords = keyword_entry.get().split(",")
    messages = check_messages(keywords)
    print(messages)

def start_scraping():
    """Mesajları sürekli kontrol eder."""
    while True:
        update_messages()
        time.sleep(60 * 30)


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
    root.geometry("500x400")
    root.resizable(False, False)

    frame = ctk.CTkFrame(root, corner_radius=10)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    ctk.CTkLabel(frame, text="Anahtar Kelimeler (Virgülle Ayırın):", font=("Arial", 12, "bold")).pack(pady=5)

    keyword_entry = ctk.CTkEntry(frame, width=300, font=("Arial", 12))
    keyword_entry.pack(pady=5)

    btn_update = ctk.CTkButton(frame, text="Mesajları Güncelle", width=200, corner_radius=15, fg_color="#4CAF50", hover_color="#45A049", command=update_messages)
    btn_update.pack(pady=5)

    btn_start = ctk.CTkButton(frame, text="WhatsApp Web Aç", width=200, corner_radius=15, fg_color="#008CBA", hover_color="#007BB5", command=start_selenium)
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
