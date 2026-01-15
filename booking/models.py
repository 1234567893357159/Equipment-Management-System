from django.db import models
from django.contrib.auth.models import User
from user.models import UserInfo

from devices.models import Device

# 预约申请模型
class Booking(models.Model):
    # 审批状态（适配多级审批）
    APPROVAL_STATUS = (
        ('teacher_pending', '待指导教师审批'),  # 学生预约：待指导教师审批
        ('pending', '待管理员审批'),  # 教师预约：待管理员审批；学生预约：指导教师已批准，待管理员审批
        ('admin_approved', '管理员已批准（待负责人审批）'),  # 校外人员：待负责人审批
        ('manager_approved', '全部审批通过'),
        ('payment_pending', '待缴费'),  # 校外人员：负责人已批准，待缴费
        ('teacher_rejected', '指导教师已拒绝'),
        ('admin_rejected', '管理员已拒绝'),
        ('manager_rejected', '负责人已拒绝'),
        ('cancelled', '用户已撤销'),
    )
    
    booking_code = models.CharField(max_length=20, unique=True, verbose_name='预约编号')
    applicant = models.ForeignKey(UserInfo, on_delete=models.CASCADE, verbose_name='申请人')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name='预约设备')
    booking_date = models.DateField(verbose_name='预约日期')
    time_slot = models.CharField(max_length=20, verbose_name='预约时段')
    purpose = models.TextField(verbose_name='借用用途', blank=True, null=True)
    teacher = models.ForeignKey(UserInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_bookings', verbose_name='指导教师')
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending', verbose_name='审批状态')
    payment_status = models.CharField(max_length=20, choices=[('unpaid', '未缴费'), ('paid', '已缴费'), ('refunded', '已退款')], default='unpaid', verbose_name='缴费状态')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='缴费金额')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='退款金额')
    finance_confirmed = models.BooleanField(default=False, verbose_name='财务处确认')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return f"{self.booking_code} - {self.applicant.name} - {self.device.model}"

    class Meta:
        verbose_name = '预约申请'
        verbose_name_plural = '预约申请'

# 审批记录模型（记录每一步审批操作）
class ApprovalRecord(models.Model):
    APPROVAL_ACTION = (
        ('approve', '批准'),
        ('reject', '拒绝'),
    )
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, verbose_name='关联预约')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='审批人')
    approval_level = models.CharField(max_length=20, choices=[('teacher', '指导教师'), ('admin', '管理员'), ('manager', '负责人')], verbose_name='审批级别')
    action = models.CharField(max_length=10, choices=APPROVAL_ACTION, verbose_name='审批操作')
    comment = models.TextField(blank=True, null=True, verbose_name='审批备注')
    approval_time = models.DateTimeField(auto_now_add=True, verbose_name='审批时间')

    class Meta:
        verbose_name = '审批记录'
        verbose_name_plural = '审批记录'