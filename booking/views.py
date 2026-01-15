from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from user.models import UserInfo
from devices.models import Device
from .models import Booking, ApprovalRecord
from .utils import generate_booking_code
from django.http import JsonResponse
from django.urls import reverse
from datetime import date, timedelta, datetime
from decimal import Decimal

# 1. 设备预约申请页面
@login_required
@csrf_protect
def booking_apply(request):
    """设备预约申请视图"""
    # 获取当前登录用户的信息
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
    except UserInfo.DoesNotExist:
        messages.error(request, '未找到你的个人信息，请联系管理员！')
        return redirect('user_home')
    
    # 获取所有设备
    # 注意：设备状态只表示物理状态（正常/维修中/已报废），时段可用性由预约情况决定
    devices = Device.objects.all().order_by('device_code')
    
    if request.method == 'POST':
        # 获取表单数据
        device_code = request.POST.get('device_id')
        booking_date_str = request.POST.get('booking_date')
        time_slot = request.POST.get('time_slot')
        purpose = request.POST.get('purpose')
        teacher_id = request.POST.get('teacher_id', '')
        
        # 验证预约日期格式
        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, '预约日期格式错误！')
            student_advisors = user_info.advisors.all() if user_info.user_type == 'student' else []
            return render(request, 'user/booking_apply.html', {
                'user_info': user_info,
                'devices': devices,
                'student_advisors': student_advisors
            })
        
        # 验证预约日期：必须提前1-7天
        today = date.today()
        min_date = today + timedelta(days=1)
        max_date = today + timedelta(days=7)
        
        if booking_date < min_date:
            messages.error(request, f'预约日期必须至少提前1天！最早可预约日期：{min_date.strftime("%Y-%m-%d")}')
            student_advisors = user_info.advisors.all() if user_info.user_type == 'student' else []
            return render(request, 'user/booking_apply.html', {
                'user_info': user_info,
                'devices': devices,
                'student_advisors': student_advisors
            })
        
        if booking_date > max_date:
            messages.error(request, f'预约日期不能超过7天！最晚可预约日期：{max_date.strftime("%Y-%m-%d")}')
            student_advisors = user_info.advisors.all() if user_info.user_type == 'student' else []
            return render(request, 'user/booking_apply.html', {
                'user_info': user_info,
                'devices': devices,
                'student_advisors': student_advisors
            })
        
        # 校验设备是否存在
        try:
            device = Device.objects.get(device_code=device_code)
        except Device.DoesNotExist:
            messages.error(request, '该设备不存在！')
            student_advisors = user_info.advisors.all() if user_info.user_type == 'student' else []
            return render(request, 'user/booking_apply.html', {
                'user_info': user_info,
                'devices': devices,
                'student_advisors': student_advisors
            })
        
        # 检查设备状态：如果设备是"维修中"或"已报废"，不允许预约
        if device.status in ['maintenance', 'discarded']:
            messages.error(request, f'该设备状态为"{device.get_status_display()}"，不允许预约！')
            student_advisors = user_info.advisors.all() if user_info.user_type == 'student' else []
            return render(request, 'user/booking_apply.html', {
                'user_info': user_info,
                'devices': devices,
                'student_advisors': student_advisors
            })
        
        # 检查设备冲突（校内人员优先规则）
        conflict_bookings = Booking.objects.filter(
            device=device,
            booking_date=booking_date,
            time_slot=time_slot,
            status__in=['teacher_pending', 'pending', 'admin_approved', 'manager_approved', 'payment_pending']
        )
        
        # 如果新预约是校内人员，检查是否有校外人员预约
        if user_info.user_type in ['student', 'teacher']:
            external_conflicts = conflict_bookings.filter(applicant__user_type='external')
            if external_conflicts.exists():
                # 校内人员优先：自动取消校外人员预约
                for conflict in external_conflicts:
                    conflict.status = 'cancelled'
                    # 计算退款（95%）
                    if conflict.payment_amount > 0:
                        conflict.refund_amount = conflict.payment_amount * Decimal('0.95')
                        conflict.payment_status = 'refunded'
                    conflict.save()
                    messages.warning(request, f'由于校内人员优先规则，已自动取消校外人员预约：{conflict.booking_code}')
        
        # 检查是否仍有冲突（校内人员之间或校外人员之间）
        remaining_conflicts = conflict_bookings.exclude(status='cancelled')
        if remaining_conflicts.exists():
            messages.error(request, '该时段已被预约，请选择其他时段！')
            student_advisors = user_info.advisors.all() if user_info.user_type == 'student' else []
            return render(request, 'user/booking_apply.html', {
                'user_info': user_info,
                'devices': devices,
                'student_advisors': student_advisors
            })
        
        # 学生用户必须填写指导教师，且必须在教师的学生列表中
        teacher = None
        if user_info.user_type == 'student':
            if not teacher_id:
                messages.error(request, '学生用户必须选择指导教师！')
                student_advisors = user_info.advisors.all()
                return render(request, 'user/booking_apply.html', {
                    'user_info': user_info,
                    'devices': devices,
                    'student_advisors': student_advisors
                })
            
            # 验证指导教师是否存在且是教师类型
            try:
                teacher = UserInfo.objects.get(user_code=teacher_id, user_type='teacher')
                # 验证学生是否在教师的学生列表中（通过多对多关系）
                if teacher not in user_info.advisors.all():
                    messages.error(request, f'您不在指导教师 {teacher.name} 的学生列表中，无法预约！请联系指导教师将您添加到学生列表中。')
                    student_advisors = user_info.advisors.all()
                    return render(request, 'user/booking_apply.html', {
                        'user_info': user_info,
                        'devices': devices,
                        'student_advisors': student_advisors
                    })
            except UserInfo.DoesNotExist:
                messages.error(request, f'指导教师编号 {teacher_id} 不存在或不是教师！')
                student_advisors = user_info.advisors.all()
                return render(request, 'user/booking_apply.html', {
                    'user_info': user_info,
                    'devices': devices,
                    'student_advisors': student_advisors
                })
        
        # 确定初始状态
        if user_info.user_type == 'student':
            initial_status = 'teacher_pending'  # 学生：待指导教师审批
        elif user_info.user_type == 'teacher':
            initial_status = 'pending'  # 教师：待管理员审批
        else:  # external
            initial_status = 'pending'  # 校外人员：待管理员审批
        
        # 计算缴费金额（校外人员）
        payment_amount = Decimal('0')
        if user_info.user_type == 'external':
            payment_amount = device.price_external
        
        # 生成预约编号
        booking_code = generate_booking_code()
        
        # 创建预约申请
        booking = Booking.objects.create(
            booking_code=booking_code,
            applicant=user_info,
            device=device,
            booking_date=booking_date,
            time_slot=time_slot,
            purpose=purpose,
            teacher=teacher,
            status=initial_status,
            payment_amount=payment_amount
        )
        
        if user_info.user_type == 'student':
            messages.success(request, f'预约申请提交成功！预约编号：{booking_code}，已提交给指导教师审批。')
        else:
            messages.success(request, f'预约申请提交成功！预约编号：{booking_code}，请等待审批。')
        return redirect('my_booking')
    
    # GET请求：渲染申请页面
    # 如果是学生，获取该学生的指导教师列表（用于下拉选择）
    student_advisors = []
    if user_info.user_type == 'student':
        student_advisors = user_info.advisors.all()
    
    context = {
        'user_info': user_info,
        'devices': devices,
        'student_advisors': student_advisors
    }
    return render(request, 'user/booking_apply.html', context)

