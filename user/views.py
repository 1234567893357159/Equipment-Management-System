from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Q
from user.models import UserInfo
from user.forms import UserInfoForm
from django.contrib.auth.hashers import make_password  # 密码加密
from django.contrib.auth import update_session_auth_hash  # 保持登录状态

# 以下是创建角色组和初始用户的代码
from django.contrib.auth.models import User, Group, Permission

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

from booking.models import Booking, ApprovalRecord
from user.models import UserInfo
from devices.models import Device

from .forms import RegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from django.contrib.auth.decorators import user_passes_test
# 添加 StudentForm
from .forms import UserInfoForm, RegistrationForm, StudentForm, StudentIdForm



@login_required
@csrf_protect
def user_profile(request):
    """个人信息管理视图"""
    # 获取当前登录用户关联的UserInfo
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
    except UserInfo.DoesNotExist:
        messages.error(request, '未找到你的个人信息，请联系管理员！')
        # 确保重定向到首页，不会导致循环跳转
        return redirect('user_home')
    
    # 教师用户：获取指导的学生列表（通过多对多关系）
    advisor_students = []
    if user_info.user_type == 'teacher':
        advisor_students = user_info.students.all()  # 通过反向关系获取学生
    
    # 处理表单提交
    if request.method == 'POST':
        try:
            # 获取并验证基础信息
            name = request.POST.get('name', '').strip()
            gender = request.POST.get('gender', '').strip()
            department = request.POST.get('department', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            # 基础字段验证
            if not name:
                messages.error(request, '姓名不能为空！')
                return render(request, 'user/user_profile.html', {
                    'user_info': user_info,
                    'advisor_students': advisor_students
                })
            
            if not gender or gender not in ['男', '女']:
                messages.error(request, '请选择有效的性别！')
                return render(request, 'user/user_profile.html', {
                    'user_info': user_info,
                    'advisor_students': advisor_students
                })
            
            if not department:
                messages.error(request, '所在学院/单位不能为空！')
                return render(request, 'user/user_profile.html', {
                    'user_info': user_info,
                    'advisor_students': advisor_students
                })
            
            if not phone:
                messages.error(request, '联系电话不能为空！')
                return render(request, 'user/user_profile.html', {
                    'user_info': user_info,
                    'advisor_students': advisor_students
                })
            
            # 更新基础信息
            user_info.name = name
            user_info.gender = gender
            user_info.department = department
            user_info.phone = phone
            
            # 更新不同用户类型的专属字段
            if user_info.user_type == 'student':
                major = request.POST.get('major', '').strip()
                user_info.major = major if major else None
                # 指导教师通过多对多关系管理，不在个人信息中直接修改
            elif user_info.user_type == 'teacher':
                title = request.POST.get('title', '').strip()
                research_field = request.POST.get('research_field', '').strip()
                user_info.title = title if title else None
                user_info.research_field = research_field if research_field else None
            elif user_info.user_type == 'external':
                position = request.POST.get('position', '').strip()
                company_address = request.POST.get('company_address', '').strip()
                user_info.position = position if position else None
                user_info.company_address = company_address if company_address else None
            
            # 保存修改
            user_info.save()
            messages.success(request, '个人信息修改成功！')
            return redirect('user_profile')
            
        except Exception as e:
            messages.error(request, f'保存失败：{str(e)}')
            return render(request, 'user/user_profile.html', {
                'user_info': user_info,
                'advisor_students': advisor_students
            })
    
    # GET请求：渲染页面
    context = {
        'user_info': user_info,
        'advisor_students': advisor_students
    }
    return render(request, 'user/user_profile.html', context)

# 新增：修改密码视图（简单版）
@login_required
@csrf_protect
def change_password(request):
    """修改密码视图（完整版）"""
    # 如果是POST请求（提交改密表单）
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # 1. 空值校验
        if not old_password or not new_password or not confirm_password:
            messages.error(request, '请填写所有密码字段！')
            return render(request, 'user/change_password.html')
        
        # 2. 验证原密码是否正确
        if not request.user.check_password(old_password):
            messages.error(request, '原密码输入错误，请重新输入！')
            return render(request, 'user/change_password.html')
        
        # 3. 验证新密码长度
        # if len(new_password) < 6:
        #     messages.error(request, '新密码长度不能少于6位！')
        #     return render(request, 'user/change_password.html')
        
        # 4. 验证两次新密码是否一致
        if new_password != confirm_password:
            messages.error(request, '两次输入的新密码不一致！')
            return render(request, 'user/change_password.html')
        
        # 5. 验证新密码是否和原密码相同
        if new_password == old_password:
            messages.error(request, '新密码不能和原密码相同！')
            return render(request, 'user/change_password.html')
        
        # 6. 所有校验通过，更新密码
        request.user.set_password(new_password)
        request.user.save()
        
        # 关键：保持用户登录状态（否则改密后会自动登出）
        update_session_auth_hash(request, request.user)
        
        messages.success(request, '密码修改成功！')
        return redirect('user_profile')  # 改密成功后返回个人信息页
    
    # GET请求：显示改密页面
    return render(request, 'user/change_password.html')


# ---------------------- 普通用户视图 ----------------------
@login_required
def user_home(request):
    """用户首页视图"""
    # 验证用户身份：确保request.user是正确的用户
    # 防止session混淆导致的身份切换
    if not request.user.is_authenticated:
        from django.contrib.auth import logout
        logout(request)
        messages.error(request, '登录已过期，请重新登录！')
        return redirect('user_login')
    
    # 验证用户是否有UserInfo（普通用户必须有）
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
        # 如果用户是管理员或负责人，不应该访问普通用户首页
        is_admin = request.user.groups.filter(name='设备管理员').exists()
        is_manager = request.user.groups.filter(name='实验室负责人').exists()
        if is_admin or is_manager or request.user.is_superuser:
            # 管理员或负责人访问普通用户首页，重定向到对应首页
            if is_admin or request.user.is_superuser:
                return redirect('admin_home')
            elif is_manager:
                return redirect('manager_home')
    except UserInfo.DoesNotExist:
        # 如果没有UserInfo，可能是管理员或负责人
        is_admin = request.user.groups.filter(name='设备管理员').exists()
        is_manager = request.user.groups.filter(name='实验室负责人').exists()
        if is_admin or request.user.is_superuser:
            return redirect('admin_home')
        elif is_manager:
            return redirect('manager_home')
        else:
            # 既不是管理员也不是负责人，也没有UserInfo，这是异常情况
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, '用户信息异常，请重新登录！')
            return redirect('user_login')
    
    return render(request, 'user/home.html')

