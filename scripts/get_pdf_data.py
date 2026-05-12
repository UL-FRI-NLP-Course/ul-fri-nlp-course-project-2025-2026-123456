import argparse
import os
import sys
import re
import requests
from bs4 import BeautifulSoup


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.config import PDF_ROOT

# WEBSITE = "https://www.auto-brochures.com/audi.html"
WEBSITE = "https://www.auto-brochures.com"  # Spletna stran, iz katere rabimo podatke
BRANDS = ["audi", "bmw", "buick","cadillac", "chevrolet", "chrysler", "dodge", "ford", "honda", "hyundai", "infiniti", "jeep", "kia", "land rover", "lexus", "mazda", "mercedes-benz", "mini", "mitsubishi", "nissan", "porsche", "ram", "subaru", "toyota", "volkswagen", "volvo"]  # Seznam vseh znamk, za katere zelimo pdf
ONLY_RECENT = False  # Ce je True, potem downloadamo samo najnovejso letnico
MIN_YEAR = None  # Minimalna letnica za download (ce je None, potem downloadamo vse, -1 pomeni samo najnovejso) 

def download_pdf(url, save_path):
    if os.path.exists(save_path):
        return
    print(f"Downloading: {os.path.basename(save_path)}")
    response = requests.get(url)
    with open(save_path, "wb") as f:
        f.write(response.content)

def get_model_year(pdf_name):
    match = re.search(r'(\d{4})', pdf_name)
    if match:
        return int(match.groups()[-1])
    return 0

def get_brand_model_year(pdf_name):
    split = pdf_name.replace(".pdf", "").split("_")
    brand = split[0]
    model = split[1].split()[1:]
    model = " ".join(model)
    year = get_model_year(pdf_name)
    return brand, model, year
    

def get_data(brands, min_year=None, only_latest=False):
    download_all = min_year is None and only_latest is False

    for brand in brands:
        os.makedirs(f"{PDF_ROOT}/{brand}", exist_ok=True)

    for brand in brands:

        website = WEBSITE + "/" + brand + ".html"

        response = requests.get(website)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a")

        dicti = {}
        for link in links:
            href = link.get("href")
            if href and ".pdf" in href.lower():
                pdf_name = href.split("/")[-1]

                if download_all:
                    download_pdf(href, f"{PDF_ROOT}/{brand}/{pdf_name}")
                    continue

                brand, model, model_year = get_brand_model_year(pdf_name)
                
                if model not in dicti:
                    dicti[model] = []

                dicti[model].append((model_year, href))

        if download_all:
            return
        
        # filter by year
        for model, versions in dicti.items():
            download_from = 0
            if min_year is not None:
                download_from = min_year

            if only_latest:
                latest_year = max(versions, key=lambda x: x[0])[0]
                download_from = max(latest_year, download_from)

            versions = filter(lambda x: x[0] >= download_from, versions)

            for model_year, href in versions:
                pdf_name = href.split("/")[-1]
                download_pdf(href, f"{PDF_ROOT}/{brand}/{pdf_name}")
            

    print("end")


def filter_data(brands, min_year=None, only_latest=False):
    for downloaded_brand in os.listdir(PDF_ROOT):
        if downloaded_brand not in brands:
            response = input(f"Brand '{downloaded_brand}' is not in the specified brands list. Do you want to delete its data? (y/n): ")
            if response.lower() == "y":
                brand_path = os.path.join(PDF_ROOT, downloaded_brand)
                for filename in os.listdir(brand_path):
                    file_path = os.path.join(brand_path, filename)
                    os.remove(file_path)
                os.rmdir(brand_path)
            continue

        brand_path = os.path.join(PDF_ROOT, downloaded_brand)
        if not os.path.isdir(brand_path):
            continue

        dicti = {}
        for filename in os.listdir(brand_path):
            if filename.endswith(".pdf"):
                brand, model, model_year = get_brand_model_year(filename)

                if model not in dicti:
                    dicti[model] = []

                full_path = os.path.join(brand_path, filename)
                dicti[model].append((model_year, full_path))

        # filter by year
        for model, versions in dicti.items():
            remove_below = 9999
            if min_year is not None:
                remove_below = min_year

            if only_latest:
                latest_year = max(versions, key=lambda x: x[0])[0]
                remove_below = max(latest_year, remove_below)

            delete_versions = filter(lambda x: x[0] < remove_below, versions)

            for model_year, file_path in delete_versions:
                pdf_name = os.path.basename(file_path)
                print(f"Deleting {pdf_name} (model year {model_year})")
                os.remove(file_path)


def parse_args():
    parser = argparse.ArgumentParser(description="Download or filter car brochure data.")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    def _add_shared(p):
        p.add_argument(
            "--brands",
            nargs="+",
            default=BRANDS,
            help="One or more brands to operate on, for example: --brands toyota mazda",
        )
        p.add_argument(
            "--latest",
            action="store_true",
            default=ONLY_RECENT,
            help="Only use the most recent brochure for each model",
        )
        p.add_argument(
            "--min-year",
            type=int,
            default=MIN_YEAR,
            help="Minimum year for filtering brochures (only use brochures from this year or later)",
        )

    dl = subparsers.add_parser("download", help="Download brochure PDFs")
    _add_shared(dl)

    fl = subparsers.add_parser("filter", help="Filter existing brochure data")
    _add_shared(fl)

    return parser.parse_args()

def main():
    args = parse_args()

    # default to download if no subcommand provided
    if args.command is None or args.command == "download":
        get_data(brands=args.brands, min_year=args.min_year, only_latest=args.latest)
        return

    if args.command == "filter":
        filter_data(brands=args.brands, min_year=args.min_year, only_latest=args.latest)
        return

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
