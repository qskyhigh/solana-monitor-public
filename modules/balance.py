import inspect
import time
import aiohttp
from loguru import logger
from utils.func import update_metric
from prometheus.metrics import solana_account_balance, solana_vote_account_balance
from config import PUB_KEY, VOTE_PUB_KEY, NETWORK_RPC_ENDPOINT, HEADERS


# Unified async function to fetch both balances
async def fetch_balances():
    # Payload for fetching both identity and vote account balances
    payload = [
        {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [PUB_KEY]},
        {"jsonrpc": "2.0", "id": 2, "method": "getBalance", "params": [VOTE_PUB_KEY]}
    ]

    try:
        # Send the requests asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.post(NETWORK_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                response.raise_for_status()
                results = await response.json()

        try:
            # Parsing the results for both accounts
            identity_balance = results[0]['result'].get('value') / 10 ** 9 if 'result' in results[0] else None
            vote_acc_balance = results[1]['result'].get('value') / 10 ** 9 if 'result' in results[1] else None

            logger.debug(f"Identity balance: {identity_balance} SOL, Vote account balance: {vote_acc_balance} SOL")

            return identity_balance, vote_acc_balance
        except Exception as e:
            logger.error(f"Error processing balance data: {e}")
            return None, None

    except aiohttp.ClientError as e:
        logger.error(f"Error making request to Solana RPC: {e}")
        return None, None


# Main async function to gather and update modules
async def balance_metrics():
    logger.info(f"{inspect.currentframe().f_code.co_name}: Starting metrics collection process.")
    start_time = time.time()

    # Fetch both balances asynchronously
    identity_balance, vote_acc_balance = await fetch_balances()

    # Function to update Prometheus modules if values are valid
    update_metric(solana_account_balance, identity_balance)
    update_metric(solana_vote_account_balance, vote_acc_balance)

    end_time = time.time()
    logger.success(f"{inspect.currentframe().f_code.co_name}: Metrics successfully collected and exported to "
                   f"Prometheus. Time: {end_time - start_time}")
