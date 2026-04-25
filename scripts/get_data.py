import requests
from bs4 import BeautifulSoup
import os

# WEBSITE = "https://www.auto-brochures.com/audi.html"
WEBSITE = "https://www.auto-brochures.com"  # Spletna stran, iz katere rabimo podatke
BRANDS = ["audi", "mazda"]  # Seznam vseh znamk, za katere zelimo pdf
# BRANDS = ["audi"]
ONLY_RECENT = False  # Ce je True, potem downloadamo samo najnovejso letnico


def get_data():

    os.makedirs("data", exist_ok=True)
    ze_zloudan = []

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

                if os.path.exists("data/" + pdf_name):
                    continue

                ze_zloudan.append(avto)

                print("Downloadam " + str(pdf_name))

                response = requests.get(href)

                with open("data/" + pdf_name, "wb") as f:
                    f.write(response.content)

                # break

    print("end")


if __name__ == "__main__":
    get_data()
