#!/usr/bin/env python3

import datetime
import json
import os
import regex
import sys
import time
import traceback
import urllib.parse
import urllib.request


def main():
    query = ''
    while True:
        c = sys.stdin.read(1)
        if not c:
            break
        query += c
        if c == ')':
            sys.stdout.write(handle_query(query))
            sys.stdout.flush()
            query = ''


def handle_query(query):
    log('Query: {}'.format(query))

    match = regex.match(r'^\s*\(\s*([^ ]+)\s+(?:"([^"]+)"\s*)+\)$', query)
    if not match:
        raise RuntimeError('Invalid query: {}'.format(query))

    method = match.group(1)
    symbols = match.captures(2)

    if method == 'alphavantage':
        return get_quotes_for_symbols(symbols)

    if method == 'currency':
        return get_exchange_rate(*symbols)

    raise RuntimeError('Unsupported method: {}'.format(method))


def get_quotes_for_symbols(symbols):
    return '({})'.format(''.join(
        get_quotes_for_symbol(symbol)
        for symbol in symbols
    ))


def get_quotes_for_symbol(symbol):
    response = query_alphavantage(function='GLOBAL_QUOTE', symbol=symbol)
    info = response['Global Quote']
    date = info['07. latest trading day']
    last_price = info['05. price']

    if symbol.endswith('.DE') or \
       symbol.endswith('.AMS') or \
       symbol.endswith('.AS'):
        currency = 'EUR'
    else:
        currency = 'USD'

    return (
        '("{symbol}"'
        ' (symbol . "{symbol}")'
        ' (gnc:time-no-zone . "{date} 12:00:00")'
        ' (last . #e{last_price})'
        ' (currency . "{currency}")'
        ')'
    ).format(**locals())


cached_exchange_rates = None

def get_exchange_rates():
    global cached_exchange_rates

    if cached_exchange_rates is None:
        qs = urllib.parse.urlencode({
            'access_key': os.environ['EXCHANGERATE_API_KEY'],
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        })

        resp = urllib.request.urlopen('http://api.exchangerate.host/historical?' + qs)
        info = json.loads(resp.read().decode())
        info['quotes'][info['source'] + info['source']] = 1.0
        log('Exchange rates: {}'.format(info))
        cached_exchange_rates = info

    return cached_exchange_rates


def get_exchange_rate(to_currency, from_currency):
    info = get_exchange_rates()

    time = info['date'] + '00:00:00'
    last_price = info['quotes'][info['source'] + to_currency] / info['quotes'][info['source'] + from_currency]

    return (
        '(("{from_currency}"'
        '  (symbol . "{from_currency}")'
        '  (gnc:time-no-zone . "{time}")'
        '  (last . #e{last_price})'
        '  (currency . "{to_currency}")'
        '))'
    ).format(**locals())


def query_alphavantage(**kwargs):
    kwargs.update(apikey=os.environ['ALPHAVANTAGE_API_KEY'])
    url = 'https://www.alphavantage.co/query?' + urllib.parse.urlencode(kwargs)

    timeout_sec = 10

    while True:
        log('HTTP request: {}'.format(url))
        resp = urllib.request.urlopen(url)
        result = json.loads(resp.read().decode())
        log('Response: {}'.format(result))
        if 'Note' in result:
            log('Detected rate limiting: {}'.format(result))
            log('Sleeping for {} seconds.'.format(timeout_sec))
            time.sleep(timeout_sec)
            timeout_sec *= 2
        else:
            log('Success!')
            return result


def log(message):
    print(message, file=sys.stderr)


def test_self():
    import subprocess

    proc = subprocess.Popen(
        __file__,
        stdin=subprocess.PIPE,
        close_fds=True
    )
    try:
        proc.stdin.write(b'(alphavantage "VOO""VUSA.AS")')
        proc.stdin.write(b'(currency "USD""EUR")')
        proc.stdin.close()
        proc.wait()
        assert proc.returncode == 0
    finally:
        proc.kill()
        proc.wait()
        proc.stdin.close()


if __name__ == '__main__':
    if '--test' in sys.argv:
        test_self()
    else:
        try:
            main()
        except:
            log(str(sys.exc_info()[0]))
            log(str(sys.exc_info()[1]))
            for line in traceback.format_tb(sys.exc_info()[2]):
                log(line)
            raise