@login_required
def device_list(request):
    """
    用户端设备查询视图
    对应路径：/user/device/list/
    """
    # 1. 处理搜索逻辑
    keyword = request.GET.get('keyword', '')
    # 基础查询：获取所有设备（按编号排序）
    devices = Device.objects.all().order_by('device_code')
    
    # 如果有搜索关键词，过滤结果
    if keyword:
        devices = devices.filter(
            Q(device_code__icontains=keyword) |  # 按设备编号搜索
            Q(model__icontains=keyword) |        # 按型号搜索
            Q(manufacturer__icontains=keyword) | # 按厂商搜索
            Q(purpose__icontains=keyword)        # 按实验用途搜索
        )

    # 2. 准备上下文数据
    context = {
        'devices': devices,
        'keyword': keyword,  # 回显搜索关键词
    }
    return render(request, 'user/device_list.html', context)

# 用户注册功能

@csrf_protect
def register_view(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # 提取表单数据
            user_code = form.cleaned_data['user_code']
            password = form.cleaned_data['password']
            name = form.cleaned_data['name']
            gender = form.cleaned_data['gender']
            user_type = form.cleaned_data['user_type']
            department = form.cleaned_data['department']
            phone = form.cleaned_data['phone']
            
            try:
                # 1. 创建Django内置User（登录账号）
                user = User.objects.create_user(
                    username=user_code,  # 使用user_code作为用户名
                    password=password,
                    first_name=name,  # 将姓名存储到first_name字段
                    is_active=True  # 默认激活
                )
                
                # 2. 创建UserInfo记录
                user_info = UserInfo.objects.create(
                    user_code=user_code,
                    name=name,
                    gender=gender,
                    user_type=user_type,
                    department=department,
                    phone=phone,
                    auth_user=user  # 关联到Django User
                )
                
                # 3. 根据用户类型设置其他字段的默认值
                if user_type == 'student':
                    user_info.major = ''  # 留空，用户可后续补充
                    user_info.approval_status = 'approved'  # 学生直接通过
                    # 学生账号直接激活
                    user.is_active = True
                elif user_type == 'teacher':
                    user_info.title = ''
                    user_info.research_field = ''
                    user_info.approval_status = 'pending'  # 教师需要审核
                    # 教师账号待审核，暂时禁用登录
                    user.is_active = False
                elif user_type == 'external':
                    user_info.position = ''
                    user_info.company_address = ''
                    user_info.approval_status = 'approved'  # 校外人员直接通过
                    user.is_active = True
                
                user.save()  # 保存User的is_active状态
                user_info.save()
                
                # 根据用户类型显示不同的提示信息
                if user_type == 'student':
                    messages.success(request, f'注册成功！请使用用户编号 {user_code} 登录')
                elif user_type == 'teacher':
                    messages.info(request, f'注册成功！您的账号已提交审核，审核通过后即可登录。请使用用户编号 {user_code} 登录')
                else:
                    messages.success(request, f'注册成功！请使用用户编号 {user_code} 登录')
                
                return redirect('user_login')
                
            except Exception as e:
                messages.error(request, f'注册失败：{str(e)}')
                return render(request, 'user/register.html', {'form': form})
    else:
        form = RegistrationForm()
    
    return render(request, 'user/register.html', {'form': form})


def teacher_required(function=None):
    """装饰器：检查用户是否是教师"""
    actual_decorator = user_passes_test(
        lambda u: hasattr(u, 'userinfo') and u.userinfo.user_type == 'teacher',
        login_url='user_home',  # 改为重定向到首页，避免循环跳转
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

@login_required
@teacher_required
@csrf_protect
def add_student(request):
    """教师添加指导学生 - 第一步：输入学号"""
    teacher_info = UserInfo.objects.get(auth_user=request.user)
    
    if request.method == 'POST':
        form = StudentIdForm(request.POST)
        if form.is_valid():
            user_code = form.cleaned_data['user_code']
            
            try:
                # 检查学号是否已存在
                existing_student = UserInfo.objects.get(user_code=user_code)
                
                if existing_student.user_type == 'student':
                    # 如果学生已存在，添加到指导教师的多对多关系中
                    if teacher_info not in existing_student.advisors.all():
                        existing_student.advisors.add(teacher_info)
                        messages.success(request, f'学生 {existing_student.name} 已注册，成功添加为您的学生！')
                    else:
                        messages.info(request, f'学生 {existing_student.name} 已经是您的学生了！')
                    return redirect('user_profile')
                else:
                    # 存在但不是学生类型
                    messages.error(request, f'学号 {user_code} 对应的用户不是学生，无法添加！')
                    return render(request, 'user/add_student_step1.html', {
                        'form': form,
                        'teacher_info': teacher_info,
                    })
                    
            except UserInfo.DoesNotExist:
                # 学号不存在，进入第二步填写完整信息
                # 将学号存入session
                request.session['adding_student_code'] = user_code
                return redirect('add_student_full')
    
    else:
        form = StudentIdForm()
    
    context = {
        'form': form,
        'teacher_info': teacher_info,
        'title': '添加学生 - 第一步',
    }
    return render(request, 'user/add_student_step1.html', context)

@login_required
@teacher_required
@csrf_protect
def add_student_full(request):
    """教师添加指导学生 - 第二步：填写完整信息（学号不存在时）"""
    teacher_info = UserInfo.objects.get(auth_user=request.user)
    
    # 从session获取学号
    user_code = request.session.get('adding_student_code')
    if not user_code:
        messages.error(request, '请先输入学号！')
        return redirect('add_student')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, teacher_name=teacher_info.name)
        if form.is_valid():
            try:
                # 1. 创建Django内置User（登录账号）
                password = user_code  # 默认密码为学号
                user = User.objects.create_user(
                    username=user_code,
                    password=password,
                    first_name=form.cleaned_data['name'],
                    is_active=True
                )
                
                # 2. 创建UserInfo记录
                student = form.save(commit=False)
                student.user_code = user_code  # 使用session中的学号
                student.auth_user = user
                student.user_type = 'student'
                student.is_active = True
                student.save()
                
                # 3. 将学生添加到教师的多对多关系中
                student.advisors.add(teacher_info)
                
                # 4. 清除session
                if 'adding_student_code' in request.session:
                    del request.session['adding_student_code']
                
                messages.success(request, f'成功注册并添加学生 {student.name}！')
                return redirect('user_profile')
                
            except Exception as e:
                messages.error(request, f'添加失败：{str(e)}')
        else:
            # 表单验证失败
            messages.error(request, '表单填写有误，请检查后重新提交！')
    else:
        # 初始化表单，预填学号
        form = StudentForm(teacher_name=teacher_info.name)
        form.fields['user_code'].initial = user_code
        form.fields['user_code'].widget.attrs['readonly'] = True
    
    context = {
        'form': form,
        'title': '添加学生 - 第二步',
        'teacher_info': teacher_info,
        'user_code': user_code,
    }
    return render(request, 'user/add_student_step2.html', context)

@login_required
@teacher_required
@csrf_protect
def edit_student(request, student_id):
    """教师编辑学生信息"""
    # 获取当前教师信息
    teacher_info = UserInfo.objects.get(auth_user=request.user)
    
    # 获取学生信息，确保该学生是指定教师指导的
    student = get_object_or_404(UserInfo, id=student_id, user_type='student')
    
    # 验证学生是否在当前教师的学生列表中
    if teacher_info not in student.advisors.all():
        messages.error(request, '您无权编辑该学生信息！')
        return redirect('user_profile')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student, teacher_name=teacher_info.name)
        if form.is_valid():
            try:
                # 更新学生信息
                form.save()
                
                # 更新关联的User信息（姓名）
                if student.auth_user:
                    student.auth_user.first_name = form.cleaned_data['name']
                    student.auth_user.save()
                
                messages.success(request, '学生信息更新成功！')
                return redirect('user_profile')
                
            except Exception as e:
                messages.error(request, f'更新失败：{str(e)}')
        else:
            # 表单验证失败
            messages.error(request, '表单填写有误，请检查后重新提交！')
    else:
        form = StudentForm(instance=student, teacher_name=teacher_info.name)
    
    context = {
        'form': form,
        'title': '编辑学生信息',
        'student': student,
        'teacher_info': teacher_info,
    }
    return render(request, 'user/student_form.html', context)

@login_required
@teacher_required
@csrf_protect
def remove_student(request, student_id):
    """教师移除指导学生（软删除）"""
    # 获取当前教师信息
    teacher_info = UserInfo.objects.get(auth_user=request.user)
    
    # 获取学生信息，确保该学生是指定教师指导的
    student = get_object_or_404(UserInfo, id=student_id, user_type='student')
    
    # 验证学生是否在当前教师的学生列表中
    if teacher_info not in student.advisors.all():
        messages.error(request, '您无权移除该学生！')
        return redirect('user_profile')
    
    if request.method == 'POST':
        try:
            # 从多对多关系中移除
            student.advisors.remove(teacher_info)
            messages.success(request, f'已移除学生 {student.name}')
        except Exception as e:
            messages.error(request, f'移除失败：{str(e)}')
    
    return redirect('user_profile')