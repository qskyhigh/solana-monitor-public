import asyncio
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import THREAD_POOL_SIZE
from modules.balance import balance_metrics
from modules.block import block_metrics
from modules.epoch import get_epoch_information
from modules.validator import validator_metrics, get_vote_accounts
from modules.version import get_version
from modules.leader_slot import leader_slot_metrics
from modules.node_health import get_health
from modules.slot import get_block_height, get_slots
from modules.vote import get_votes


def run_sync_tasks():
    sync_tasks = [
        block_metrics,
        validator_metrics
    ]

    with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as executor:
        futures = [executor.submit(task) for task in sync_tasks]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error collecting sync metric: {e}, task: {future}")


async def run_async_tasks():
    async_tasks = {
        "get_block_height": get_block_height(),
        "get_slots": get_slots(),
        "get_votes": get_votes(),
        "balance_metrics": balance_metrics(),
        "get_vote_accounts": get_vote_accounts(),
        "leader_slot_metrics": leader_slot_metrics(),
        "get_epoch_information": get_epoch_information(),
        "get_health": get_health(),
        "get_version": get_version()
    }

    try:
        results = await asyncio.gather(*async_tasks.values(), return_exceptions=True)

        for task, result in zip(async_tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"{task.upper()}: {result}", exc_info=True)
    except Exception as e:
        logger.error(f"Error collecting async metric: {e}")


async def collect():
    loop = asyncio.get_event_loop()
    sync_task = loop.run_in_executor(None, run_sync_tasks)
    async_task = run_async_tasks()
    await asyncio.gather(sync_task, async_task)
