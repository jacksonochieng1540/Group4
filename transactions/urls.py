from django.urls import path
from .views import index, check_node_status, get_balances, reset_balances, simulate_failure, get_system_stats

urlpatterns = [
    path('', index, name='index'),
    path('check-node/<int:port>/', check_node_status, name='check_node_status'),
    path('api/balances/', get_balances, name='get_balances'),
    path('api/reset-balances/', reset_balances, name='reset_balances'),
    path('api/simulate-failure/', simulate_failure, name='simulate_failure'),
    path('api/system-stats/', get_system_stats, name='system_stats'),
]