import yaml

HEADERS = {'Content-Type': 'application/json'}

with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

PUB_KEY = config.get("pub_key")
VOTE_PUB_KEY = config.get("vote_pub_key")
NETWORK_RPC_ENDPOINT = config.get("network_rpc_endpoint", "https://api.testnet.solana.com")
VALIDATOR_RPC_ENDPOINT = config.get("validator_rpc_endpoint", "http://localhost:8899")
SOLANA_BINARY_PATH = config.get("solana_binary_path", "solana")

THREAD_POOL_SIZE = config.get("thread_pool_size", 4)
SLEEP_TIME = config.get("sleep_time", 45)
PORT = config.get("metric_port", 1234)
LOG_LEVEL = config.get("log_level", "INFO")
RETRY = config.get("retry", 5)



