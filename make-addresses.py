from pathlib import Path

from definitions import PlaceRef
from georef_engine import ChatGptApi


ESTABLISHMENTS_TXT = 'establishments.txt'
PLACE_REFS_DIR = 'addresses'


def load_addresses() -> list[str]:
    with open(ESTABLISHMENTS_TXT) as f:
        return [x.strip().strip(',') for x in f.read().splitlines() if x.strip()]


def make_places(addresses: list[str]) -> list[PlaceRef]:
    return [PlaceRef(name=a) for a in addresses]


if __name__ == '__main__':
    places: list[PlaceRef] = make_places(load_addresses())
    api = ChatGptApi()

    for p in places:
        api.geocoding_prompt(place=p)
        p.to_file(PLACE_REFS_DIR)
