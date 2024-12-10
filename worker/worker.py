import os
import time
import redis
from web3 import Web3


# Load environment variables
ETH_RPC = os.getenv("ETH_RPC")
TREASURY_PUBLIC_KEY = os.getenv("TREASURY_PUBLIC_KEY")
TREASURY_PRIVATE_KEY = os.getenv("TREASURY_PRIVATE_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")

# Initialize Redis connection
cache = redis.Redis(host=REDIS_HOST, port=6379, db=0)

# Initialize Web3 connection
web3 = Web3(Web3.HTTPProvider(ETH_RPC))

def process_transaction():
    """
    Fetch and monitor the status of a transaction from the Redis queue.
    """
    try:
        # Block until a transaction hash is available
        _, tx_hash = cache.blpop("faucet:tx_queue")
        tx_hash = tx_hash.decode("utf-8")
        print(f"Processing transaction {tx_hash}")

        tx_key = f"faucet:tx:{tx_hash}"

        # Poll for confirmation
        start_time = time.time()
        confirmed = False
        while time.time() - start_time < 120:  # 2 minutes timeout
            try:
                receipt = web3.eth.get_transaction_receipt(tx_hash)
                if receipt is not None:
                    if receipt.status == 1:
                        # Success
                        print(f"Transaction {tx_hash} confirmed successfully.")
                        cache.hset(tx_key, "status", "success")
                        cache.zadd("faucet:success", {tx_hash: int(time.time())})
                        cache.hincrby("faucet:stats", "success", 1)
                        confirmed = True
                        break
                    else:
                        # Failed on-chain
                        print(f"Transaction {tx_hash} failed on-chain.")
                        cache.hset(tx_key, "status", "failed")
                        cache.zadd("faucet:failed", {tx_hash: int(time.time())})
                        cache.hincrby("faucet:stats", "failed", 1)
                        confirmed = True
                        break
            except Exception as e:
                print(f"Error checking receipt for {tx_hash}: {e}")
            time.sleep(5)

        if not confirmed:
            # Timed out
            print(f"Transaction {tx_hash} not confirmed within timeout.")
            cache.hset(tx_key, "status", "failed")
            cache.zadd("faucet:failed", {tx_hash: int(time.time())})
            cache.hincrby("faucet:stats", "failed", 1)

    except Exception as e:
        print(f"Unexpected error in worker: {e}")


def worker_loop():
    """
    Main worker loop.
    Continuously processes transactions from the Redis queue.
    """
    print("Worker started. Listening for transactions...")
    while True:
        try:
            process_transaction()
        except Exception as e:
            print(f"Worker loop error: {e}")
            time.sleep(5)  # Sleep briefly to avoid rapid error loops


if __name__ == "__main__":
    worker_loop()
