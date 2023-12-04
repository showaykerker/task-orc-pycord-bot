import asyncio
import datetime
import discord
import logging
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from discord.ext import commands
from discord.ext import tasks
from ezcord.internal.dc import discord as dc
from ezcord import log

class Event:
    def __init__(
            self,
            title: str,
            posttime: Optional[datetime.datetime],
            endtime: Optional[datetime.datetime],
            source: str,
            link:str,
            info: str="",
            img: str=None) -> None:
        self.title = title
        self.posttime = posttime
        self.endtime = endtime
        self.source = source
        self.link = link
        self.info = info
        self.img = img
    def __str__(self) -> str:
        return f"<Event> {self.source} {self.title}\n"\
            f"\tposttime: {self.posttime}\n"\
            f"\tendtime: {self.endtime}\n"\
            f"\tinfo: {self.info}\n"\
            f"\timg: {self.img}\n"\
            f"\tlink: {self.link}\n"

class SoupBase:
    def __init__(self, name: str, url: str, use_selenium: bool=False) -> None:
        self.name = name
        self.url = url
        if use_selenium:
            self.options = ChromeOptions()
            self.options.add_argument("--disable-extenstions")
            self.options.add_argument("--headless");
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.get(url)
            self.web = self.driver.page_source
            self.soup = BeautifulSoup(self.web, "html.parser")
        else:
            self.web = requests.get(url)
            self.soup = BeautifulSoup(self.web.text, "html.parser")
    def get_events(self, class_) -> List[Event]:
        return self.soup.find_all("div", class_=class_)
    async def get_driver(self, url: str, use_selenium: bool=False):
        if use_selenium:
            driver = webdriver.Chrome(options=self.options)
            driver.get(url)
            web = driver.page_source
            return BeautifulSoup(web, "html.parser")
        else:
            web = requests.get(url)
            return BeautifulSoup(web.text, "html.parser")

class StreetVoiceSoup(SoupBase):
    def __init__(self) -> None:
        super().__init__('StreetVoice', 'https://streetvoice.com/opportunities/')
    async def get_events(self) -> List[Event]:
        results = []
        for event in super().get_events("border-block oppo-event-item mb-5"):
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
            results.append(Event(title, None, endtime, self.name, link, info, img))
        return results

class BountyHunterSoup(SoupBase):
    def __init__(self) -> None:
        super().__init__(
            'BountyHunter',
            'https://bhuntr.com/tw/competitions?category=119,120,121',
            True)

    async def read_inside(self, url) -> Tuple[Optional[str], Optional[str]]:
        soup = await self.get_driver(url, use_selenium=True)
        content = soup.find("div", class_="bh-page bh-contest-item-page")
        if content is None: return None, None
        if "樂團" in content or "團體" in content or "創作" in content:
            endtime = content.find_all("span", class_="bh-value")[-1].string
            endtime = datetime.datetime.strptime(endtime, "%Y-%m-%d %H:%M") # + relativedelta(months=24)
            img_link = content.find("img", class_="bh-image")["src"]
            return endtime, img_link
        return None, None

    async def get_events(self) -> List[Event]:
        results = []
        for event in super().get_events(class_="bh-title-block"):
            event_info = event.find("a")
            title = event_info.string
            link = "https://bhuntr.com" + event_info["href"]
            endtime, img_link = await self.read_inside(link)
            if endtime is not None:
                if endtime < datetime.datetime.now(): break
                info = ""
                results.append(Event(title, None, endtime, self.name, link, info, img))
        return results

class IdeaShow(SoupBase):
    def __init__(self) -> None:
        super().__init__(
            'IdeaShow',
            'https://news.idea-show.com/tag/樂團徵選/',
            True)
    async def read_inside(self, url) -> Tuple[Optional[str], Optional[str]]:
        soup = await self.get_driver(url, use_selenium=False)
        endtime = soup.find_all("span", class_="event-date")
        if endtime:
            endtime = endtime[-1].string  # 2023-03-31
            endtime = datetime.datetime.strptime(endtime, "%Y-%m-%d")  # + relativedelta(months=3)
            img_link = soup.find("div", class_="post-more-meta-thumbnail").find("img")["src"]
            return endtime, img_link
        return None, None
    async def get_events(self) -> List[Event]:
        results = []
        for event in super.get_events(class_="post-inner post-hover"):
            title_info = event.find("h2", class_="post-title entry-title fittexted_for_post_titles")
            title = title_info.find("a").string
            link = title_info.find("a")["href"]
            endtime, img_link = await self.read_inside(link)
            if endtime is None: continue
            if endtime < datetime.datetime.now(): break
            info = event.find("div", class_="entry excerpt entry-summary fittexted_for_entry").find("p")
            info = info.get_text(strip=True, separator='\n')
            results.append(Event(title, None, endtime, self.name, link, info, img_link))
        return results

