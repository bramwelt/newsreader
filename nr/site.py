"""
Newsreader - Site

Copyright (c) 2018 Trevor Bramwell <trevor@bramwell.net>
SPDX-License-Identifier: Apache-2.0
"""
import requests
from bs4 import BeautifulSoup

from .article import Article


class Site():
    """A site represents a news source and contains a list of articles
       after being parsed"""

    def __init__(self, url):
        self.url = url
        self.articles = []

    def parse(self):
        """Parse a site and extract the articles"""
        # logging.info("Parsing: %s", self.url)
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, 'html.parser')
        links = soup.body.ul.find_all('li')
        for link in links:
            # logging.info("Adding article: %s", link)
            href = "%s%s" % (self.url, link.a['href'])
            article = Article(link.text, href)
            self.articles.append(article)

    def get_articles(self):
        """Return articles from the site, requires the site have been
           parsed first"""
        return self.articles
