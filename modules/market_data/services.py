from decimal import Decimal

import requests
from django.utils import timezone

YAHOO_CHART_URL = 'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0'}
REQUEST_TIMEOUT = 10


def fetch_quote(symbol):
    """Fetch the latest price + previous close for a Yahoo Finance symbol.

    Returns a dict with 'price' and 'previous_close' (as Decimal), or raises
    ValueError/requests.RequestException on failure — callers decide how to log it.
    """
    url = YAHOO_CHART_URL.format(symbol=symbol)
    response = requests.get(url, headers=REQUEST_HEADERS, params={'range': '5d', 'interval': '1d'}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    error = payload.get('chart', {}).get('error')
    if error:
        raise ValueError(error.get('description', 'Unknown Yahoo Finance error'))

    results = payload.get('chart', {}).get('result')
    if not results:
        raise ValueError('No data returned for symbol')

    meta = results[0].get('meta', {})
    price = meta.get('regularMarketPrice')
    previous_close = meta.get('chartPreviousClose') or meta.get('previousClose')
    if price is None or previous_close is None:
        raise ValueError('Missing price data in Yahoo Finance response')

    return {'price': Decimal(str(price)), 'previous_close': Decimal(str(previous_close))}


def refresh_instrument(instrument):
    """Fetch and persist the latest quote for a single MarketInstrument. Returns (ok, message)."""
    try:
        quote = fetch_quote(instrument.symbol)
    except (requests.RequestException, ValueError) as exc:
        instrument.last_error = str(exc)[:255]
        instrument.save(update_fields=['last_error'])
        return False, str(exc)

    price = quote['price']
    previous_close = quote['previous_close']
    change = price - previous_close
    change_percent = (change / previous_close * 100) if previous_close else Decimal('0')

    instrument.last_price = price
    instrument.last_change = change
    instrument.last_change_percent = change_percent
    instrument.last_updated = timezone.now()
    instrument.last_error = ''
    instrument.save(update_fields=['last_price', 'last_change', 'last_change_percent', 'last_updated', 'last_error'])
    return True, 'ok'


def refresh_all_instruments(queryset):
    """Refresh every instrument in the queryset. Returns a list of (instrument, ok, message)."""
    results = []
    for instrument in queryset:
        ok, message = refresh_instrument(instrument)
        results.append((instrument, ok, message))
    return results
