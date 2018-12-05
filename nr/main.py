#!/usr/env/bin python
"""
Newsreader - Main

Copyright (c) 2018 Trevor Bramwell <trevor@bramwell.net>
SPDX-License-Identifier: Apache-2.0
"""
from datetime import timedelta

import urwid
from urwid import curses_display

import requests
import requests_cache
from bs4 import BeautifulSoup

# import logging
# logging.basicConfig(filename='nr.log', level=logging.INFO)

# Transparently cache requests so we don't constantly hit the server,
# and expire any old values when newsreader is started.
requests_cache.install_cache('nr_cache', expire_after=timedelta(hours=1))
requests_cache.core.remove_expired_responses()

# Remap up/down pageup/pagedown to VIM bindings
urwid.command_map['k'] = 'cursor up'
urwid.command_map['j'] = 'cursor down'
urwid.command_map['ctrl b'] = 'cursor page up'
urwid.command_map['ctrl f'] = 'cursor page down'


class Site():
    """News site containing links to news articles
       (ex: text.npr.org, lite.cnn.org)"""

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


class Article(urwid.Button):
    """News Article - A button that when clicked displays the article"""
    button_left = urwid.Text("")
    button_right = urwid.Text("")

    def __init__(self, label, link, on_press=None, user_data=None):
        super(Article, self).__init__(label, on_press, user_data)
        self.link = link
        self.text = []

    def parse(self):
        """Parse an article and extract the contents"""
        if not self.text:
            page = requests.get(self.link)
            soup = BeautifulSoup(page.content, 'html.parser')
            for i, par in enumerate(soup.body.find_all('p')[2:]):
                # NPR Specific
                if i < 2:
                    self.text.append(
                        urwid.AttrMap(urwid.Text(par.text), 'bold'))
                else:
                    self.text.append(urwid.Divider())
                    self.text.append(urwid.Text(par.text))


class App():
    """Newsreader App

    This is the main view for newsreader and contains a browsable list
    of articles.
    """
    def __init__(self):
        """App Initialization"""
        self.pull_articles()
        self.refresh()
        self.palette = [
            ('reversed', 'standout', ''),
            ('bold', 'default,bold', '')]
        self.loop = None

    def run(self):
        """Starts the main loop"""
        self.loop = urwid.MainLoop(
            self.main,
            palette=self.palette,
            screen=curses_display.Screen(),
            unhandled_input=self.other_input)
        self.loop.run()

    def pull_articles(self):
        """Downloads the list of articles"""
        site = Site('https://text.npr.org')
        site.parse()
        self.articles = site.get_articles()

    def refresh(self):
        """Clear the cache and update the list of articles in the main
        view"""
        self.body = [urwid.Text("News"), urwid.Divider(u'-')]
        for article in self.articles:
            urwid.connect_signal(article, 'click', self.show_article)
            self.body.append(
                urwid.AttrMap(article, None, focus_map='reversed'))

        self.main = urwid.ListBox(urwid.SimpleFocusListWalker(self.body))
        self.view = urwid.ListBox([])

    def show_article(self, article):
        """Display the selected article in a new window"""
        article.parse()
        self.view.body = article.text
        self.loop.widget = urwid.Padding(
            self.view,
            align='center',
            width=('relative', 40),
            min_width=70)

    def close_article(self):
        """Closes the article by setting the view back to the article
        browser"""
        self.loop.widget = self.main

    def other_input(self, key):
        """Handle application inputs"""
        if key in ('b',):
            self.close_article()
        if key in ('r',):
            requests_cache.core.remove_expired_responses()
            self.pull_articles()
            self.refresh()
            # This is used as a misnomer
            self.close_article()
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()


def main():
    """Run the app"""
    App().run()


if __name__ == "__main__":
    main()