# 2. 我的预约记录页面
@login_required
@csrf_protect
def my_booking(request):
    """我的预约记录页面"""
    # 获取当前用户信息
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
    except UserInfo.DoesNotExist:
        messages.error(request, '未找到你的个人信息，请联系管理员！')
        return redirect('user_home')
    
    # 状态筛选（全部/待审批/已批准/已拒绝/已撤销）
    status_filter = request.GET.get('status', 'all')
    bookings = Booking.objects.filter(applicant=user_info).order_by('-create_time')
    
    # 筛选状态
    if status_filter != 'all' and status_filter in [s[0] for s in Booking.APPROVAL_STATUS]:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'APPROVAL_STATUS': Booking.APPROVAL_STATUS
    }
    return render(request, 'user/my_booking.html', context)

# 3. 撤销预约申请
@login_required
def cancel_booking(request, booking_id):
    """撤销预约申请（支持已批准的预约，至少提前1天，付费预约退95%）"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # 校验是否是本人的预约
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
        if booking.applicant != user_info:
            messages.error(request, '你无权撤销他人的预约申请！')
            return redirect('my_booking')
    except UserInfo.DoesNotExist:
        messages.error(request, '未找到你的个人信息，请联系管理员！')
        return redirect('my_booking')
    
    # 不能撤销已撤销或已拒绝的申请
    if booking.status in ['cancelled', 'teacher_rejected', 'admin_rejected', 'manager_rejected']:
        messages.error(request, '该申请已撤销或已拒绝，无法再次撤销！')
        return redirect('my_booking')
    
    # 可以撤销的状态：待审批、已批准、待缴费等
    allowed_statuses = ['teacher_pending', 'pending', 'admin_approved', 'manager_approved', 'payment_pending']
    if booking.status not in allowed_statuses:
        messages.error(request, f'当前状态（{booking.get_status_display()}）不允许撤销！')
        return redirect('my_booking')
    
    # 验证撤销时间：至少提前1天
    today = date.today()
    if booking.booking_date <= today:
        messages.error(request, '预约日期已过或为今天，无法撤销！')
        return redirect('my_booking')
    
    days_until_booking = (booking.booking_date - today).days
    if days_until_booking < 1:
        messages.error(request, '撤销预约必须至少提前1天！')
        return redirect('my_booking')
    
    # 计算退款（校外人员付费预约）
    refund_amount = Decimal('0')
    if booking.applicant.user_type == 'external' and booking.payment_amount > 0:
        if booking.status == 'manager_approved' or booking.status == 'payment_pending':
            # 已批准或待缴费的付费预约，退95%
            refund_amount = booking.payment_amount * Decimal('0.95')
            booking.refund_amount = refund_amount
            booking.payment_status = 'refunded'
            messages.success(request, f'预约已撤销，将退还95%费用：{refund_amount}元（原费用：{booking.payment_amount}元）')
        else:
            # 未缴费的预约，无需退款
            messages.success(request, '预约已撤销（未缴费，无需退款）')
    else:
        # 校内人员或未付费的预约
        messages.success(request, '预约已成功撤销！')
    
    # 更新状态为已撤销
    booking.status = 'cancelled'
    booking.save()
    
    return redirect('my_booking')
@login_required
def device_booking_detail(request, device_id):
    """设备预约详情页面"""
    # 获取设备信息，不存在则返回404
    device = get_object_or_404(Device, id=device_id)
    # 查询该设备的所有预约记录（按预约时间倒序）
    bookings = Booking.objects.filter(device=device).order_by('-create_time')
    
    # 检查用户是否是管理员或负责人
    is_admin = request.user.groups.filter(name='设备管理员').exists()
    is_manager = request.user.groups.filter(name='实验室负责人').exists()
    can_view_booking_details = is_admin or is_manager
    
    context = {
        'device': device,
        'bookings': bookings,
        'can_view_booking_details': can_view_booking_details
    }
    return render(request, 'user/device_booking_detail.html', context)
@login_required
def check_availability(request):
    """检查设备在指定日期和时段是否空闲"""
    device_id = request.GET.get('device_id')
    booking_date_str = request.GET.get('date')
    time_slot = request.GET.get('time_slot')

    # 验证参数
    if not all([device_id, booking_date_str, time_slot]):
        return JsonResponse({
            'available': False,
            'reason': '参数不完整'
        })

    # 验证并转换日期格式
    try:
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({
            'available': False,
            'reason': '日期格式错误，应为YYYY-MM-DD'
        })

    # 检查设备是否存在（支持通过设备编号或设备ID查询）
    try:
        # 先尝试作为设备编号查询
        device = Device.objects.get(device_code=device_id)
    except Device.DoesNotExist:
        try:
            # 如果失败，尝试作为设备ID查询
            device = Device.objects.get(id=device_id)
        except (Device.DoesNotExist, ValueError):
            return JsonResponse({
                'available': False,
                'reason': '设备不存在'
            })

    # 检查设备状态：如果设备是"维修中"或"已报废"，所有时段都不可用
    if device.status in ['maintenance', 'discarded']:
        return JsonResponse({
            'available': False,
            'reason': f'设备状态为"{device.get_status_display()}"，所有时段都不可预约'
        })

    # 检查该时段是否已有预约（考虑校内人员优先规则）
    # 关键：只检查该具体日期和具体时段的预约，而不是整个日期
    existing_bookings = Booking.objects.filter(
        device=device,                  # 使用设备对象
        booking_date=booking_date,      # 使用转换后的日期对象
        time_slot=time_slot,            # 预约时段
        status__in=['teacher_pending', 'pending', 'admin_approved', 'manager_approved', 'payment_pending']  # 待审核或已通过的预约视为占用
    )
    
    # 获取请求用户信息（如果已登录）
    user_type = None
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
        user_type = user_info.user_type
    except (UserInfo.DoesNotExist, AttributeError):
        pass
    
    if existing_bookings.exists():
        # 如果新预约是校内人员，检查是否有校外人员预约（校内人员优先）
        if user_type in ['student', 'teacher']:
            external_conflicts = existing_bookings.filter(applicant__user_type='external')
            if external_conflicts.exists():
                return JsonResponse({
                    'available': True,  # 校内人员可以预约，会自动取消校外人员预约
                    'warning': '该时段有校外人员预约，根据校内人员优先规则，您的预约将自动生效'
                })
        
        # 其他情况：有冲突
        return JsonResponse({
            'available': False,
            'reason': '已有其他预约'
        })
    else:
        return JsonResponse({'available': True})

@login_required
def get_available_time_slots(request):
    """获取指定设备和日期的可用时段列表"""
    device_id = request.GET.get('device_id')
    booking_date_str = request.GET.get('date')
    
    # 验证参数
    if not device_id or not booking_date_str:
        return JsonResponse({
            'error': '参数不完整',
            'available_slots': []
        })
    
    # 验证并转换日期格式
    try:
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({
            'error': '日期格式错误，应为YYYY-MM-DD',
            'available_slots': []
        })
    
    # 检查设备是否存在（支持通过设备编号或设备ID查询）
    try:
        # 先尝试作为设备编号查询
        device = Device.objects.get(device_code=device_id)
    except Device.DoesNotExist:
        try:
            # 如果失败，尝试作为设备ID查询
            device = Device.objects.get(id=device_id)
        except (Device.DoesNotExist, ValueError):
            return JsonResponse({
                'error': '设备不存在',
                'available_slots': []
            })
    
    # 检查设备状态：如果设备是"维修中"或"已报废"，所有时段都不可用
    if device.status in ['maintenance', 'discarded']:
        return JsonResponse({
            'error': f'设备状态为"{device.get_status_display()}"，所有时段都不可预约',
            'available_slots': []
        })
    
    # 获取请求用户信息（如果已登录）
    user_type = None
    try:
        user_info = UserInfo.objects.get(auth_user=request.user)
        user_type = user_info.user_type
    except (UserInfo.DoesNotExist, AttributeError):
        pass
    
    # 所有可能的时段
    all_time_slots = [
        '08:00-10:00',
        '10:00-12:00',
        '12:00-14:00',
        '14:00-16:00',
        '16:00-18:00',
        '18:00-20:00',
    ]
    
    # 查询该日期已占用的时段（只查询该设备、该日期、有效状态的预约）
    # 注意：只查询该具体日期，不锁定其他日期
    existing_bookings = Booking.objects.filter(
        device=device,
        booking_date=booking_date,  # 使用转换后的日期对象
        status__in=['teacher_pending', 'pending', 'admin_approved', 'manager_approved', 'payment_pending']
    ).exclude(status='cancelled')  # 排除已撤销的预约
    
    # 过滤可用时段（考虑校内人员优先规则）
    # 关键：只锁定被占用的具体时段，而不是整个日期
    # 每个时段独立判断，互不影响
    available_slots = []
    for slot in all_time_slots:
        # 检查该时段是否被占用
        slot_bookings = existing_bookings.filter(time_slot=slot)
        
        if slot_bookings.exists():
            # 该时段已被占用，检查是否可以覆盖（校内人员优先规则）
            if user_type in ['student', 'teacher']:
                # 校内人员：检查是否有校外人员预约该时段
                external_conflicts = slot_bookings.filter(applicant__user_type='external')
                if external_conflicts.exists():
                    # 该时段被校外人员占用，校内人员可以覆盖
                    available_slots.append(slot)
                # else: 该时段被校内人员占用，不可用（不添加到可用列表）
            # else: 校外人员：如果时段已被占用，都不可用（不添加到可用列表）
        else:
            # 该时段未被占用，可用
            available_slots.append(slot)
    
    # 获取已占用的时段列表（用于调试显示）
    occupied_slots = list(set(existing_bookings.values_list('time_slot', flat=True)))
    
    return JsonResponse({
        'available_slots': available_slots,
        'occupied_slots': occupied_slots
    })