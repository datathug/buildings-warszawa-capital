import json
from pathlib import Path
import pandas as pd

from definitions import PlaceRef, Address

PLACE_REFS_DIR = 'geocoded'
GEOCODED_PLACES_CSV = 'geocoded_places.csv'


def load_items() -> list[PlaceRef]:
    files = Path(PLACE_REFS_DIR).glob('*.json')
    data: list[PlaceRef] = []

    for fp in files:
        with open(str(fp.resolve()), 'r') as f:
            place = PlaceRef(**json.load(f))
            place.refs = [Address(**x) for x in place.refs]
            data.append(place)

    addr_count = sum([len(x.refs) for x in data])
    print(f'Retrieved {len(data)} PlaceRefs from disk. Total N adresses {addr_count}')
    return data


def place_to_rows(place: PlaceRef) -> list[list[str]]:
    rows = []
    for a in place.refs:
        rows.append([
            a.text, place.name, a.lon, a.lat
        ])
    return rows


def flatten(l: list):
    return [val for sublist in l for val in sublist]


if __name__ == '__main__':
    places = load_items()
    rows_unflattened = [place_to_rows(p) for p in places]
    rows = {
        i: r for i, r in enumerate(flatten(rows_unflattened))
    }

    df = pd.DataFrame.from_dict(rows, orient="index", columns=['address', 'establishment', 'lon', 'lat'])
    df.to_csv(GEOCODED_PLACES_CSV, index=False)
