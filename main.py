from modules import firefox
import Scraping


def main():
    firefox.install()
    Scraping.generate_json()


main()
