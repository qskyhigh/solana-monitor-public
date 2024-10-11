import aiohttp
from loguru import logger
from config import HEADERS, VALIDATOR_RPC_ENDPOINT, PORT
from utils.func import update_metric
from prometheus.metrics import solana_node_version

PROMETHEUS_METRICS_URL = f"http://localhost:{PORT}/metrics"


async def get_versions_from_prometheus() -> list:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PROMETHEUS_METRICS_URL) as response:
                response.raise_for_status()
                metrics = await response.text()

        all_versions = [
            line.split('{')[1].split('}')[0].split('=')[1].replace('"', '')
            for line in metrics.splitlines()
            if line.startswith(f'{solana_node_version._name}') and '1.0' in line
        ]
        return all_versions
    except Exception as e:
        logger.error(f"Failed to fetch version from Prometheus: {e}")
        return []


async def get_version():
    all_versions = await get_versions_from_prometheus()
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getVersion"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(VALIDATOR_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                response.raise_for_status()
                result = await response.json()

        current_version = result['result'].get('solana-core')
        for version in all_versions:
            if version and version != current_version:
                update_metric(solana_node_version, 0, labels={"version": version})

        update_metric(solana_node_version, 1, labels={"version": current_version})
        logger.info(f"Node version of solana: {current_version}")

    except Exception as e:
        logger.error(f"Error getting version node: {e}")
