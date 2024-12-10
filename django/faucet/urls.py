from django.contrib import admin
from django.urls import path
from faucet.views import FaucetFundView, FaucetStatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('faucet/fund', FaucetFundView.as_view(), name='faucet-fund'),
    path('faucet/stats', FaucetStatsView.as_view(), name='faucet-stats'),
]
