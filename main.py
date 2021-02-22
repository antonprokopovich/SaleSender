from collections import namedtuple

from telethon import TelegramClient
from telethon import functions, types
from telethon.tl.functions.contacts import GetLocatedRequest

from config import EnvironmentConfig


Location = namedtuple("location", ["lat", "long"])


SCAN_RADIUS = 50
SENDER_LOCATION = Location(lat=7.13, long=7.13)


cfg = EnvironmentConfig()


class Sender:
    def __init__(self):
        self.__cli = self.__create_client()

    @staticmethod
    def __create_client() -> TelegramClient:
        return TelegramClient(
            session="anon",
            api_id=int(cfg.TG_API_ID),
            api_hash=cfg.TG_API_HASH,
        )

    async def __get_located(self, loc, rad):
        result = await self.__cli(GetLocatedRequest(
            geo_point=types.InputGeoPoint(
                lat=loc.lat,
                long=loc.long,
                accuracy_radius=rad
            ),
            self_expires=42
        ))

        print(result.stringify())
        return result

    def get_people_nearby(self, loc=SENDER_LOCATION, rad=SCAN_RADIUS):
        with self.__cli as client:
            res = client.loop.run_until_complete(self.__get_located(loc, rad))

            return res


if __name__ == "__main__":
    s = Sender()

    r = s.get_people_nearby()

