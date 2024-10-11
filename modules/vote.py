import inspect
import time
import aiohttp
import asyncio
from loguru import logger
from utils.func import update_metric
from config import VALIDATOR_RPC_ENDPOINT, NETWORK_RPC_ENDPOINT, VOTE_PUB_KEY, HEADERS, RETRY
from prometheus.metrics import solana_validator_vote_height, solana_network_vote_height, solana_vote_height_diff

rpc_urls = {
    "network": NETWORK_RPC_ENDPOINT,
    "validator": VALIDATOR_RPC_ENDPOINT
}


def get_vote_accounts(result):
    return result.get('result', {}).get('current', []) or result.get('result', {}).get('delinquent', [])


async def measure_rpc_response_time(url, session, payload):
    try:
        start_time = time.time()
        async with session.post(url, json=payload, headers=HEADERS) as response:
            result = await response.json()
        end_time = time.time()
        return result, end_time - start_time
    except Exception as e:
        logger.error(f"Error while accessing {url}: {e}")
        return None, None


async def make_requests(payload, func_name):
    async with aiohttp.ClientSession() as session:
        raw_results = await asyncio.gather(
            *[measure_rpc_response_time(url, session, payload) for url in rpc_urls.values()],
            return_exceptions=True
        )

        results = []
        response_times = {}

        for (row, response_time), name in zip(raw_results, rpc_urls.keys()):
            if row is not None:
                results.append(row)
            response_times[name] = response_time
        network_time = response_times.get('network')
        validator_time = response_times.get('validator')

        if network_time is not None:
            logger.debug(f"{func_name.upper()} Response time for network: {network_time:.4f} seconds")
        else:
            logger.warning(f"{func_name.upper()} No valid response time for network")

        if validator_time is not None:
            logger.debug(f"{func_name.upper()} Response time for validator: {validator_time:.4f} seconds")
        else:
            logger.warning(f"{func_name.upper()} No valid response time for validator")

    return results, response_times


async def get_votes():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getVoteAccounts",
        "params": [
            {
                "votePubkey": VOTE_PUB_KEY
            }
        ]
    }
    func_name = inspect.currentframe().f_code.co_name
    blocks, response_times = await make_requests(payload, func_name)

    retry_count = 0
    last_blocks = None
    while retry_count < RETRY and any(t is not None and t > 1 for t in response_times.values()):
        retry_count += 1
        logger.info("One or more requests took longer than 1 second. Retrying...")
        blocks, response_times = await make_requests(payload, func_name)

        last_blocks = blocks

    if retry_count == RETRY:
        blocks = last_blocks

    try:
        results = blocks
        validator_vote_height = network_vote_height = None
        if all("error" not in res for res in results):
            vote_accounts_network = get_vote_accounts(results[0]) if len(results) > 0 else None
            if vote_accounts_network:
                network_vote_height = vote_accounts_network[0]['lastVote']
                update_metric(solana_network_vote_height, network_vote_height, labels={"rpc": "network"})
                logger.debug(f"Network vote height: {network_vote_height}")
            else:
                logger.warning(f"{func_name.upper()} No vote data for validator")

            vote_accounts_validator = get_vote_accounts(results[1]) if len(results) > 1 else None
            if vote_accounts_validator:
                validator_vote_height = vote_accounts_validator[0]['lastVote']
                update_metric(solana_validator_vote_height, validator_vote_height, labels={"rpc": "validator"})
                logger.debug(f"Validator vote height: {validator_vote_height}")
            else:
                logger.warning(f"{func_name.upper()} No vote data for network")

            if vote_accounts_network and vote_accounts_validator:
                update_metric(solana_vote_height_diff, validator_vote_height - network_vote_height)
                logger.debug(f"Diff vote height: {validator_vote_height - network_vote_height}")
        else:
            logger.error(f"Error processing vote data: {results}")
    except Exception as e:
        logger.error(f"Error processing vote data: {e}")
