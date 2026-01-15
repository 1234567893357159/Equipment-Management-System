# 假设模型在 booking app 下，路径为 booking/admin.py
from django.contrib import admin
from .models import Booking, ApprovalRecord  # 导入你的两个模型

# -------------------------- 审批记录 内联显示配置 --------------------------
# 让审批记录可以在预约申请页面直接查看/编辑（更友好）
class ApprovalRecordInline(admin.TabularInline):
    model = ApprovalRecord
    extra = 0  # 默认不显示额外的空白表单
    readonly_fields = ('approval_time',)  # 审批时间设为只读
    fields = ('approver', 'approval_level', 'action', 'comment', 'approval_time')  # 显示的字段

# -------------------------- 预约申请 Admin 配置 --------------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # 列表页显示的字段
    list_display = (
        'booking_code', 'applicant', 'device', 'booking_date', 
        'time_slot', 'status', 'create_time'
    )
    # 支持搜索的字段
    search_fields = ('booking_code', 'applicant__name', 'device__device_name', 'purpose')
    # 支持筛选的字段
    list_filter = ('status', 'booking_date', 'applicant__user_type')
    # 只读字段（自动生成/不允许手动修改的）
    readonly_fields = ('create_time', 'update_time')
    # 详情页分组显示字段
    fieldsets = (
        ('基础信息', {
            'fields': ('booking_code', 'applicant', 'device', 'booking_date', 'time_slot')
        }),
        ('申请信息', {
            'fields': ('purpose', 'teacher')
        }),
        ('审批状态', {
            'fields': ('status', 'create_time', 'update_time')
        }),
    )
    # 内联显示审批记录（在预约申请详情页直接看审批记录）
    inlines = [ApprovalRecordInline]

# -------------------------- 审批记录 Admin 配置 --------------------------
@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    # 列表页显示的字段
    list_display = ('booking', 'approver', 'approval_level', 'action', 'approval_time')
    # 支持搜索的字段
    search_fields = ('booking__booking_code', 'approver__username', 'comment')
    # 支持筛选的字段
    list_filter = ('approval_level', 'action', 'approval_time')
    # 只读字段
    readonly_fields = ('approval_time',)
    # 详情页显示的字段
    fields = ('booking', 'approver', 'approval_level', 'action', 'comment', 'approval_time')

# 如果你的模型不在 booking app 下，只需把导入路径改成正确的即可，比如：
# from devices.models import Booking, ApprovalRecord