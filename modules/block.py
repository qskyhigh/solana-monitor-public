import subprocess
import time
import inspect
import json
from loguru import logger
from config import PUB_KEY, SOLANA_BINARY_PATH
from utils.func import update_metric
from prometheus.metrics import (solana_net_skip_rate, solana_skipped_total, solana_val_blocks_produced,
                                solana_val_skip_rate, solana_val_skipped_slots, solana_total_blocks_produced,
                                solana_skip_rate_diff, solana_val_leader_slots, solana_total_slots,
                                solana_confirmed_epoch_first_slot, solana_confirmed_epoch_last_slot)


# Function to fetch block production data from Solana CLI
def get_block_production():
    # Run solana block-production command and capture output
    try:
        result = subprocess.run(
            [SOLANA_BINARY_PATH, "block-production", "--output", "json-compact"],
            capture_output=True, text=True, check=True
        )
        # logger.info("Block production command executed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing solana block-production command: {e}")
        return None

    # Remove any "Note:" lines that might be in the output
    block_production = "\n".join([line for line in result.stdout.splitlines() if "Note:" not in line])

    try:
        block_production_data = json.loads(block_production)
        # logger.info("Block production data successfully parsed.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from block production data: {e}")
        return None

    # Return parsed data
    return block_production_data


# Function to extract validator's modules and send them to Prometheus
def process_metrics(block_production_data):

    if not block_production_data:
        logger.warning("No block production data available to process.")
        return

    # Retrieve network modules
    try:
        total_slots_skipped = block_production_data.get('total_slots_skipped')
        update_metric(solana_skipped_total, total_slots_skipped)
        total_slots = block_production_data.get('total_slots')
        update_metric(solana_total_slots, total_slots)
        total_blocks_produced = block_production_data.get('total_blocks_produced')
        update_metric(solana_total_blocks_produced, total_blocks_produced)
        start_slot = block_production_data.get('start_slot')
        update_metric(solana_confirmed_epoch_first_slot, start_slot)
        end_slot = block_production_data.get('end_slot')
        update_metric(solana_confirmed_epoch_last_slot, end_slot)
        total_net_skip_rate = (total_slots_skipped / total_slots) * 100
        update_metric(solana_net_skip_rate, total_net_skip_rate)
        logger.debug(f"Network metrics - Total slots skipped: {total_slots_skipped}, Total slots: {total_slots}, "
                     f"Total blocks produced: {total_blocks_produced}, Start slot: {start_slot}, "
                     f"End slot: {end_slot}, Net skip rate: {total_net_skip_rate}")
    except KeyError as e:
        logger.error(f"Key error when extracting network metrics: {e}")
        return

    validator_block_production = [
        leader for leader in block_production_data.get("leaders", [])
        if leader.get("identityPubkey") == PUB_KEY
    ]

    # Retrieve validator-specific modules
    if validator_block_production:
        try:
            val_slots_skipped = validator_block_production[0].get('skippedSlots')
            update_metric(solana_val_skipped_slots, val_slots_skipped)
            val_leader_slots = validator_block_production[0].get('leaderSlots')
            # update_metric(solana_val_leader_slots, val_leader_slots)
            val_blocks_produced = validator_block_production[0].get('blocksProduced')
            update_metric(solana_val_blocks_produced, val_blocks_produced)
            val_skip_rate = (val_slots_skipped / val_leader_slots) * 100
            update_metric(solana_val_skip_rate, val_skip_rate)
            skip_rate_diff = val_skip_rate - total_net_skip_rate
            update_metric(solana_skip_rate_diff, skip_rate_diff)
            logger.debug(
                f"Validator metrics - blocks produced: {val_blocks_produced}, "
                f"skip rate: {val_skip_rate:.2f}%, slots skipped: {val_slots_skipped}, "
                f"leader_slots: {val_leader_slots}, skip rate diff: {skip_rate_diff}")
        except KeyError as e:
            logger.error(f"Key error when extracting validator-specific metrics: {e}")
            return
    else:
        logger.warning("No validator block production data found.")
        update_metric(solana_val_skipped_slots, 0)
        update_metric(solana_val_blocks_produced, 0)
        update_metric(solana_val_skip_rate, 0)
        update_metric(solana_skip_rate_diff, -total_net_skip_rate)


# Main function to collect block production data and process it
def block_metrics():
    logger.info(f"{inspect.currentframe().f_code.co_name}: Starting metrics collection process.")
    start_time = time.time()

    # Fetch block production data
    block_production_data = get_block_production()

    # Process and send modules to Prometheus
    process_metrics(block_production_data)

    end_time = time.time()
    logger.success(f"{inspect.currentframe().f_code.co_name}: All metrics have been successfully collected and sent "
                   f"to Prometheus. Time: {end_time - start_time}")
