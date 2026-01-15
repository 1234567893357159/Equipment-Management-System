"""教师查看自己指导的学生预约申请的视图"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from user.models import UserInfo
from booking.models import Booking

@login_required
def teacher_all_student_bookings(request):
    """教师查看指定自己为指导教师的学生的预约申请"""
    # 获取当前教师信息
    try:
        teacher_info = UserInfo.objects.get(auth_user=request.user)
        # 严格检查：必须是教师类型
        if teacher_info.user_type != 'teacher':
            messages.error(request, '只有教师可以查看学生预约申请！')
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
    
    # 只查询该学生申请的指导教师是当前教师的预约申请
    # 关键：通过 booking.teacher 字段来判断，而不是通过学生列表
    bookings = Booking.objects.filter(
        applicant__user_type='student',
        teacher=teacher_info  # 预约申请中的指导教师必须是当前教师
    ).order_by('-create_time')
    
    # 筛选条件
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    student_name = request.GET.get('student_name', '')
    if student_name:
        bookings = bookings.filter(applicant__name__icontains=student_name)
    
    student_code = request.GET.get('student_code', '')
    if student_code:
        bookings = bookings.filter(applicant__user_code__icontains=student_code)
    
    student_major = request.GET.get('student_major', '')
    if student_major:
        bookings = bookings.filter(applicant__major__icontains=student_major)
    
    # 获取该教师指导的所有学生的ID列表（用于模板中标记）
    my_student_ids = teacher_info.students.values_list('id', flat=True)
    
    context = {
        'bookings': bookings,
        'teacher_info': teacher_info,
        'my_student_ids': list(my_student_ids),
        'status_filter': status_filter,
        'student_name': student_name,
        'student_code': student_code,
        'student_major': student_major,
    }
    return render(request, 'user/teacher_all_student_bookings.html', context)
