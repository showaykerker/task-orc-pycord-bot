import asyncio
import datetime
import discord
import requests

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext import tasks
from ezcord.internal.dc import discord as dc

class Event:
    def __init__(self, title: str, endtime: datetime.datetime, source: str, link:str, info: str="", img: str=None) -> None:
        self.title = title
        self.endtime = endtime
        self.source = source
        self.link = link
        self.info = info
        self.img = img
    def __str__(self) -> str:
        return f"<Event> {self.source} {self.title}: {self.endtime}"

class SoupBase:
    def __init__(self, name: str, url: str, use_selenium: bool=False) -> None:
        self.name = name
        self.url = url
        if use_selenium:
            self.options = FirefoxOptions()
            self.options.add_argument("--headless")
            self.driver = webdriver.Firefox(options=self.options)
            self.driver.get(url)
            self.web = self.driver.page_source
            self.soup = BeautifulSoup(self.web, "html.parser")
        else:
            self.web = requests.get(url)
            self.soup = BeautifulSoup(self.web.text, "html.parser")
    def get_events(self) -> List[Event]:
        pass
    def get_driver(self, url: str):
        driver = webdriver.Firefox(options=self.options)
        driver.get(url)
        web = driver.page_source
        return BeautifulSoup(web, "html.parser")

class StreetVoiceSoup(SoupBase):
    def __init__(self) -> None:
        super().__init__('StreetVoice', 'https://streetvoice.com/opportunities/')
    def get_events(self) -> List[Event]:
        results = []
        events = self.soup.find_all("div", class_="border-block oppo-event-item mb-5")
        for event in events:

            endtime = event.find("h4", class_="text-truncate").string.strip()
            if "結束" in endtime: continue

            title_div = event.find("h2", class_="max-two")
            title = title_div.find("a").string
            link = "https://streetvoice.com" + title_div.find("a", href=True)["href"]
            info = event.find("p", class_="max-three").string
            endtime = endtime.split("・")[1]
            date_string, time_string, _ = endtime.split(" ") # "2023-12-19 23:59"
            endtime = datetime.datetime.strptime(f"{date_string} {time_string}", "%Y-%m-%d %H:%M")
            img = event.find("img")["src"]
            results.append(Event(title, endtime, self.name, link, info, img))
        return results

class BountyHunterSoup(SoupBase):
    def __init__(self) -> None:
        super().__init__('BountyHunter', 'https://bhuntr.com/tw/competitions?category=119,120,121', True)

    def read_inside(self, url) -> Tuple[Optional[str], Optional[str]]:
        soup = self.get_driver(url)
        content = soup.find("div", class_="bh-page bh-contest-item-page")
        if "樂團" in content or "團體" in content:
            endtime = content.find_all("span", class_="bh-value")[-1].string
            endtime = datetime.datetime.strptime(endtime, "%Y-%m-%d %H:%M")
            img_link = content.find("img", class_="bh-image")["src"]
            return endtime, img_link
        return None, None

    def get_events(self) -> List[Event]:
        results = []
        events = self.soup.find_all("div", class_="bh-title-block")
        for event in events:
            event_info = event.find("a")
            title = event_info.string
            link = "https://bhuntr.com" + event_info["href"]
            endtime, img_link = self.read_inside(link)
            if endtime is not None:
                results.append(Event(title, endtime, self.name, link, "", img))
        return results

async def find_audition_info():
    events = []
    events += StreetVoiceSoup().get_events()
    # events += BountyHunterSoup().get_events()
    return events

class InfoTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = bot.db
        self.find_audition_info_task.start()
        self.events = []

    def cog_unload(self):
        self.find_audition_info_task.stop()

    @tasks.loop(time=datetime.time(hour=16))  # Run at 00:00 everyday
    async def find_audition_info_task(self):
        self.events = await find_audition_info()

    @find_audition_info_task.before_loop
    async def before_periodic_task(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready before starting the task

def setup(bot):
    bot.add_cog(InfoTask(bot))

if __name__ == '__main__':
    asyncio.run(find_audition_info())