from bs4 import BeautifulSoup as bs
import requests
from constants import RESOURCE_URL


def parse_response(soup):
    d = {}
    for item in soup.find("tbody", {"class": "list"}).findChildren("tr", recursive=False):
        row = item.findChildren("td")[0]
        d[row.text.strip()] = {
            "bank": row["data-title"],
            "card": row["data-card"]
        }
    return d


def get_minfin_data(currency):
    r = requests.get(RESOURCE_URL + currency)
    soup = bs(r.text, features="lxml")
    msg = "Bank{shft}Сash Register{shft}Card".format(shft="\t"*4)
    for k, v in parse_response(soup).items():
        msg += f"\n{k}\t{v['bank']}\t{v['card']}"
    return msg
