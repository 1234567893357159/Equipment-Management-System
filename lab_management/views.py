from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Q
from devices.models import Device

from user.models import UserInfo
from user.forms import UserInfoForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from user.models import UserInfo  # 导入你的用户信息模型
from jnu_lab_system.multi_role_session import set_role_session_user, get_user_from_role_session, clear_role_session

@require_http_methods(["GET", "POST"])
@csrf_protect
def user_login(request):
    """系统登录视图：校验账号密码 + 角色匹配"""
    # 如果是POST请求（提交登录表单）
    if request.method == 'POST':
        # 1. 获取表单数据
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()
        
        # 2. 基础校验：必填项不能为空
        if not username or not password or not role:
            return render(request, 'login.html', {
                'error': '请填写完整的登录信息！'
            })
        
        # 3. 校验账号密码
        user = authenticate(request, username=username, password=password)
        if not user:
            return render(request, 'login.html', {
                'error': '用户名或密码错误！'
            })
        
        # 4. 校验角色是否匹配
        role_error = None
        if role == 'user':
            # 普通用户：必须关联UserInfo，且状态正常
            try:
                user_info = UserInfo.objects.get(auth_user=user)
                if not user_info.is_active:
                    role_error = '该账号已被禁用，无法登录！'
            except UserInfo.DoesNotExist:
                role_error = '该账号不是普通用户（学生/教师/校外人员）！'
        
        elif role == 'admin':
            # 设备管理员：必须属于「设备管理员」组，或超级管理员
            if not (user.groups.filter(name='设备管理员').exists() or user.is_superuser):
                role_error = '该账号不是设备管理员！'
        
        elif role == 'manager':
            # 实验室负责人：必须属于「实验室负责人」组
            if not user.groups.filter(name='实验室负责人').exists():
                role_error = '该账号不是实验室负责人！'
        
        else:
            role_error = '请选择正确的用户角色！'
        
        # 角色校验失败：返回错误
        if role_error:
            return render(request, 'login.html', {
                'error': role_error
            })
        
        # 5. 所有校验通过：登录并跳转对应首页
        # 多角色支持：使用角色特定的session存储，允许同一浏览器同时登录多个角色
        # 关键策略：
        # 1. 将用户信息存储到角色特定的session中（多角色支持的核心）
        # 2. 同时执行标准的login()，确保@login_required装饰器能正常工作
        # 3. 中间件会根据URL路径优先从角色特定的session中读取用户，替换request.user
        
        # 将用户信息存储到角色特定的session中（多角色支持的核心）
        role_map = {
            'user': 'user',
            'admin': 'admin',
            'manager': 'manager'
        }
        if role in role_map:
            set_role_session_user(request, user, role_map[role])
        
        # 执行标准的login()，确保@login_required装饰器能正常工作
        # 注意：这不会清除角色特定的session，因为它们是不同的key
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # 强制刷新session，确保session被保存
        request.session.save()
        
        # 根据角色跳转到对应首页
        if role == 'user':
            return redirect('user_home')  # 普通用户首页
        elif role == 'admin':
            return redirect('admin_home')  # 设备管理员首页
        elif role == 'manager':
            return redirect('manager_home')  # 实验室负责人首页
        else:
            logout(request)
            return render(request, 'login.html', {
                'error': '角色验证失败，请重新登录！'
            })
    
    # GET请求：显示登录页面
    return render(request, 'login.html')

# 可选：退出登录视图
def user_logout(request):
    """退出登录 - 支持多角色，只清除当前角色的session"""
    # 从URL路径判断角色，清除对应的角色session
    from jnu_lab_system.multi_role_session import get_role_from_path, clear_role_session
    
    # 尝试从referer或当前路径判断角色
    referer = request.META.get('HTTP_REFERER', '')
    role = get_role_from_path(referer) or get_role_from_path(request.path)
    
    if role:
        # 清除当前角色的session
        clear_role_session(request, role)
        # 如果还有其他角色登录，不清除标准session
        # 否则清除标准session
        has_other_roles = False
        for r in ['user', 'admin', 'manager']:
            if r != role:
                role_user = get_user_from_role_session(request, r)
                if role_user:
                    has_other_roles = True
                    break
        
        if not has_other_roles:
            # 没有其他角色登录，清除标准session
            logout(request)
    else:
        # 无法判断角色，清除所有session
        logout(request)
        # 清除所有角色特定的session
        for r in ['user', 'admin', 'manager']:
            clear_role_session(request, r)
    
    return redirect('user_login')

# ---------------------- 管理员视图 ----------------------
def admin_home(request):
    return render(request, 'admin/home.html')

def booking_approve(request):
    # 模拟审批操作后刷新页面
    if request.method == 'POST':
        return redirect('booking_approve')
    return render(request, 'admin/booking_approve.html')

def device_manage(request):
    return render(request, 'admin/device_manage.html')

def report_stat(request):
    return render(request, 'admin/report_stat.html')

