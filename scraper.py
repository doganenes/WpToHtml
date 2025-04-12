from datetime import datetime, timedelta
import time
import tkinter as tk
from flask import Flask, jsonify, request, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
import webbrowser
import sys
import platform
from flask_cors import CORS

driver = None
keyword_entry = None

app = Flask(__name__)
CORS(app)
load_dotenv()

computer_name = os.getlogin()
print(f"{computer_name}")
chrome_user_data_dir = os.getenv("CHROME_USER_DATA_DIR")

start_date = datetime(2025, 4, 10)
end_date = start_date + timedelta(days=10)


def is_within_valid_period():
    current_date = datetime.now()
    return start_date <= current_date <= end_date


def get_chrome_user_data_path():
    user_home = os.path.expanduser("~")

    if platform.system() == "Windows":
        return os.path.join(
            user_home, "AppData", "Local", "Google", "Chrome", "User Data", "Profile 1"
        )
    elif platform.system() == "Darwin":
        return os.path.join(
            user_home, "Library", "Application Support", "Google", "Chrome", "Profile 1"
        )
    else:
        return os.path.join(user_home, ".config", "google-chrome", "Profile 1")


def get_chromedriver_path():
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "chromedriver.exe")


chrome_user_data_dir = get_chrome_user_data_path()


def create_image():
    try:
        return Image.open("whatsapp.png")
    except Exception as e:
        print(f"whatsapp.png yüklenemedi: {e}")
        image = Image.new("RGB", (64, 64), "green")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="white")
        return image


def on_quit(icon, item):
    print("System tray quit selected.")
    icon.stop()
    on_closing()


def show_gui(icon, item):
    icon.stop()
    threading.Thread(target=run_gui).start()


def setup_tray_icon():
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem("Show GUI", show_gui), pystray.MenuItem("Exit", on_quit)
    )
    icon = pystray.Icon("whatsapp_tracker", image, "WhatsApp Tracker", menu)
    icon.run()


def start_selenium():
    global driver
    print(f"Starting Selenium on {computer_name}")
    options = Options()
    options.add_argument(rf"user-data-dir={chrome_user_data_dir}")
    options.add_experimental_option("detach", True)
    service = Service(get_chromedriver_path())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    input("After scanning the QR code, press ENTER...")


matched_messages = []


def check_messages(keywords):

    if len(matched_messages) > 0:
        matched_messages.clear()

    global driver
    if driver is None:
        print("Error: Selenium not started!")
        return []

    try:
        driver.get("https://web.whatsapp.com")
        wait = WebDriverWait(driver, 20)
        group_filter_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "group-filter"))
        )
        group_filter_btn.click()
        time.sleep(1)

        input_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='side']/div[1]/div/div[2]/div/div/div[1]/p")
            )
        )
        input_bar.send_keys(Keys.CONTROL + "a")  # Tüm metni seç
        input_bar.send_keys(Keys.DELETE)  # Seçili metni sil
        input_bar.send_keys(",".join(keywords))
        time.sleep(1)

        chat_list = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[@id='pane-side']/div/div/div")
            )
        )
        time.sleep(1)
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
                        print(f"Message parsing error: {e}")
            except Exception as e:
                print(f"Chat review error: {e}")
        input_bar.clear()
    except Exception as e:
        print(f"General error: {e}")

    return matched_messages


def on_closing():
    print("🛑 Kapatılıyor...")

    try:
        if driver:
            driver.quit()
            print("✅ Selenium kapatıldı.")
    except Exception as e:
        print(f"❌ Selenium kapatılamadı: {e}")

    os._exit(0)


def multi_command():
    if not is_within_valid_period():
        print("❌ Geçerlilik süresi dolmuş. Program sonlandırılıyor.")
        os._exit(0)
    check_messages(keyword_entry.get().split(","))

    threading.Thread(target=start_scraping).start()


"""def check_messages_threaded(keywords):
    def task():
        print("📥 Threaded check started...")
        messages = check_messages(keywords)
        print(f"✅ Found {len(messages)} messages")
        for msg in messages:
            print(f"[{msg['timestamp']}] {msg['message']}")

    threading.Thread(target=task, daemon=True).start()
"""


def start_scraping():
    time.sleep(1)
    keywords = keyword_entry.get().split(",")

    try:

        webbrowser.open(
            f"http://127.0.0.1:5005/get-messages?keywords={','.join(keywords)}", new=2
        )
        print("Opening messages page...")
    except Exception as e:
        print(f"Error opening the page: {e}")

        try:
            print(f"Auto checking for keywords: {','.join(keywords)}")
            check_messages(keywords)
        except Exception as e:
            print(f"Error during scraping: {e}")


@app.route("/get-messages", methods=["GET"])
def get_messages():
    try:
        keywords = request.args.get("keywords", "").split(",")
        check_messages(keywords)
        return render_template("index.html", messages=matched_messages)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html")


def run_flask():
    app.run(host="127.0.0.1", port=5005)


def run_gui():
    global keyword_entry

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Whatsapp Mesaj Otomasyonu")
    root.geometry("500x250")
    root.resizable(False, False)

    threading.Thread(target=start_selenium).start()

    frame = ctk.CTkFrame(root, corner_radius=10)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    ctk.CTkLabel(
        frame, text="Anahtar Kelimeler (Virgülle Ayırın):", font=("Arial", 12, "bold")
    ).pack(pady=5)
    keyword_entry = ctk.CTkEntry(frame, width=300, font=("Arial", 12))
    keyword_entry.pack(pady=5)

    ctk.CTkButton(
        frame,
        text="Mesajları Güncelle",
        width=200,
        corner_radius=15,
        fg_color="#4CAF50",
        hover_color="#45A049",
        command=lambda: threading.Thread(target=start_scraping).start(),
    ).pack(pady=5)

    ctk.CTkButton(
        frame,
        text="Mesaj Bulmaya Başla",
        width=200,
        corner_radius=15,
        fg_color="#FF9800",
        hover_color="#E68900",
        command=lambda: threading.Thread(target=multi_command).start(),
    ).pack(pady=5)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=setup_tray_icon).start()
    run_gui()
