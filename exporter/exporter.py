import asyncio
import signal
from prometheus_client import start_http_server
import time
from exporter.collector import collect
from loguru import logger
from config import SLEEP_TIME, PORT, LOG_LEVEL


async def graceful_shutdown(loop, sig=None):
    """Handles graceful shutdown on receiving a signal"""
    if sig:
        logger.info(f"Received exit signal {sig.name}...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def setup_signals(loop):
    """Setup signal handling for graceful shutdown"""
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown(loop, sig)))


async def run_exporter():
    """Main function to run the Prometheus exporter"""
    logger.info(f"Starting Prometheus metrics server on localhost:{PORT}/metrics")
    start_http_server(PORT)

    while True:
        start_time = time.time()
        logger.info("Starting collection of metrics")
        try:
            await collect()
            logger.info(f"Metrics collected successfully in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error during metrics collection: {e}")

        logger.info(f"💤 Sleeping for {SLEEP_TIME} seconds")
        await asyncio.sleep(SLEEP_TIME)


def main():
    logger.add("logs/monitor.log",
               level=LOG_LEVEL,
               rotation="00:00",
               retention="6 days",
               compression=None,
               backtrace=True,
               diagnose=True,
               enqueue=True)

    loop = asyncio.get_event_loop()
    setup_signals(loop)  # Graceful shutdown signal setup
    try:
        loop.run_until_complete(run_exporter())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down Prometheus exporter")
        loop.close()
