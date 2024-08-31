from moralis import evm_api
import streamlit as st

def get_wallet_token_balances_price(wallet_address_list):
    api_key = st.secrets['MORALIS_API_KEY']
    output = []
    
    for wallet_address in wallet_address_list:
        if wallet_address is None or wallet_address == '':
            continue
        
        params = {
        "chain": "eth",
        "address": f"{wallet_address}",
        }

        resp = evm_api.wallets.get_wallet_token_balances_price(
        api_key=api_key,
        params=params,
        )

        # print the symbol, balance where verified_contract is True and possible_spam is False
        for token in resp['result']:
            if token['verified_contract'] and not token['possible_spam']:
                # get the symbol and balance - where balance's decimals is used to convert to the actual balance
                print(token['symbol'], int(token['balance']) / 10 ** token['decimals'], token['usd_price'])
                output.append({
                    'wallet_address': wallet_address,
                    'chain': 'ETH',
                    'symbol': token['symbol'],
                    'balance': int(token['balance']) / 10 ** token['decimals'],
                    'usd_price': token['usd_price'],
                    'usd_value': round(int(token['balance']) / 10 ** token['decimals'] * float(token['usd_price']),2) if token['usd_price'] is not None else None
                })
    
    return output