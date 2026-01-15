from django.urls import path
from . import views

urlpatterns = [
    # 负责人首页
    path('home/', views.manager_home, name='manager_home'),
    # 校外人员审批页
    path('booking/approve/', views.booking_approve, name='manager_booking_approve'),
    # 用户管理核心路由
    path('user/manage/', views.user_manage, name='user_manage'),          # 用户列表/新增
    path('user/edit/<int:pk>/', views.user_edit, name='user_edit'),      # 编辑用户
    path('user/delete/<int:pk>/', views.user_delete, name='user_delete'),# 删除用户
    path('user/toggle/<int:pk>/', views.user_toggle_status, name='user_toggle_status'),  # 切换状态
    path('user/export/', views.user_export_ledger, name='user_export_ledger'),  # 导出用户台账
    # 报表
    path('report/', views.manager_report_stat, name='manager_report_stat'),
    # 报表导出
    path('report/export/<int:report_id>/', views.manager_export_report_csv, name='manager_export_report_csv'),
]