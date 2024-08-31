# https://pypi.org/project/coinbase-advanced-py/

from coinbase.rest import RESTClient
import streamlit as st
def get_coinbase_balance():
    api_key = st.secrets['COINBASE_API_KEY']
    api_secret = st.secrets['COINBASE_API_SECRET']
    client = RESTClient(api_key=api_key, api_secret=api_secret)

    result = []
    accounts = client.get_accounts()['accounts']
    for account in accounts:
        available_balance_value = account['available_balance']['value']
        available_balance_currency = account['available_balance']['currency']
        if float(available_balance_value) > 0:
            if available_balance_currency != 'USDC':
                price = client.get_product(available_balance_currency.replace('2', '') + '-USD')['price']
                result.append({"symbol": available_balance_currency, "balance": available_balance_value, "price_usd": price, "usd_value": float(available_balance_value) * float(price)})
    
    return result