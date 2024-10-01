import json
from pathlib import Path

from definitions import PlaceRef, Address
from geocoder_api import Geocoder


PLACE_REFS_DIR = 'addresses'
GEOCODED_PLACES_DIR = 'geocoded'
IGNORE_FLAG = 'NO_ADDRESS'

APPEND_TO_PROGRESS = True       # will overwrite when False
FORCE_OVERWRITE = False


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


if __name__ == '__main__':
    items = load_items()

    api = Geocoder(check_api=True)

    for i in items:
        if IGNORE_FLAG in i.raw_gpt:
            print(f'WARN: skipped empty address for {i.name}')
            continue
        for a in i.refs:
            lonlat = api.geocode_with_cache(address=a.text)
            a.lon, a.lat = lonlat   # in place

        i.to_file(directory=GEOCODED_PLACES_DIR)