class Musico(SoupBase):
    def __init__(self, keyword) -> None:
        super().__init__(
            'Musico',
            f'https://www.musico.com.tw/all-search/?keyword={keyword}&post-cat%5B%5D=36',
            False)
    async def get_events(self) -> List[Event]:
        results = []
        for event in super().get_events("post-list-wrap"):
            try:
                title_info = event.find("h2", class_="entry-title").find('a')
                title = title_info.string
                link = title_info["href"]
                if not ("募集" in title or "徵選" in title): continue
                postdate = event.find("h5").string.split('/')[0]
                postdate = datetime.datetime.strptime(postdate, "%Y.%m.%d")
                if postdate < datetime.datetime.now() - relativedelta(days=7): # - relativedelta(months=36):
                    break
                info = event.find("div", class_="post-excerpt").text.strip().split('\n')[0]
                img = event.find("div", class_="image_wrapper").find("img")["src"]
                results.append(Event(title, postdate, None, self.name, link, info, img))
            except AttributeError:
                log.warning(f"AttributeError: {event}")
        return results

class Ltn(SoupBase):
    def __init__(self, keyword) -> None:
        super().__init__(
            '自由電子報',
            f'https://search.ltn.com.tw/list?keyword={keyword}&type=all&sort=date')
        # &start_time=20231203&end_time=20231204
    async def get_events(self) -> List[Event]:
        results = []
        for event in self.soup.find("ul", class_="list boxTitle").find_all("li"):
            try:
                title_info = event.find("a")
                title = title_info["title"]
                link = title_info["href"]
                info = event.find("p").text.strip()
                if "管樂團" in title or "弦樂團" in title or "絃樂團" in title: continue
                if not ("募集" in title or "徵選" in title or "報名" in title or "開跑" in title) and\
                        not ("募集" in info or "徵選" in info or "報名" in info or "開跑" in info):
                    continue
                postdate = event.find("span", class_="time").string
                postdate = datetime.datetime.strptime(postdate, "%Y/%m/%d")
                if postdate < datetime.datetime.now() - relativedelta(days=700): # - relativedelta(months=36):
                    break
                img = event.find("img")["src"]
                results.append(Event(title, postdate, None, self.name, link, info, img))
            except AttributeError:
                log.warning(f"AttributeError: {event}")
        return results

async def find_audition_info():
    events = []
    log.info("Finding audition info...")
    log.info("From StreetVoice")
    events += await StreetVoiceSoup().get_events()
    log.info("From BountyHunter")
    events += await BountyHunterSoup().get_events()
    log.info("From IdeaShow")
    events += await IdeaShow().get_events()
    log.info("From Musico")
    events += await Musico("樂團徵選").get_events()
    events += await Musico("原創音樂徵選").get_events()
    events += await Musico("創作徵選").get_events()
    log.info("From Ltn")
    events += await Ltn("樂團徵選").get_events()
    events += await Ltn("音樂徵選").get_events()
    log.info("Done")
    for e in events:
        print(e)
    return events

class InfoTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.find_audition_info_task.start()
        self.events = []

    def cog_unload(self):
        self.find_audition_info_task.stop()

    async def send_to_channels(self, events):
        async for guild in self.bot.fetch_guilds():
            channels = await guild.fetch_channels()
            for channel in channels:
                # print(channel.name)
                if channel.name == "task-orc":
                    embed = dc.Embed(
                        title = "找到的Auditions",
                        color=dc.Colour.green()
                    )
                    for event in events:
                        embed.add_field(
                            name=event.title,
                            value=f"截止時間：{event.endtime}\n"\
                                f"```{event.info[:50]}...```\n"\
                                f"[Check it on {event.source}](<{event.link}>)",
                            inline=True)
                    await channel.send(embed=embed)

    @tasks.loop(time=datetime.time(hour=16))  # Run at 00:00 everyday
    # @tasks.loop(minutes=10.0)
    async def find_audition_info_task(self):
        events = await find_audition_info()
        await self.send_to_channels(events)

    @find_audition_info_task.before_loop
    async def before_periodic_task(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready before starting the task


def setup(bot):
    bot.add_cog(InfoTask(bot))

if __name__ == '__main__':
    asyncio.run(find_audition_info())
