#!/usr/bin/env python3

import os
import regex
import requests
import sys
import time
import urllib.parse


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
        ' (last . {last_price})'
        ' (currency . "{currency}")'
        ')'
    ).format(**locals())


def get_exchange_rate(to_currency, from_currency):
    response = query_alphavantage(
        function='CURRENCY_EXCHANGE_RATE',
        from_currency=from_currency,
        to_currency=to_currency
    )
    info = response['Realtime Currency Exchange Rate']
    last_price = info['5. Exchange Rate']
    time = info['6. Last Refreshed']

    return (
        '(("{from_currency}"'
        '  (symbol . "{from_currency}")'
        '  (gnc:time-no-zone . "{time}")'
        '  (last . {last_price})'
        '  (currency . "{to_currency}")'
        '))'
    ).format(**locals())


def query_alphavantage(**kwargs):
    kwargs.update(apikey=os.environ['ALPHAVANTAGE_API_KEY'])
    url = 'https://www.alphavantage.co/query?' + urllib.parse.urlencode(kwargs)

    timeout_sec = 10

    while True:
        log('HTTP request: {}'.format(url))
        result = requests.get(url).json()
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
            raise
