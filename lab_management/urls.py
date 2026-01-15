from django.urls import path, include
from . import views
from devices.views import device_manage, device_delete, device_detail

urlpatterns = [
    # 首页/登录页
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),

    # 普通用户
    path('user/', include('user.urls')),

    # 管理员
    path('labadmin/', include('labadmin.urls')),
    # 设别删除
    path('device/delete/<int:pk>/', device_delete, name='device_delete'),
    
    # 负责人
    path('manager/', include('manager.urls')),
]