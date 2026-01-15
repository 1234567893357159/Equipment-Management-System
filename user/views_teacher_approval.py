"""教师审批学生预约申请的视图"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.db.models import Q
from user.models import UserInfo
from booking.models import Booking, ApprovalRecord

@login_required
@csrf_protect
def teacher_booking_approve(request):
    """教师审批学生预约申请"""
    # 获取当前教师信息
    try:
        teacher_info = UserInfo.objects.get(auth_user=request.user)
        # 严格检查：必须是教师类型
        if teacher_info.user_type != 'teacher':
            messages.error(request, '只有教师可以审批学生预约申请！')
            # 根据用户类型重定向到正确的首页，避免循环跳转
            if teacher_info.user_type == 'student':
                return redirect('user_home')
            elif teacher_info.user_type == 'external':
                return redirect('user_home')
            else:
                return redirect('user_home')
    except UserInfo.DoesNotExist:
        messages.error(request, '未找到你的个人信息，请联系管理员！')
        return redirect('user_home')
    
    # 获取待审批的学生预约
    # 关键：只显示指定当前教师为指导教师的预约申请（通过booking.teacher字段判断）
    # 这样确保同一个预约只出现在一个教师的审批列表中
    bookings = Booking.objects.filter(
        status='teacher_pending',
        teacher=teacher_info  # 预约申请中的指导教师必须是当前教师
    ).order_by('-create_time')
    
    # 处理审批操作
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')  # 'approve' 或 'reject'
        
        if booking_id and action:
            booking = get_object_or_404(
                Booking, 
                id=booking_id
            )
            # 验证预约申请中的指导教师是否是当前教师
            if booking.teacher != teacher_info:
                messages.error(request, '您无权审批该预约申请！该预约申请指定的指导教师不是您。')
                return redirect('teacher_booking_approve')
            
            if action == 'approve':
                # 教师批准：状态变为待管理员审批
                booking.status = 'pending'
                booking.save()
                
                # 记录审批日志
                ApprovalRecord.objects.create(
                    booking=booking,
                    approver=request.user,
                    approval_level='teacher',
                    action='approve',
                    comment=request.POST.get('comment', '')
                )
                
                messages.success(request, f'已批准学生 {booking.applicant.name} 的预约申请：{booking.booking_code}')
            elif action == 'reject':
                # 教师拒绝
                booking.status = 'teacher_rejected'
                booking.save()
                
                # 记录审批日志
                ApprovalRecord.objects.create(
                    booking=booking,
                    approver=request.user,
                    approval_level='teacher',
                    action='reject',
                    comment=request.POST.get('comment', '')
                )
                
                messages.success(request, f'已拒绝学生 {booking.applicant.name} 的预约申请：{booking.booking_code}')
            
            return redirect('teacher_booking_approve')
    
    context = {
        'bookings': bookings,
        'teacher_info': teacher_info
    }
    return render(request, 'user/teacher_booking_approve.html', context)
