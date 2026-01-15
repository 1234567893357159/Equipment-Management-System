from django.urls import path
from .finance_integration import finance_payment_callback

urlpatterns = [
    path('callback/', finance_payment_callback, name='finance_payment_callback'),
]
