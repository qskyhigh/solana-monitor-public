import inspect
import time
import aiohttp
import asyncio
from loguru import logger
from config import VALIDATOR_RPC_ENDPOINT, NETWORK_RPC_ENDPOINT, HEADERS, RETRY
from utils.func import update_metric
from prometheus.metrics import (solana_block_height, solana_network_block_height, solana_current_slot,
                                solana_net_current_slot, solana_net_max_shred_insert_slot,
                                solana_net_max_retransmit_slot, solana_slot_diff, solana_block_height_diff,
                                solana_val_max_shred_insert_slot, solana_val_max_retransmit_slot)

rpc_urls = {
    "network": NETWORK_RPC_ENDPOINT,
    "validator": VALIDATOR_RPC_ENDPOINT
}


def extract_slot(data, req_id):
    return next((item['result'] for item in data if item['id'] == req_id and 'error' not in item), None)


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


async def get_slots():
    payload = [
        {"jsonrpc": "2.0", "id": 1, "method": "getMaxRetransmitSlot"},
        {"jsonrpc": "2.0", "id": 2, "method": "getMaxShredInsertSlot"},
        {"jsonrpc": "2.0", "id": 3, "method": "getSlot", "params": [{"commitment": "confirmed"}]}
    ]
    func_name = inspect.currentframe().f_code.co_name
    slots, response_times = await make_requests(payload, func_name)

    retry_count = 0
    last_slots = None
    while retry_count < RETRY and any(t is not None and t > 1 for t in response_times.values()):
        retry_count += 1
        logger.info("One or more requests took longer than 1 second. Retrying...")
        slots, response_times = await make_requests(payload, func_name)

        last_slots = slots

    if retry_count == RETRY:
        slots = last_slots

    try:
        val_slot = net_slot = None
        if slots[0] is not None:
            net_slot = extract_slot(slots[0], 3)
            update_metric(solana_current_slot, net_slot)
            net_max_shred_insert_slot = extract_slot(slots[0], 2)
            update_metric(solana_net_max_shred_insert_slot, net_max_shred_insert_slot)
            net_max_retransmit_slot = extract_slot(slots[0], 1)
            update_metric(solana_net_max_retransmit_slot, net_max_retransmit_slot)
            logger.debug(f"Network slot: {net_slot}, "
                         f"net_max_shred_insert_slot: {net_max_shred_insert_slot}, net_max_retransmit_slot: {net_max_retransmit_slot}")
        else:
            logger.warning(f"{func_name.upper()} No slot data for network")

        if slots[1] is not None:
            val_slot = extract_slot(slots[1], 3)
            update_metric(solana_net_current_slot, val_slot)
            val_max_shred_insert_slot = extract_slot(slots[1], 2)
            update_metric(solana_val_max_shred_insert_slot, val_max_shred_insert_slot)
            val_max_retransmit_slot = extract_slot(slots[1], 1)
            update_metric(solana_val_max_retransmit_slot, val_max_retransmit_slot)
            logger.debug(f"Validator slot: {val_slot}, "
                         f"val_max_shred_insert_slot: {val_max_shred_insert_slot}, val_max_retransmit_slot: {val_max_retransmit_slot}")
        else:
            logger.warning(f"{func_name.upper()} No slot data for validator")

        if val_slot is not None and net_slot is not None:
            update_metric(solana_slot_diff, val_slot - net_slot)
            logger.debug(f"Slot diff: {val_slot - net_slot}")

    except Exception as e:
        logger.error(f"Error processing slots data: {e}")


async def get_block_height():
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "getBlockHeight"
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
        val_block_height = net_block_height = None
        if blocks[0] is not None:
            net_block_height = blocks[0]['result']
            update_metric(solana_network_block_height, net_block_height)
        else:
            logger.warning(f"{func_name.upper()} No block height data for network")

        if blocks[1] is not None:
            val_block_height = blocks[1]['result']
            update_metric(solana_block_height, val_block_height)
        else:
            logger.warning(f"{func_name.upper()} No block height data for validator")

        if val_block_height and net_block_height:
            update_metric(solana_block_height_diff, val_block_height-net_block_height)
            logger.debug(f"Block diff: {val_block_height - net_block_height}")

        logger.debug(f"Network block height: {net_block_height}, Validator block height: {val_block_height}")

    except Exception as e:
        logger.error(f"Error processing blocks data: {e}")
