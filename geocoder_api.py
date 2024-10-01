import time
import traceback
from pathlib import Path
from queue import Queue, Empty

from geopy import Location
from geopy.exc import GeocoderServiceError
from geopy.geocoders import GoogleV3

from common import logger, MAX_RETRIES, MAX_REQUESTS_PER_MINUTE
from definitions import PlaceRef, Credentials


class Geocoder(GoogleV3):
    queue: Queue
    results: list[PlaceRef]
    cache: dict   # str address : Location
    __min_time_between_requests: float = 60 / MAX_REQUESTS_PER_MINUTE    # seconds
    __last_request_timestamp: float = 0

    def __init__(self, check_api: bool = True) -> None:
        self.queue = Queue()
        self.results = []
        self.cache = {}

        super().__init__(api_key=Credentials.load().google, timeout=5)
        self.check_api() if check_api else None

    def geocode(self, address: str, exactly_one: bool = True) -> (float, float):     # ignore warning from IDE

        if not exactly_one:
            raise NotImplemented('this geocoding approach supports exactly one point per address')

        try:

            response: Location = super().geocode(address, exactly_one=exactly_one)
            if response:
                xy = self.cache[address] = response.longitude, response.latitude   # update cache

            logger.warning(
                f"Received multiple ({len(response)}) locations for '{address}'"
            ) if (isinstance(response, list) and len(response) > 1) else None

            return xy
        except GeocoderServiceError:
            logger.error(f"Exception caught when geocoding '{address}'")
            logger.error(traceback.format_exc())

    def geocode_with_cache(self, address: str) -> (float, float):

        # look up in cache first
        if address in self.cache:
            logger.info(f"Found cached value for {address}")
            return self.cache[address]

        begin = time.perf_counter()
        xy = self.geocode(address, exactly_one=True)
        self.__last_request_timestamp = time.perf_counter()
        elapsed = self.__last_request_timestamp - begin

        msg = "{} \t ({} ms) \t {} {}".format(
            'OK' if xy else 'FAILED',
            int(elapsed * 1000),
            address,
            tuple(round(i, 4) for i in xy)
        )
        logger.info(msg) if xy else logger.warning(msg)
        return xy

    def check_api(self):
        """ Dummy request to ensure API is working and key is valid. """

        response: Location = super().geocode(
            query='Berlin', components={"country": 'Germany'},
        )
        if not all([
            response,
            response.point
        ]):
            raise Exception(f'could not perform API check call, key {self.api_key[:5]}')
        else:
            logger.info(f'Google Geocoder API works, API key {self.api_key[:5]}... good')


if __name__ == '__main__':
    api = Geocoder(check_api=True)
