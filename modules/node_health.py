import aiohttp
from loguru import logger
from config import VALIDATOR_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from prometheus.metrics import solana_node_health, solana_node_slots_behind


async def get_health():
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "getHealth"
    }

    try:
        # Create async session and send request to Validator RPC endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post(VALIDATOR_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                response.raise_for_status()  # Raise error for HTTP issues
                result = await response.json()

        if "result" in result and result["result"] == "ok":
            update_metric(solana_node_health, 1, labels={"status": "healthy", "cause": "none"})
            logger.info("Node is healthy")
        elif "error" in result:
            error_message = result["error"].get("message", "Unknown error")
            slots_behind = result["error"]["data"]["numSlotsBehind"]
            solana_node_health.labels(status="unhealthy", cause="slots_behind").set(0)
            update_metric(solana_node_health, 1, labels={"status": "unhealthy", "cause": "slots_behind"})
            update_metric(solana_node_health, 0, labels={"status": "healthy", "cause": "none"})
            update_metric(solana_node_slots_behind, slots_behind)
            logger.error(f"Node is unhealthy: {error_message}.")

        else:
            logger.error("Unexpected response format")
            update_metric(solana_node_health, 0, labels={"status": "healthy", "cause": "none"})

    except aiohttp.ClientError as e:
        logger.error(f"Network error occurred while fetching node information: {e}")
        update_metric(solana_node_health, 0, labels={"status": "healthy", "cause": "none"})
    except ValueError as e:
        logger.error(f"Data format error: {e}")
        update_metric(solana_node_health, 0, labels={"status": "healthy", "cause": "none"})
    except Exception as e:
        logger.error(f"Error getting node status: {e}")
        update_metric(solana_node_health, 0, labels={"status": "healthy", "cause": "none"})
