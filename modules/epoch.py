import aiohttp
from loguru import logger
from config import NETWORK_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from prometheus.metrics import (solana_network_epoch, solana_tx_count, solana_slot_in_epoch, solana_slot_index)


async def get_epoch_information():
    """Fetches epoch information from Solana network and updates Prometheus metrics asynchronously."""
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "getEpochInfo"
    }

    try:
        # Create async session and send request to Solana RPC endpoint
        # logger.info("Sending async request to fetch epoch information from Solana network.")
        async with aiohttp.ClientSession() as session:
            async with session.post(NETWORK_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                response.raise_for_status()  # Raise error for HTTP issues
                result = await response.json()

        # Validate required keys in the result
        if 'result' not in result:
            raise ValueError("Invalid response format: 'result' field is missing")

        # Extract metrics from result
        epoch = result['result'].get('epoch')
        update_metric(solana_network_epoch, epoch)
        slot_in_epoch = result['result'].get('slotsInEpoch')
        update_metric(solana_slot_in_epoch, slot_in_epoch)
        slot_index = result['result'].get('slotIndex')
        update_metric(solana_slot_index, slot_index)
        tx_count = result['result'].get('transactionCount')
        update_metric(solana_tx_count, tx_count)

        # logger.info("Successfully retrieved epoch information.")
        logger.debug(f"Epoch: {epoch}, Slot in Epoch: {slot_in_epoch}, Slot Index: {slot_index}, Transaction Count: {tx_count}")

    except aiohttp.ClientError as e:
        # Log network or connection errors
        logger.error(f"Network error occurred while fetching epoch information: {e}")
    except ValueError as e:
        # Log invalid response format issues
        logger.error(f"Data format error: {e}")
    except Exception as e:
        # Log any other unexpected errors
        logger.error(f"Unexpected error while getting epoch information: {e}")
