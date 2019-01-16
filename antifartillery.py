#!/usr/bin/env python

import requests, bs4, random, time, httplib

class Gun:
    _epoch = 0
    _session = None

    def __init__(self, u, p):
        self._epoch = int(1000*time.time())
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
        self._session = session
        self._u = u

    def name(self):
        return self._u

    def load(self, url):
        return self._session.get(url)

    def fire(self, nazipost):
        return self.load("%s&_=%s" % (nazipost, self.epoch()))

    def epoch(self):
        self._epoch += 1
        return self._epoch


class TerminateWithExtremePrejudice:
    _nazilist = []
    _naziposts = {}
    _nazinames = {}
    _guns = []

    def __init__(self, guns, nazis):
        for l in guns:
            u, p = l.strip().split()
            self._guns.append(Gun(u, p))

        self._nazilist = [nazi.strip() for nazi in nazis]

    def naziname(self, nazi):
        return self._nazinames.get(nazi)

    def randomgun(self):
        return random.choice(self._guns)

    def load(self):
        for nazi in self._nazilist:
            n1 = self.randomgun().load(nazi)
            soup = bs4.BeautifulSoup(n1.text, 'lxml')
            self._nazinames[nazi] = soup.title.text.split('--')[-1].split(' @')[0]
            self._naziposts[nazi] = [
                    "https://slo-tech.com" + np.parent.get('href')
                    for np in soup.find_all(string='predlagaj izbris')]

    def fire(self):
        for nazi in self._nazilist:
            for np in self._naziposts[nazi]:
                random.shuffle(self._guns)
                for gun in self._guns[:3]:
                    r = gun.fire(np)
                    print(self.naziname(nazi), gun.name(), r.status_code, r.reason)

if __name__ == '__main__':
    import sys
    afa = TerminateWithExtremePrejudice(
            open(sys.argv[1]), # whitespace separated user/pass per line
            open(sys.argv[2]), # "latest posts by user" url per line
            )
    afa.load()
    afa.fire()

