from django.urls import path, include
from . import views
from booking.views import booking_apply, cancel_booking, my_booking, device_booking_detail, check_availability

urlpatterns = [
    # 普通用户首页
    path('home/', views.user_home, name='user_home'),
    # 设备查询页
    path('device/list/', views.device_list, name='device_list'),
    # 设备预约详情路由
    path('device/booking/<int:device_id>/', device_booking_detail, name='device_booking_detail'),
    # 预约申请页
    path('booking/apply/', booking_apply, name='booking_apply'),
    # 查询空闲状态
    path('check-availability/', check_availability, name='check_availability'),
    # 我的预约页
    path('booking/my/', my_booking, name='my_booking'),
    # 删除预约
    path('booking/cancel/<int:booking_id>/', cancel_booking, name='cancel_booking'),
    # 个人信息页
    path('profile/', views.user_profile, name='user_profile'),
    path('change-password/', views.change_password, name='change_password'),
    # 注册页
    path('register/', views.register_view, name='register'),
    # 教师指导学生管理
    path('student/add/', views.add_student, name='add_student'),
    path('student/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('student/remove/<int:student_id>/', views.remove_student, name='remove_student'),
    # 教师新增学生
    path('student/add/', views.add_student, name='add_student'),  # 第一步
    path('student/add/full/', views.add_student_full, name='add_student_full'),  # 第二步
]