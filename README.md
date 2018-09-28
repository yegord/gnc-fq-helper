# A drop-in replacement for GnuCash's Finance::Quote helper

[gnc-fq-helper](http://manpages.ubuntu.com/manpages/xenial/man1/gnc-fq-helper.1.html) is a helper tool used by [GnuCash](http://gnucash.org/) as a wrapper around [Finance::Quote](http://finance-quote.sourceforge.net/) Perl library for getting quotes and exhange rates.

This is a drop-in replacement for the native gnc-fq-helper, written in Python, capable of getting quotes and exhange rates from [Alpha Vantage](https://www.alphavantage.co/).
It just works for me, works around some problems I had when using Finance::Quote-based version (missing currency information for some symbols, missing retries when hitting rate limiting), and is written in a sensible programming language, so it is easy to fix if it breaks.

## Installation
```
git clone https://github.com/yegord/gnc-fq-helper
sudo rm -f /usr/bin/gnc-fq-helper
sudo ln -s $(pwd)/gnc-fq-helper/gnc-fq-helper -t /usr/bin
```

If not done yet, get an [AlphaVantage key](https://www.alphavantage.co/support/#api-key) and set environment variable `ALPHAVANTAGE_API_KEY` to it before running GnuCash.

## Limitations

Alpha Vantage does not say the currency in which a quote is given.
So, the tool effectively guesses this, see `get_quotes_for_symbol` function.
The guessing logic might not cover your cases, so, feel free to fix it and send a pull request.

## Licence

[MIT License](LICENSE)
