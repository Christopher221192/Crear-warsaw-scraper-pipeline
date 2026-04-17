import random
from fake_useragent import UserAgent

def get_random_headers():
    ua = UserAgent(platforms=['pc'])
    return {
        "User-Agent": ua.random,
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

TARGET_URLS = {
    "otodom": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?ownerTypeSingleSelect=DEVELOPER&roomsNumber=%5B2%2C%5D&buildYear=%5B2027%2C2027%5D",
    "rynekpierwotny": "https://rynekpierwotny.pl/s/warszawa/?rooms=2,3,4,5,6&year_of_handover=2027"
}
