import requests
from bs4 import BeautifulSoup
import os

# WEBSITE = "https://www.auto-brochures.com/audi.html"
WEBSITE = "https://www.auto-brochures.com"  # Spletna stran, iz katere rabimo podatke
BRANDS = ["audi", "mazda"]  # Seznam vseh znamk, za katere zelimo pdf
ONLY_RECENT = False  # Ce je True, potem downloadamo samo najnovejso letnico


def get_data():
    ze_zloudan = []

    for brand in BRANDS:
        os.makedirs(f"data/pdfs/{brand}", exist_ok=True)

    for brand in BRANDS:

        website = WEBSITE + "/" + brand + ".html"

        response = requests.get(website)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a")

        for link in links:

            href = link.get("href")

            if href and ".pdf" in href.lower():

                pdf_name = href.split("/")[-1]

                avto = pdf_name.split("_")[:-1]
                avto = "_".join(avto)

                if ONLY_RECENT and avto in ze_zloudan:
                    continue

                pdf_path = f"data/pdfs/{brand}/{pdf_name}"

                if os.path.exists(pdf_path):
                    continue

                ze_zloudan.append(avto)

                print("Downloadam " + str(pdf_name))

                response = requests.get(href)

                with open(pdf_path, "wb") as f:
                    f.write(response.content)

                # break

    print("end")


if __name__ == "__main__":
    get_data()
