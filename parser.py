from bs4 import BeautifulSoup as bs
import requests
from constants import RESOURCE_URL
import prettytable as pt


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
    # TODO: add restriction for max bank in one message
    r = requests.get(RESOURCE_URL + currency)
    soup = bs(r.text, features="lxml")
    table = pt.PrettyTable(["Bank", "Cash Register(Bit/Ask)", "Card(Bit/Ask)"])
    banks_number = 0
    for bank, rate in parse_response(soup).items():
        if banks_number == 25:
            break
        table.add_row([bank, rate["bank"], rate["card"]])
        banks_number += 1
    msg = "<pre>{}</pre>".format(table)
    return msg
