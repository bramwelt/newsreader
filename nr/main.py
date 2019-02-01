#!/usr/env/bin python
"""
Newsreader - Main

Copyright (c) 2018 Trevor Bramwell <trevor@bramwell.net>
SPDX-License-Identifier: Apache-2.0
"""
from string import digits
from datetime import timedelta
from configparser import SafeConfigParser
from os.path import expanduser

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


def getlist(option):
    """ConfigParser method for extracting list from config file"""
    return [item.strip() for item in option.split(',')]


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


class Article(urwid.SelectableIcon):
    """News Article - A button that when clicked displays the article"""

    def __init__(self, text, link):
        # Set the cursor to just beyond the article text so it is
        # 'hidden'
        curs_pos = len(text)+1
        super(Article, self).__init__(text, cursor_position=curs_pos)
        self.link = link
        self.parsed = False
        self.body = []

    def keypress(self, size, key):
        """Handle keypresses by emitting signals"""
        if key == 'enter':
            # Emit a 'select' event so we can handle key presses in
            # another place.
            urwid.emit_signal(self, 'select', self)
            return None
        return key

    def parse(self):
        """Parse an article and extract the contents"""
        if not self.parsed:
            page = requests.get(self.link)
            soup = BeautifulSoup(page.content, 'html.parser')
            for i, par in enumerate(soup.body.find_all('p')[2:]):
                # NPR Specific
                if i < 2:
                    self.body.append(
                        urwid.AttrMap(urwid.Text(par.text), 'bold'))
                else:
                    self.body.append(urwid.Divider())
                    self.body.append(urwid.Text(par.text))


urwid.register_signal(Article, 'select')


class App():
    """Newsreader App

    This is the main view for newsreader and contains a browsable list
    of articles.
    """
    defaults = {
        'newsreader': {
            'width': 40,
            'align': 'center',
            'sites': 'https://text.npr.org',
        },
    }

    def __init__(self):
        """App Initialization"""
        self.init_config()
        self.pull_articles()
        self.refresh()
        self.palette = [
            ('reversed', 'standout', ''),
            ('bold', 'default,bold', '')]
        self.loop = None

    def init_config(self):
        """Initialize configuration from a config file"""
        self.config = SafeConfigParser(converters={'list': getlist})
        self.config.read_dict(self.defaults)
        self.config.read(['nr.ini', expanduser('~/.config/nr.ini')],
                         encoding='utf-8')

    def run(self):
        """Starts the main loop"""
        self.loop = urwid.MainLoop(
            self.main,
            palette=self.palette,
            screen=curses_display.Screen(),
            unhandled_input=self.other_input)
        self.loop.run()

    def get_config(self, item):
        """Curry function to get configuration from the config file"""
        section = 'newsreader'
        if item in ['width']:
            return self.config.getint(section, item)
        if item in ['sites']:
            return self.config.getlist(section, item)  # pylint: disable=E1101
        return self.config.get(section, item)

    def pull_articles(self):
        """Downloads the list of articles"""
        self.articles = []
        for site in self.get_config('sites'):
            tmp_site = Site(site)
            tmp_site.parse()
            self.articles.extend(tmp_site.get_articles())

    def refresh(self):
        """Update the list of articles in the main
        view"""
        self.body = [urwid.Text("News"), urwid.Divider(u'-')]
        for i, article in enumerate(self.articles):
            urwid.connect_signal(article, 'select', self.show_article)
            article_num = (3, urwid.Text(str(i+1), align='right'))
            column_div = (1, urwid.Divider())
            column = urwid.Columns([article_num, column_div, article])
            self.body.append(
                urwid.AttrMap(column, None, focus_map='reversed'))

        self.main = urwid.ListBox(urwid.SimpleFocusListWalker(self.body))
        self.view = urwid.ListBox([])

    def show_article(self, article):
        """Display the selected article in a new window"""
        article.parse()
        self.view.body = article.body
        self.loop.widget = urwid.Padding(
            self.view,
            align=self.get_config('align'),
            width=('relative', self.get_config('width')),
            min_width=72,
            left=2,
            right=2)

    def hide_article(self):
        """Hides the article by setting the view back to the article
        browser"""
        self.loop.widget = self.main

    def other_input(self, key):
        """Handle application inputs"""
        if key in ('b',):
            self.hide_article()
        if key in ('r',):
            # Clear the cache and update the article list
            requests_cache.core.remove_expired_responses()
            self.pull_articles()
            self.refresh()
            self.hide_article()
        if key in digits:
            row = int(key)
            if row == 0:
                row = 10
            self.main.set_focus(row+1)
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()


def main():
    """Run the app"""
    App().run()


if __name__ == "__main__":
    main()
