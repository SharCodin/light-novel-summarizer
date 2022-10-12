"""Summarize Text using QuillBot."""


import os
import re
from time import sleep
from tkinter import Tk
from tkinter.filedialog import askdirectory

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


# Create a file called "SECRETS.py" in the main directory of the project.
# Save your QuillBot Email and Password login information in it in the 
# following format.
#
# EMAIL: str = 'YOUR EMAIL ADDRESS HERE'
# PASSWORD: str = 'YOUR PASSWROD HERE'
# INITIALDIR: str = 'The path to the folder containing your text files.'

import SECRETS


def login(driver, email, password) -> None:
    """Login to Quillbot."""
    email_field = None
    while email_field is None:
        try:
            email_field = driver.find_element(
                By.XPATH, '//*[@id="loginContainer"]/div/div[4]/div/div/input'
            )
            password_field = driver.find_element(
                By.XPATH, '//*[@id="loginContainer"]/div/div[5]/div/div/input'
            )

            email_field.send_keys(email)
            sleep(1)
            password_field.send_keys(password)
            ActionChains(driver).key_down(Keys.ENTER).key_up(Keys.ENTER).perform()
        except NoSuchElementException:
            print('Waiting for page to load.', end='\r')
            sleep(1)


def make_chunks(text: str) -> list[list[str]]:
    """Split the text into 1,200 words chunks."""
    counter: int = 0
    chunk_length: int = 1200
    chunks: list[list[str]] = []
    sentences: list[str] = []
    for sentence in text.split("\n"):
        if len(sentence.split()) + counter < chunk_length:
            sentences.append(sentence)
            counter: int = counter + len(sentence.split())
        else:
            chunks.append(sentences[:])
            counter: int = 0
            sentences.clear()
            sentences.append(sentence)
            counter: int = counter + len(sentence.split())
    chunks.append(sentences[:])
    return chunks


def get_summary(driver, text) -> str:
    """Get summarized text from website."""
    textbox = driver.find_element(By.ID, "inputBoxSummarizer")
    textbox.clear()
    sleep(1)
    textbox.send_keys(text)
    sleep(5)
    (ActionChains(driver)
        .key_down(Keys.CONTROL)
        .key_down(Keys.ENTER)
        .key_up(Keys.CONTROL)
        .key_up(Keys.ENTER)
        .perform()
    )
    sleep(10)
    summary = driver.find_element(By.ID, "outputBoxSummarizer")
    return summary.text


def save_to_file(FOLDER_PATH: str, text: str, file: str):
    """Append summarized text to file."""
    file_part: str = "summary" + " - " + file.title()
    SUMMARY: str = os.path.join(FOLDER_PATH, "summary")
    file_summary: str = os.path.join(SUMMARY, file_part)
    if not os.path.exists(SUMMARY):
        os.mkdir(os.path.join(SUMMARY))
    with open(file_summary, "a", encoding="utf-8") as f:
        f.write(text)
        f.write("\n\n")


def main():
    """Run when the script is called."""
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)  # type: ignore
    driver.set_window_position(-8,-1088)
    driver.maximize_window()
    driver.get("https://quillbot.com/login?returnUrl=/summarize")

    login(driver, SECRETS.EMAIL, SECRETS.PASSWORD)
    print('\n\n')

    root = Tk()
    root.withdraw()
    FOLDER_PATH = askdirectory(
        initialdir=SECRETS.INITIALDIR
    )

    pattern = r"—|-|:|\s"
    for index, file in enumerate(os.listdir(FOLDER_PATH)):
        file_path: str = os.path.join(FOLDER_PATH, file)
        if not os.path.isfile(file_path):
            continue
        with open(file_path, encoding="utf-8") as f:
            file_text = f.read()
            cycle_times = str(round(len(re.split(pattern, file_text)) / 1200)).zfill(3)
        print(index + 1, "--> Cycle Time:", cycle_times, "--> File:", file)

    print("\n\n")

    index: int = 0
    stopper: int = int(input("Number of files to process: "))

    for file in os.listdir(FOLDER_PATH):
        if index >= stopper:
            break
        file_path: str = os.path.join(FOLDER_PATH, file)
        if not os.path.isfile(file_path):
            continue
        print()
        print("\n\n", file)
        with open(file_path, "r", encoding="utf-8") as f:
            text: str = f.read()
            text: str = re.sub(r"\n{2,50}", "\n", text).strip()
            text: str = re.sub(r"(?<=\S)\?(?=\S)", ", ", text).strip()
            text: str = text.replace("—", ", ").strip()
            parts: list[list[str]] = make_chunks(text)
            for idx, part in enumerate(parts):
                print(f"{idx + 1}/{len(parts)}")
                text: str = "\n".join(part)
                summary_text: str = get_summary(driver, text)
                save_to_file(FOLDER_PATH, summary_text, file)
        index += 1
        os.remove(file_path)
    driver.quit()

    print("\n\n")
    print("COMPLETED".center(50, "*"))


if __name__ == "__main__":
    main()
