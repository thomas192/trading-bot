import ccxt
from pprint import pprint


def get_order_status(exchange, symbol, order_id):
    # Query
    status = exchange.fetch_order_status(order_id, symbol)
    # Return
    return status


def create_limit_quote_order(exchange, symbol, side, limit_price, quote_order_quantity):
    # Query
    order = exchange.create_order(symbol, "limit", side, amount=None, price=limit_price,
                                      params={"quoteOrderQty": quote_order_quantity})
    # Return
    return order["id"]


def create_market_quote_order(exchange, symbol, side, quote_order_quantity):
    # Query
    order = exchange.create_order(symbol, "market", side, amount=quote_order_quantity, price=None,
                                      params={"quoteOrderQty": quote_order_quantity})
    # Return
    return order["id"]


print('CCXT Version:', ccxt.__version__)

exchange = ccxt.binance({
    'apiKey': 'C0DsfrNhLDEVvWOvXXAKOD2GKioruMZoWn1zaVQ3YSJQ4bobdsYsERkdmxuKbpV2',
    'secret': 'boOhj5889EjRS5Ctk99o1ERa37K9fioNGRqPum94QYbLSeabTHjkE98d3GUOOFX9',
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True)
markets = exchange.load_markets()
exchange.verbose = True  # comment/uncomment for debugging purposes

symbol = 'BTC/USDT'
amount = 123.45  # in quote currency, how much USDT you want to spend for buying BTC

order_id = create_limit_quote_order(exchange, symbol, "buy", 10597, amount)

pprint(order_id)

status = get_order_status(exchange, symbol, order_id)

pprint(status)
