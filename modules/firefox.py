import zipfile
import os
import requests

ZIP_PATH = "modules/firefox.zip"
DIST_PATH = "modules/"
URL = "https://ftp.mozilla.org/pub/firefox/nightly/latest-mozilla-central/firefox-108.0a1.en-US.win32.zip"


def download():
    print("Baixando Firefox 108.0a1...\n")
    response = requests.get(URL)
    open(ZIP_PATH, "wb").write(response.content)


def unzip():
    print("Extraindo Firefox 108.0a1...\n")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(DIST_PATH)


def install():
    if not os.path.exists("modules/firefox"):
        download()
        unzip()
