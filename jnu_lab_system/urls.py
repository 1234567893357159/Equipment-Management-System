from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 挂载应用路由
    path('', include('lab_management.urls')),
    path('ledger/', include('ledger.urls')),
    # 财务处回调接口
    path('booking/finance/', include('booking.urls')),
]