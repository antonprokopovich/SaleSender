import datetime
import logging
import time
import typing as t
from collections import namedtuple
from dataclasses import dataclass


from telethon import TelegramClient
from telethon import types
from telethon.tl.functions.contacts import GetLocatedRequest

from config import EnvironmentConfig
from sales_congif import sales_data


Location = namedtuple("location", ["lat", "long"])


# Каждые сколько минут делать рассылку
WORK_RATE = 3
# Радиус поиска людей рядом
SCAN_RADIUS = 1

# Локация `заведения` для тестов
PERLOVKA_LOCATION = Location(lat=55.889070, long=37.726270)


cfg = EnvironmentConfig()


@dataclass
class Address:
    """Модель адресса заведения"""
    location: Location
    city: str
    street: str
    building: str
    # Корпус, если есть
    korpus: str = None
    # Кабинетб, если есть
    office: int = None


@dataclass
class Shop:
    """Модель заведения"""
    type: str
    name: str
    address: Address


@dataclass
class Sale:
    """Модель акции"""
    name: str
    text: str
    shop: Shop
    start_date: datetime.datetime
    end_date: datetime.datetime

    def to_msg(self) -> str:
        """Конвертирует объект акции в строку-сообщение для отправки"""
        return (
            f"""**{self.shop.type.capitalize()} "{self.shop.name}" проводит акцию:""" 
            f"""{self.name}**\n\n{self.text}\n\n"""
            f"""Приходите по адрессу __{self.shop.address.street}, {self.shop.address.building}__.\n\n"""
            f"""Акция действует с {self.start_date:%d.%m.%y} по {self.end_date:%d.%m.%y}."""
        )


def sales_from_config() -> t.List[Sale]:
    """
    Парсит конфиг-файл с данными об акциях.

    *** Временное решения для тестов без использования реальной базы данных. ***

    Returns:
        Массив с объектами акций
    """
    res = []
    for d in sales_data:
        shop = Shop(
            type=d['shop']['type'],
            name=d['shop']['name'],
            address=Address(
                location=Location(
                    lat=d['shop']['address']['location']['latitude'],
                    long=d['shop']['address']['location']['longitude'],
                ),
                city=d['shop']['address']['city'],
                street=d['shop']['address']['street'],
                building=d['shop']['address']['building'],
            )
        )
        for s in d['shop']['sales']:
            s = Sale(
                name=s['name'],
                text=s['text'],
                shop=shop,
                start_date=datetime.datetime.strptime(s['starts'], '%d.%m.%y'),
                end_date=datetime.datetime.strptime(s['ends'], '%d.%m.%y'),
            )
            res.append(s)
    return res


class Sender:
    def __init__(self):
        self.__cli = self._create_client()

    @staticmethod
    def _create_client() -> TelegramClient:
        return TelegramClient(
            session="anon",
            api_id=int(cfg.TG_API_ID),
            api_hash=cfg.TG_API_HASH,
        )

    def _get_people_nearby(self, loc, rad=SCAN_RADIUS) -> t.List[types.User]:
        with self.__cli as client:
            res = client.loop.run_until_complete(self._get_located(loc, rad))
            return res.users

    async def _get_located(self, loc, rad):
        result = await self.__cli(GetLocatedRequest(
            geo_point=types.InputGeoPoint(
                lat=loc.lat,
                long=loc.long,
                accuracy_radius=rad
            ),
            self_expires=42
        ))
        return result

    async def _send(self, user: types.User, msg: str):
        logging.info(f'Sending to {user.first_name}')

        user = types.InputPeerUser(user.id, user.access_hash)
        await self.__cli.send_message(user, msg)

    def run(self):
        sales = sales_from_config()
        while True:
            # Обычно будет не более 1 акции, чтобы не спамить кучей сообщений за раз.
            # Но оставляем возможность, что их будет несколько
            for s in sales:
                users = self._get_people_nearby(loc=s.shop.address.location)
                for u in users:
                    with self.__cli as client:
                        client.loop.run_until_complete(
                            self._send(u, s.to_msg())
                        )
            time.sleep(WORK_RATE * 60)

    # Для тестов
    def test_run_ones(self, test_user_fn: str = 'Мама'):
        """
        Отправляет только юзеру/контанту с указанным именем

        Args:
            test_user_fn: Имя целевого юзера/контакта
        """
        sales = sales_from_config()
        users = self._get_people_nearby(loc=PERLOVKA_LOCATION)
        for u in users:
            for s in sales:
                if u.first_name == test_user_fn:
                    with self.__cli as client:
                        client.loop.run_until_complete(
                            self._send(u, s.to_msg())
                        )


if __name__ == "__main__":
    sndr = Sender()

    try:
        sndr.run()
    except KeyboardInterrupt:
        logging.info("Shutdown requested... exiting")

    # sndr.test_run_ones()
