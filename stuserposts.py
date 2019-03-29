#!/usr/bin/env python
# use: stuserposts.py username password https://slo-tech.com/forum/c1 > file.html

import requests, bs4, random, time, httplib, logging, sys, re

class STGrab:
    def __init__(self, url, u, p):
        self.url = url
        self.urlqueue = [url]
        self.rooturl = re.search(r'(https://[^/]+)', url).groups()[0]
        self.login(u, p)

    def login(self, u, p):
        session = requests.session()
        url = 'https://slo-tech.com'
        p1 = session.get(url, allow_redirects=True)
        p2 = session.post(url + '/script/login.php', dict(
            ssl="on",
            kaj="1",
            polozajUporabnika="https%3A%2F%2Fslo-tech.com%2F",
            uime=u,
            ugeslo=p,
            submit="Prijavi me",
            )
        )
        self.r = session

    def get(self, url):
        return bs4.BeautifulSoup(
                self.r.get(url).text, 'html.parser')

    def next_link(self, html):
        return html.find_all("a", class_="selected")[0].find_next('a').get("href")

    def posts(self, html):
        return html.find_all("div", class_="post")

    def getAllPosts(self):
        while self.urlqueue:
            nexturl = self.urlqueue.pop()
            html = self.get(nexturl)
            link = self.next_link(html)
            for post in self.posts(html):
                text = unicode(post).encode('utf-8')
                yield text.replace('href="/', 'href="'+self.rooturl+'/')
            if (self.rooturl + link).startswith(self.url):
                self.urlqueue.append(self.rooturl + link)


if __name__ == '__main__':
    user = sys.argv[1]
    password = sys.argv[2]
    rooturl = sys.argv[3]
    print('''<html>
        <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        </head>
        <body>''')
    for post in STGrab(rooturl, user, password).getAllPosts():
        print(post)
    print('</body></html>')

