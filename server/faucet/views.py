from web3 import Web3
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .serializers import FundRequestSerializer
import os

class FaucetFundView(APIView):
    def post(self, request):
        address = request.data.get("address")
        client_ip = request.META.get("REMOTE_ADDR")
        redis_timeout = int(os.getenv("FAUCET_RATE_LIMIT_SECONDS", 60))  # Default timeout is 1 minute

        if not Web3.is_address(address):
            return Response({"error": "Invalid Ethereum address"}, status=status.HTTP_400_BAD_REQUEST)
        
        address_key = f"faucet_rate_limit_{address}"
        ip_key = f"faucet_rate_limit_{client_ip}"

        if cache.get(address_key) or cache.get(ip_key):
            return Response({"error": "Rate limit exceeded. Please wait before requesting again."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        web3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC")))
        preconfigured_wallet = os.getenv("TREASURY_PUBLIC_KEY")
        private_key = os.getenv("TREASURY_PRIVATE_KEY")

        try:
            # Check balance of the pre-configured wallet
            balance = web3.eth.get_balance(preconfigured_wallet)
            gas_price = web3.eth.gas_price
            gas_limit = 21000
            transaction_fee = gas_price * gas_limit
            send_value = web3.to_wei(0.0001, "ether")

            if balance < send_value + transaction_fee:
                return Response({"error": "Insufficient funds in pre-configured wallet"}, status=status.HTTP_400_BAD_REQUEST)

            # Create transaction
            nonce = web3.eth.get_transaction_count(preconfigured_wallet)
            transaction = {
                "to": address,
                "value": send_value,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": 11155111,  # Sepolia chain ID
            }

            # Sign transaction
            signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)

            # Send transaction
            tx_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)

            # Set rate limit in Redis
            cache.set(address_key, True, timeout=redis_timeout)
            cache.set(ip_key, True, timeout=redis_timeout)

            return Response({
                "message": "Transaction sent", 
                "tx_hash": tx_hash.hex()
            }, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FaucetStatsView(APIView):
    def get(self, request):
        successful_transactions = int(cache.get("faucet_successful_transactions") or 0)
        failed_transactions = int(cache.get("faucet_failed_transactions") or 0)

        return Response({
            "successful_transactions": successful_transactions,
            "failed_transactions": failed_transactions
        }, status=status.HTTP_200_OK)
