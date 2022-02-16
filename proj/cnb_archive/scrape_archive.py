from datetime import datetime
from time import sleep

import requests
from pandas import DataFrame
from bs4 import BeautifulSoup

CNB_NEWS_ARCHIVE_URL = ("https://www.cnb.gov.sg/newsandevents/news/archive"
                        "/archivesubnews/index/{year}")

event_write_up = []
event_titles = []
dates = []
links = []
for year in range(2012, 2023):
    resp = requests.get(CNB_NEWS_ARCHIVE_URL.format(year=year))
    soup = BeautifulSoup(resp.text, 'html.parser')
    timeline_panels = soup.find_all('div', 'tl-heading')
    for tp in timeline_panels:
        event_title = tp.find('h4').get_text()
        event_link = tp.find('a').get('href')
        event_date = datetime.strptime(tp.find('p').get_text(), ' %d %b %Y')
        event_date = event_date.strftime('%Y-%m-%d')
        dates.append(event_date)
        links.append('https://www.cnb.gov.sg' + event_link)
        event_titles.append(event_title)
        article_resp = requests.get(links[-1])
        if article_resp.status_code != 200:
            continue
        art_soup = BeautifulSoup(article_resp.text, 'html.parser')
        p_tags = art_soup.find_all('p')
        write_up = ' '.join([p_tag.text for p_tag in p_tags])
        event_write_up.append(write_up)
        sleep(0.1)

DataFrame(
  {'title': event_titles,
   'date': dates,
   'link': links,
   'article': event_write_up}).to_csv("cnb_articles.csv")
