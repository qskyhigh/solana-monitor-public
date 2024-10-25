import inspect
import json
import time
import aiohttp
import subprocess
from loguru import logger
from config import PUB_KEY, VOTE_PUB_KEY, NETWORK_RPC_ENDPOINT, SOLANA_BINARY_PATH, HEADERS
from utils.func import update_metric
from prometheus.metrics import (solana_active_stake, solana_current_stake, solana_delinquent_stake, solana_vote_credits,
                                solana_active_validators, solana_validator_activated_stake, solana_val_status,
                                solana_total_credits, solana_val_commission, solana_avg_vote_credits)


def get_validators():
    """Fetch validators information using Solana CLI and update Prometheus modules."""
    try:
        result = subprocess.run(
            [SOLANA_BINARY_PATH, "validators", "--output", "json-compact"],
            capture_output=True, text=True, check=True
        )
        logger.info("Successfully executed solana validators command.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while running solana validators command: {e}")
        return None

    # Remove any "Note:" lines that might be in the output
    validators = "\n".join([line for line in result.stdout.splitlines() if "Note:" not in line])

    try:
        # Parse the JSON data from Solana validators
        validators_data = json.loads(validators)
        logger.info("Block production data successfully parsed.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from block production data: {e}")
        return None

    # Return parsed data
    return validators_data


def process_metrics(validators_data):
    if not validators_data:
        logger.warning("No validator data available to process.")
        return

    # Retrieve network modules
    try:
        active_stake = validators_data.get('totalActiveStake') / 10 ** 9
        current_stake = validators_data.get('totalCurrentStake') / 10 ** 9
        delinquent_stake = validators_data.get('totalDelinquentStake') / 10 ** 9
        logger.debug(f'Active Stake: {round(active_stake, 2)}, Current Stake: {round(current_stake, 2)}, '
                     f'Delinquent Stake: {round(delinquent_stake, 2)}')
    except KeyError as e:
        logger.error(f"EKey error when extracting validator-specific modules: {e}")
        return

    # Dictionary mapping Prometheus Gauges to their corresponding values
    update_metric(solana_active_stake, active_stake)
    update_metric(solana_current_stake, current_stake)
    update_metric(solana_delinquent_stake, delinquent_stake)


def validator_metrics():
    logger.info(f"{inspect.currentframe().f_code.co_name}: Starting modules collection process.")
    start_time = time.time()

    # Fetch validators data
    validators_data = get_validators()

    # Process and send modules to Prometheus
    process_metrics(validators_data)

    end_time = time.time()
    logger.success(f"{inspect.currentframe().f_code.co_name}: All modules have been successfully collected and sent "
                   f"to Prometheus. Time: {end_time - start_time}")


async def get_vote_accounts():
    """Fetch vote account information using RPC and update Prometheus metrics."""
    payload = [
        {"jsonrpc": "2.0", "id": 1, "method": "getVoteAccounts", "params": [{"commitment": "recent"}]},
        {"jsonrpc": "2.0", "id": 2, "method": "getEpochInfo"}
    ]

    logger.info(f"{inspect.currentframe().f_code.co_name}: Starting modules collection process.")
    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(NETWORK_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                response.raise_for_status()
                result = await response.json()

        current_val = result[0]['result'].get('current', [])
        delinquent_val = result[0]['result'].get('delinquent', [])
        current_epoch = result[1]['result']['epoch']

        update_metric(solana_active_validators, len(current_val), labels={"state": "current"})
        update_metric(solana_active_validators, len(delinquent_val), labels={"state": "delinquent"})

        logger.debug(f'Current: {len(current_val)}, Delinquent: {len(delinquent_val)}')

        all_vote_credits = []
        vote_account = None

        all_accounts = current_val + delinquent_val

        for account in all_accounts:
            if account.get('nodePubkey') == PUB_KEY:
                vote_account = account
                if account in delinquent_val:
                    logger.error("Your Solana validator is in DELINQUENT state")

            activated_stake = account.get('activatedStake')
            epoch_credits = account.get('epochCredits', [])

            if activated_stake and epoch_credits:
                last_epoch = epoch_credits[-1]
                if last_epoch and current_epoch == last_epoch[0]:
                    vote_credits = last_epoch[1] - last_epoch[2]
                    all_vote_credits.append(vote_credits)

        if all_vote_credits:
            avg_vote_credits = sum(all_vote_credits) / len(all_vote_credits)
            update_metric(solana_avg_vote_credits, avg_vote_credits)
            logger.debug(f'Average Network Vote credits: {avg_vote_credits}')

        if vote_account:
            process_vote_account(vote_account)
        else:
            logger.error("Validator account not found in both current and delinquent lists.")

    except Exception as e:
        logger.error(f"Error fetching or processing vote accounts: {e}")

    end_time = time.time()
    logger.success(f"{inspect.currentframe().f_code.co_name}: Collection completed in {end_time - start_time:.2f} seconds.")


def process_vote_account(vote_account):
    """Process and update metrics for the given vote account."""
    val_stake = vote_account.get('activatedStake') / 10 ** 9
    commission = vote_account.get('commission')
    epoch_vote = vote_account.get('epochVoteAccount')
    root_slot = vote_account.get('rootSlot')
    last_epoch = vote_account.get('epochCredits')[-1]
    vote_credits = last_epoch[1] - last_epoch[2]
    total_credits = last_epoch[1]

    update_metric(solana_validator_activated_stake, val_stake, labels={"pubkey": PUB_KEY, "votekey": VOTE_PUB_KEY})
    update_metric(solana_val_commission, commission, labels={"commission": str(commission)})

    logger.debug(f'Validator Stake: {round(val_stake, 2)}, Commission: {commission}, Epoch vote: {epoch_vote}, '
                 f'Vote credits: {vote_credits}, Total credits: {total_credits}')

    update_metric(solana_val_status, 1 if epoch_vote else 0, labels={"state": "voting" if epoch_vote else "not voting"})
    update_metric(solana_vote_credits, vote_credits)
    update_metric(solana_total_credits, total_credits)

    logger.info("Updated Prometheus metrics for validator.")
