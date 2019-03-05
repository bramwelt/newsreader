"""
Newsreader - Article

Copyright (c) 2018 Trevor Bramwell <trevor@bramwell.net>
SPDX-License-Identifier: Apache-2.0
"""
import urwid
import requests
from bs4 import BeautifulSoup


class Article(urwid.SelectableIcon):
    """Articles represent pages from a news Site. They are parsed and """

    def __init__(self, text, link):
        # Set the cursor to just beyond the article text so it is
        # 'hidden'
        curs_pos = len(text)+1
        super(Article, self).__init__(text, cursor_position=curs_pos)
        self.site = "NPR"
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
