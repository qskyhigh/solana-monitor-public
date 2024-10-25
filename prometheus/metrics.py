from prometheus_client import Gauge

# Prometheus Gauges
# balance module
solana_account_balance = Gauge('solana_account_balance', 'Identity account balance')
solana_vote_account_balance = Gauge('solana_vote_account_balance', 'Vote account balance')

# block module
solana_net_skip_rate = Gauge('solana_net_skip_rate', 'Network skip rate')
solana_skipped_total = Gauge('solana_skipped_total', 'Total skipped slots of network in current epoch')
solana_val_blocks_produced = Gauge('solana_val_blocks_produced', 'Blocks produced of a validator in current epoch')
solana_val_skip_rate = Gauge('solana_val_skip_rate', 'Validator skip rate')
solana_val_skipped_slots = Gauge('solana_val_skipped_slots', 'Skipped slots of a validator in current epoch')
solana_total_blocks_produced = Gauge('solana_total_blocks_produced', 'Total blocks produced in current epoch')
solana_skip_rate_diff = Gauge('solana_skip_rate_diff', 'Skip rate difference of network and validator')
solana_val_leader_slots = Gauge('solana_val_leader_slots', 'Leader slots of a validator in current epoch')
solana_total_slots = Gauge('solana_total_slots', 'Total slots in current epoch')
solana_confirmed_epoch_first_slot = Gauge('solana_confirmed_epoch_first_slot', 'First slot in current epoch')
solana_confirmed_epoch_last_slot = Gauge('solana_confirmed_epoch_last_slot', 'Last slot in current epoch')

# epoch module
solana_node_version = Gauge('solana_node_version', 'Node version of solana', ['version'])
solana_network_epoch = Gauge('solana_network_epoch', 'Current epoch of network (max confirmation)')
solana_tx_count = Gauge('solana_tx_count', 'solana transaction count')
solana_slot_in_epoch = Gauge('solana_slot_in_epoch', 'solana_slot_in_epoch')
solana_slot_index = Gauge('solana_slot_index', 'solana_slot_index')

# leader_slot module
solana_val_total_leader_slots = Gauge('solana_val_total_leader_slots', 'Total number of leader slots in current epoch')
solana_next_leader_slot = Gauge('solana_next_leader_slot', 'The next leader slot')
solana_time_to_next_slot = Gauge('solana_time_to_next_slot', 'Time until the next leader slot in seconds')
solana_avg_slot_duration = Gauge('solana_avg_slot_duration', 'Average slot duration in seconds')
solana_next_slot_time = Gauge('solana_next_slot_time', 'Time of the next leader slot')
solana_previous_leader_slot = Gauge('solana_previous_leader_slot', 'The previous leader slot')

# node_health module
solana_node_health = Gauge('solana_node_health', 'Health status of the Solana node', ['status', 'cause'])
solana_node_slots_behind = Gauge('solana_node_slots_behind', 'Number of slots the Solana node is behind')

# slot module
solana_block_height = Gauge('solana_block_height', 'Current Block Height of validator')
solana_network_block_height = Gauge('solana_network_block_height', 'Current Block Height of network')
solana_block_height_diff = Gauge('solana_block_height_diff', 'Current Block Height difference of network and validator')
solana_current_slot = Gauge('solana_current_slot', 'Current validator slot height')
solana_net_current_slot = Gauge('solana_net_current_slot', 'Current network slot height')
solana_slot_diff = Gauge('solana_slot_diff', 'Current slot difference of network and validator')
solana_net_max_shred_insert_slot = Gauge('solana_net_max_shred_insert_slot', 'Get the max NETWORK slot seen from after shred insert')
solana_net_max_retransmit_slot = Gauge('solana_net_max_retransmit_slot', 'Get the max NETWORK slot seen from retransmit stage')
solana_val_max_shred_insert_slot = Gauge('solana_val_max_shred_insert_slot', 'Get the max VALIDATOR slot seen from after shred insert')
solana_val_max_retransmit_slot = Gauge('solana_val_max_retransmit_slot', 'Get the max VALIDATOR slot seen from retransmit stage')

# validator module
solana_active_stake = Gauge('solana_active_stake', 'Active Stake SOLs')
solana_current_stake = Gauge('solana_current_stake', 'Current Stake SOLs')
solana_delinquent_stake = Gauge('solana_delinquent_stake', 'Delinquent Stake SOLs')
solana_val_commission = Gauge('solana_val_commission', 'Solana validator current commission', ['commission'])
solana_active_validators = Gauge('solana_active_validators', 'Total number of active validators by state', ['state'])
solana_validator_activated_stake = Gauge('solana_validator_activated_stake', 'Activated stake per validator',
                                         ['pubkey', 'votekey'])
solana_val_status = Gauge('solana_val_status', 'Solana validator voting status i.e., voting or jailed', ['state'])
solana_vote_credits = Gauge('solana_vote_credits', 'Solana validator vote credits of current epoch')
solana_avg_vote_credits = Gauge('solana_avg_vote_credits', 'Average network vote credits of current epoch')
solana_total_credits = Gauge('solana_total_credits', 'Solana validator vote credits of all epochs')

# vote module
solana_validator_vote_height = Gauge('solana_validator_vote_height',
                                     'Most recent VALIDATOR slot voted on by this vote account',
                                     ['rpc'])
solana_network_vote_height = Gauge('solana_network_vote_height',
                                   'Most recent NETWORK slot voted on by this vote account',
                                   ['rpc'])
solana_vote_height_diff = Gauge('solana_vote_height_diff', 'Vote height difference of validator and network')
