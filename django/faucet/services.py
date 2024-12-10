import os
import time
import redis
from web3 import Web3

# Initialize Redis
cache = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)

class FaucetService:
    @staticmethod
    def validate_address(address):
        """Validate Ethereum address."""
        return Web3.is_address(address)

    @staticmethod
    def is_rate_limited(address, client_ip, timeout):
        """Check if address or IP is rate-limited."""
        address_key = f"faucet_rate_limit_{address}"
        ip_key = f"faucet_rate_limit_{client_ip}"
        return cache.get(address_key) or cache.get(ip_key)

    @staticmethod
    def enforce_rate_limit(address, client_ip, timeout):
        """Set rate limit for address and IP."""
        address_key = f"faucet_rate_limit_{address}"
        ip_key = f"faucet_rate_limit_{client_ip}"
        cache.setex(address_key, timeout, "1")
        cache.setex(ip_key, timeout, "1")

    @staticmethod
    def send_transaction(address):
        """Create, sign, and send a transaction."""
        web3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC")))
        preconfigured_wallet = os.getenv("TREASURY_PUBLIC_KEY")
        private_key = os.getenv("TREASURY_PRIVATE_KEY")

        balance = web3.eth.get_balance(preconfigured_wallet)
        gas_price = web3.eth.gas_price
        gas_limit = 21000
        transaction_fee = gas_price * gas_limit
        send_value = web3.to_wei(0.0001, "ether")

        if balance < send_value + transaction_fee:
            raise ValueError("Insufficient funds in pre-configured wallet")

        # Create and sign transaction
        nonce = web3.eth.get_transaction_count(preconfigured_wallet)
        transaction = {
            "to": address,
            "value": send_value,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": 11155111,  # Sepolia
        }
        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)

        web3.eth.send_raw_transaction(signed_transaction.raw_transaction)

        tx_hash = web3.to_hex(web3.keccak(signed_transaction.raw_transaction))

        # Store in Redis
        cache.hset(f"faucet:tx:{tx_hash}", mapping={
            "address": address,
            "status": "pending",
            "timestamp": str(int(time.time())),
            "rawTransaction": signed_transaction.raw_transaction.hex()
        })

        # Queue for async processing
        cache.rpush("faucet:tx_queue", tx_hash)

        return tx_hash

    @staticmethod
    def get_transaction_stats():
        """Fetch transaction statistics for the last 24 hours."""
        since = int(time.time()) - 86400
        successful_count = cache.zcount("faucet:success", since, "+inf")
        failed_count = cache.zcount("faucet:failed", since, "+inf")
        return {"successful": successful_count, "failed": failed_count}
