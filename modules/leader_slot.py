import inspect
import aiohttp
import asyncio
import time
from datetime import datetime, timedelta
from loguru import logger
from utils.func import update_metric
from config import NETWORK_RPC_ENDPOINT, PUB_KEY, HEADERS
from prometheus.metrics import (solana_val_total_leader_slots, solana_next_leader_slot, solana_time_to_next_slot,
                                solana_avg_slot_duration, solana_next_slot_time, solana_previous_leader_slot)


# Generalized async function to fetch data from the Solana RPC
async def fetch_rpc_data(session, method, params=None):
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or []
    }

    try:
        async with session.post(NETWORK_RPC_ENDPOINT, headers=HEADERS, json=payload) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        logger.error(f"Error fetching {method} from RPC: {e}")
        return None


# Get current slot
async def get_current_slot(session):
    result = await fetch_rpc_data(session, "getSlot", [{"commitment": "confirmed"}])
    return result.get('result') if result else None


# Get leader schedule
async def get_leader_schedule(session):
    result = await fetch_rpc_data(session, "getLeaderSchedule", [None, {"identity": PUB_KEY}])
    return result.get('result', {}).get(PUB_KEY, []) if result else None


# Get epoch information
async def get_epoch(session):
    epoch_schedule = await fetch_rpc_data(session, "getEpochSchedule")
    epoch_info = await fetch_rpc_data(session, "getEpochInfo")

    if epoch_schedule and epoch_info:
        return (epoch_schedule['result'].get('firstNormalEpoch'),
                epoch_schedule['result'].get('firstNormalSlot'),
                epoch_schedule['result'].get('slotsPerEpoch'),
                epoch_info['result'].get('epoch'))
    else:
        logger.error("Error fetching epoch data")
        return None, None, None, None


# Calculate average slot duration
async def calculate_slot_duration(session):
    result = await fetch_rpc_data(session, "getRecentPerformanceSamples", [1])
    if result and len(result['result']) > 0:
        sample = result['result'][0]
        sample_period_secs = sample.get('samplePeriodSecs')
        num_slots = sample.get('numSlots')
        if num_slots != 0:
            return sample_period_secs / num_slots
        else:
            logger.warning("Warning: Division by zero, setting result to 0")
            return 0
    else:
        logger.error("Error fetching slot duration data")
        return None


# Main function to gather and set Prometheus modules
async def leader_slot_metrics():
    logger.info(f"{inspect.currentframe().f_code.co_name}: Starting metrics collection process.")
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        # Parallel requests to Solana RPC
        current_slot, leader_slots_in_epoch, epoch_data, slot_duration = await asyncio.gather(
            get_current_slot(session),
            get_leader_schedule(session),
            get_epoch(session),
            calculate_slot_duration(session)
        )

    if current_slot is None or leader_slots_in_epoch is None or epoch_data is None or slot_duration is None:
        logger.error("Failed to fetch all required data. Skipping metric collection.")
        return

    first_normal_epoch, first_normal_slot, slots_per_epoch, epoch = epoch_data
    if not all([first_normal_epoch, first_normal_slot, slots_per_epoch, epoch]):
        logger.error("Incomplete epoch data. Skipping metric collection.")
        return

    # Calculate next and previous leader slots
    first_slot_in_epoch = (epoch - first_normal_epoch) * slots_per_epoch + first_normal_slot
    next_slot = next((slot for slot in leader_slots_in_epoch if slot + first_slot_in_epoch > current_slot), None)
    previous_slot = next(
        (slot for slot in reversed(leader_slots_in_epoch) if slot + first_slot_in_epoch < current_slot), 0)

    if next_slot:
        next_slot_epoch = first_slot_in_epoch + next_slot
        time_to_next_slot = (next_slot_epoch - current_slot) * slot_duration
        next_slot_time = datetime.now() + timedelta(seconds=time_to_next_slot)
        next_slot_time = next_slot_time.replace(second=0, microsecond=0)
        next_slot_time_unix = time.mktime(next_slot_time.timetuple())
        logger.debug(f"Next leader slot: {next_slot_epoch} in {time_to_next_slot:.2f}s")

        # Update Prometheus modules
        update_metric(solana_next_leader_slot, next_slot_epoch)
        update_metric(solana_time_to_next_slot, time_to_next_slot)
        update_metric(solana_next_slot_time, next_slot_time_unix)
    else:
        logger.warning("No upcoming leader slots found.")
        solana_next_leader_slot.set(0)
        solana_time_to_next_slot.set(0)
        solana_next_slot_time.set(0)

    previous_slot_epoch = first_slot_in_epoch + previous_slot
    update_metric(solana_previous_leader_slot, previous_slot_epoch)
    update_metric(solana_val_total_leader_slots, len(leader_slots_in_epoch))
    update_metric(solana_avg_slot_duration, slot_duration)
    logger.debug(f"Previous leader slot: {previous_slot_epoch}, Total_leader_slots: {len(leader_slots_in_epoch)}, "
                 f"Avg slot duration: {slot_duration}")
    end_time = time.time()
    logger.success(f"{inspect.currentframe().f_code.co_name}: Metrics successfully collected and exported to "
                   f"Prometheus. Time: {end_time - start_time}")
