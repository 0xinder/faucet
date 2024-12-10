import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import FaucetService

class FaucetFundView(APIView):
    def post(self, request):
        address = request.data.get("address")
        client_ip = request.META.get("REMOTE_ADDR")
        redis_timeout = int(os.getenv("FAUCET_RATE_LIMIT_SECONDS", 60))  # 1 minute default

        # Validate Ethereum address
        if not FaucetService.validate_address(address):
            return Response({"error": "Invalid Ethereum address"}, status=status.HTTP_400_BAD_REQUEST)

        # Check rate limits
        if FaucetService.is_rate_limited(address, client_ip, redis_timeout):
            return Response({"error": "Rate limit exceeded. Please wait before requesting again."}, 
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            # Send transaction
            tx_hash = FaucetService.send_transaction(address)

            # Enforce rate limit
            FaucetService.enforce_rate_limit(address, client_ip, redis_timeout)

            return Response({"message": "Transaction queued and pending confirmation", "tx_hash": tx_hash}, 
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FaucetStatsView(APIView):
    def get(self, request):
        stats = FaucetService.get_transaction_stats()
        return Response({
            "successful_transactions": stats["successful"],
            "failed_transactions": stats["failed"]
        }, status=status.HTTP_200_OK)
