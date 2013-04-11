###
# Copyright (c) 2013, Jure Koren
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot import ircmsgs
from supybot import log
log = log.getPluginLogger("Ticker")

from decimal import Decimal

import time, threading, json, urllib2

CURRENCYCOLORMAP = dict(
        BTC='green',
        LTC='orange',
        NMC='orange',
        NVC='orange',
        PPC='orange',
    )


def currencycolor(cur):
    if cur in CURRENCYCOLORMAP:
        return ircutils.mircColor(cur, CURRENCYCOLORMAP[cur])
    else:
        return cur

def updown(x, s=None):
    if x < 0:
        if not s: s = 'down'
        return ircutils.mircColor(s, 'red')
    elif x > 0:
        if not s: s = ' up '
        return ircutils.mircColor(s, 'green')
    else:
        if not s: s = 'same'
        return s

def getvalue(data, keys):
    try:
        for k in keys:
            data = data.get(k)
    except Exception, e:
        log.exception("data=%r keys=%r", data, keys)
    if type(data) == type(0.0):
        data = '%.8f' % data
    return data

def d(x):
    return Decimal(x)

def q(x):
    if x > 0:
        return d('0.%s1' % ((x-1)*'0'))
    return d('1')

TICKERS = dict(
    mtgox = dict(delay=10,
                urls=dict(ticker='https://data.mtgox.com/api/2/BTCUSD/money/ticker',),
                label=ircutils.mircColor('MtGox', 'yellow'),
                outputs=dict(
                    mtgoxusd = dict(source='mtgox',
                                metrics = dict(
                                    last = (q(3), 'ticker', 'data', 'last', 'value',),
                                    #buy = (q(3), 'ticker', 'data', 'buy', 'value',),
                                    #sell = (q(3), 'ticker', 'data', 'sell', 'value',),
                                    #volume = (q(0), 'ticker', 'data', 'vol', 'value',),
                                ),
                                unit = 'BTC',
                                currency = 'USD',
                                reportchange = dict(
                                    last = q(2),
                                ),
                            ),
                    ),
            ),
    bitstamp = dict(delay=10,
                urls=dict(ticker='https://www.bitstamp.net/api/ticker/',),
                label=ircutils.mircColor('Stamp', 'green'),
                outputs=dict(
                    bitstampusd = dict(source='bitstamp',
                                metrics = dict(
                                    last = (q(3), 'ticker', 'last',),
                                    #buy = (q(2), 'ticker', 'bid',),
                                    #sell = (q(2), 'ticker', 'ask',),
                                    #volume = (q(0), 'ticker', 'volume',),
                                ),
                                unit = 'BTC',
                                currency = 'USD',
                                reportchange = dict(
                                    last = q(2),
                                ),
                            ),
                    ),
            ),
    btce = dict(delay=60,
                urls=dict(
                    ltc='https://btc-e.com/api/2/ltc_btc/ticker',
                    nmc='https://btc-e.com/api/2/nmc_btc/ticker',
                    nvc='https://btc-e.com/api/2/nvc_btc/ticker',
                    ppc='https://btc-e.com/api/2/ppc_btc/ticker',
                    trc='https://btc-e.com/api/2/trc_btc/ticker',
                    usd='https://btc-e.com/api/2/btc_usd/ticker',
                    ),
                label='BTC-e',
                outputs=dict(
                    btceltc = dict(source='btce',
                                metrics = dict(
                                    last = (q(6), 'ltc', 'ticker', 'last',),
                                    #buy = (q(6), 'ltc', 'ticker', 'sell',),
                                    #sell = (q(6), 'ltc', 'ticker', 'buy',),
                                    #volume = (q(0), 'ltc', 'ticker', 'vol_cur',),
                                ),
                                unit = 'LTC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    btcenmc = dict(source='btce',
                                metrics = dict(
                                    last = (q(6), 'nmc', 'ticker', 'last',),
                                    #buy = (q(6), 'nmc', 'ticker', 'sell',),
                                    #sell = (q(6), 'nmc', 'ticker', 'buy',),
                                    #volume = (q(0), 'nmc', 'ticker', 'vol_cur',),
                                ),
                                unit = 'NMC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    btcenvc = dict(source='btce',
                                metrics = dict(
                                    last = (q(6), 'nvc', 'ticker', 'last',),
                                    #buy = (q(6), 'nvc', 'ticker', 'sell',),
                                    #sell = (q(6), 'nvc', 'ticker', 'buy',),
                                    #volume = (q(0), 'nvc', 'ticker', 'vol_cur',),
                                ),
                                unit = 'NVC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    btceppc = dict(source='btce',
                                metrics = dict(
                                    last = (q(6), 'ppc', 'ticker', 'last',),
                                    #buy = (q(6), 'ppc', 'ticker', 'sell',),
                                    #sell = (q(6), 'ppc', 'ticker', 'buy',),
                                    #volume = (q(0), 'ppc', 'ticker', 'vol_cur',),
                                ),
                                unit = 'PPC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    btcetrc = dict(source='btce',
                                metrics = dict(
                                    last = (q(6), 'trc', 'ticker', 'last',),
                                    #buy = (q(6), 'trc', 'ticker', 'sell',),
                                    #sell = (q(6), 'trc', 'ticker', 'buy',),
                                    #volume = (q(0), 'trc', 'ticker', 'vol_cur',),
                                ),
                                unit = 'TRC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    ),
            ),
    vircurex = dict(delay=60,
                urls=dict(ticker='https://vircurex.com/api/get_info_for_currency.json',),
                label='VCrEx',
                outputs=dict(
                    vircurexppc = dict(source='vircurex',
                                metrics = dict(
                                    last = (q(6), 'ticker', 'PPC', 'BTC', 'last_trade',),
                                    #buy = (q(6), 'ticker', 'PPC', 'BTC', 'highest_bid',),
                                    #sell = (q(6), 'ticker', 'PPC', 'BTC', 'lowest_ask',),
                                    #volume = (q(0), 'ticker', 'PPC', 'BTC', 'volume',),
                                ),
                                unit = 'PPC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    vircurextrc = dict(source='vircurex',
                                metrics = dict(
                                    last = (q(6), 'ticker', 'TRC', 'BTC', 'last_trade',),
                                    #buy = (q(6), 'ticker', 'TRC', 'BTC', 'highest_bid',),
                                    #sell = (q(6), 'ticker', 'TRC', 'BTC', 'lowest_ask',),
                                    #volume = (q(0), 'ticker', 'TRC', 'BTC', 'volume',),
                                ),
                                unit = 'TRC',
                                currency = 'BTC',
                                reportchange = dict(
                                    last = q(3),
                                ),
                            ),
                    ),
            ),
)

class Ticker(callbacks.Plugin):
    """Add the help for "@plugin help Ticker" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Ticker, self)
        self.__parent.__init__(irc)
        self.stop = True
        self._threads = []
        self.startticker(irc, None, None)

    def _ticker(self, irc, ticker):
        prev = dict()
        while True:
            if self.stop:
                return
            try:
                log.debug("refreshing ticker %r", ticker)
                data = dict()
                for key, url in TICKERS[ticker]['urls'].iteritems():
                    log.debug("fetching url %r", url)
                    try:
                        t0 = time.time()
                        data[key] = json.load(urllib2.urlopen(url, timeout=30))
                    except Exception, e:
                        log.exception("error fetching %r", url)
                        continue
                    log.info("fetched %r in %.2f s", url, time.time() - t0)
                    log.debug("data = %r", data[key])
                if not data:
                    raise Exception("no data for ticker %s" % repr(ticker))
                for output, o in TICKERS[ticker]['outputs'].iteritems():
                    log.debug("processing output %r: %r", output, o)
                    values = []
                    diffstring = ''
                    report = False
                    for metric, m in o['metrics'].iteritems():
                        value = d(getvalue(data, m[1:])).quantize(m[0])
                        if metric == 'volume': # volume is in base units
                            currency = o['unit']
                        else: # others are in currency
                            currency = o['currency']
                        log.debug("output %r metric %r has value %r", output, metric, value)
                        if metric in o['reportchange']:
                            if output+metric in prev:
                                vdiff = value - prev[output+metric]
                            else:
                                vdiff = Decimal(0)
                                prev[output+metric] = value
                                report = True
                            if vdiff.copy_abs() >= o['reportchange'][metric]:
                                log.debug("output %r metric %r value diff %r exceeds %r, reporting change",
                                    output, metric, vdiff.copy_abs(), o['reportchange'][metric])
                                prev[output+metric] = value
                                report = True
                            values.append("%12s %-3s" % (
                                    value, currency))
                            diffstring = updown(vdiff)
                        else:
                            values.append("%12s %-3s" % (
                                value, currency))
                    diffstring=updown(vdiff, '(%s%s %s)' % (
                        '-' if vdiff.is_signed() else '+',
                        vdiff.copy_abs(), currency))
                    out = "%s %s %s %s" % (
                        '['+TICKERS[ticker]['label']+']',
                        currencycolor(o['unit']),
                        " ".join(values),
                        diffstring)
                    if report:
                        for chan in self.registryValue('channels'):
                            irc.queueMsg(ircmsgs.privmsg(chan,
                                ircutils.bold(out)))
            except Exception, e:
                log.exception("in ticker thread %r", ticker)
            time.sleep(TICKERS[ticker]['delay'])

    def startticker(self, irc, msg, args):
        if not self.stop and self._threads:
            irc.reply("Already monitoring? %r threads running." % len(self._threads))
            return
        if msg:
            irc.reply("Starting monitoring.")
        self.stop = False
        for ticker in TICKERS:
            log.debug("starting %r", ticker)
            t = threading.Thread(target=self._ticker, args=(irc, ticker,))
            t.start()
    startticker = wrap(startticker)

    def stopticker(self, irc, msg, args):
        self.stop = True
        while self._threads:
            t = self._threads.pop()
            log.debug("waiting for %r to finish", t.name)
            t.join()
            log.debug("%r exited", t.name)
        irc.reply("Stopped monitoring.")
    stopticker = wrap(stopticker)

Class = Ticker


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
