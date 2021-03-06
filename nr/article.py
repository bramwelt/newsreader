"""
Newsreader - Article

Copyright (c) 2018 Trevor Bramwell <trevor@bramwell.net>
SPDX-License-Identifier: Apache-2.0
"""
import logging
import urwid
import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)


class Article(urwid.SelectableIcon):
    """Articles represent pages from a news Site."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, site, linktext, url):
        # Set the cursor to just beyond the article text so it is
        # 'hidden'
        curs_pos = len(linktext)+1
        super(Article, self).__init__(linktext, cursor_position=curs_pos)
        self.site = site
        self.url = url
        self.parsed = False
        self.title = None
        self.date = None
        self.author = None
        self.links = {}
        self.section = "default"
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
            self.parsed = True
            page = requests.get(self.url)
            soup = BeautifulSoup(page.content, 'html5lib')
            program = False
            for i, par in enumerate(soup.body.find_all('p')):
                LOGGER.debug("Line %d, %d: %s", i, len(par.contents),
                             repr(par))
                if i == 0:
                    LOGGER.debug("skip header")
                    self.body.append(urwid.Divider())
                elif i == 1:
                    if not par.string == "Home":
                        LOGGER.debug("> program")
                        program = True
                    else:
                        LOGGER.debug("> homelink")
                # First paragraph is assumed to be the title
                elif i == 2:
                    self.title = par.text
                    LOGGER.debug("Title: %s", self.title)
                    self.body.append(urwid.Text(('bold', self.title)))
                    self.body.append(urwid.Divider())
                # Second paragraph the author
                elif i == 3:
                    self.author = par.text[3:]
                    LOGGER.debug("Author: %s", self.author)
                    self.body.append(
                        urwid.Text(('bold', "By %s" % self.author)))
                # Third "NPR.org, <date> &middot;"
                elif i == 4:
                    partitioned_text = par.text.partition(" · ")
                    if not program:
                        self.date = partitioned_text[0].lstrip("NPR.org, ")
                        LOGGER.debug("Date: %s", self.date)
                        self.body.append(urwid.Text(('bold', self.date)))
                    self.body.append(urwid.Divider('—'))
                    self.body.append(urwid.Text(partitioned_text[2]))
                # Rest is the article
                else:
                    line = []
                    if not par.contents and par.text != "":
                        continue
                    for child in par.children:
                        LOGGER.debug("Child: %s", repr(child))
                        if not child.name:
                            if child.string:
                                line.append(child.string)
                            else:
                                LOGGER.error("Unknown tag: %s", repr(child))
                        elif child.name in ["b", "strong", "h3"]:
                            if child.string:
                                line.append(('bold', child.string))
                        elif child.name in ["i", "em"]:
                            if child.string:
                                line.append(('italics', child.string))
                        elif child.name in ["a"]:
                            link_num = len(self.links)+1
                            self.links[str(link_num)] = child.href
                            if child.string:
                                line.append(('underline', child.string))
                                line.append(('bold', "[%i]" % link_num))
                        elif child.name in ["hr"]:
                            self.body.append(urwid.Divider('—'))
                    if line:
                        LOGGER.debug("Line: %s", line)
                        self.body.append(urwid.Divider())
                        self.body.append(urwid.Text(line))
                    else:
                        LOGGER.error("Parsing failed on %d, %s", i, repr(par))
                # Last is (c) NPR


urwid.register_signal(Article, 'select')
