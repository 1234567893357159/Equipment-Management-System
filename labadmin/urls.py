from django.urls import path, include
from . import views
from devices.views import device_manage, device_delete, device_detail

urlpatterns = [
    # 管理员首页
    path('home/', views.admin_home, name='admin_home'),
    # 预约审批页
    path('booking/approve/', views.booking_approve, name='booking_approve'),
    # 设备管理页
    path('device/manage/', device_manage, name='device_manage'),
    # 设备详情/编辑页（接收设备ID pk）
    path('device/detail/<int:pk>/', device_detail, name='device_detail'),
    # 报表统计页
    path('report/', views.report_stat, name='report_stat'),
    # 报表导出
    path('report/export/<int:report_id>/', views.export_report_csv, name='export_report_csv'),
    # 报表删除
    path('report/delete/<int:report_id>/', views.delete_report, name='delete_report'),
]