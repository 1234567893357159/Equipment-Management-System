from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

# 设备状态枚举（设备物理状态，不包含时段占用情况）
DEVICE_STATUS = (
    ('available', '正常'),
    ('maintenance', '维修中'),
    ('discarded', '已报废'),
)

class Device(models.Model):
    """实验室设备模型（适配现有页面字段）"""
    # 核心字段（与你的页面一一对应）
    device_code = models.CharField(max_length=50, verbose_name='设备编号', unique=True)  # 例如 DEV001
    model = models.CharField(max_length=100, verbose_name='型号')  # 型号A-100
    manufacturer = models.CharField(max_length=100, verbose_name='生产厂商', default='未知厂商')  # 已加默认值
    purchase_date = models.DateField(verbose_name='购入时间', null=True, blank=True)  # 可选：加空值支持
    purpose = models.CharField(max_length=200, verbose_name='实验用途', null=True, blank=True, default='未知用途')  # 可选：加空值支持
    status = models.CharField(max_length=20, choices=DEVICE_STATUS, default='available', verbose_name='设备状态', help_text='设备物理状态：正常/维修中/已报废。时段可用性由预约情况决定。')
    # 关键修改：给价格字段加默认值（Decimal类型默认值用数字）
    price_internal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='校内租用价格（元/2小时）', default=Decimal('0'))
    price_external = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='校外租用价格（元/2小时）', default=Decimal('0'))

    # 时间戳（自动生成，无需页面输入）
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '设备'
        verbose_name_plural = '设备管理'
        ordering = ['device_code']  # 按设备编号排序

    def __str__(self):
        return f"{self.device_code} - {self.model}"

    def save(self, *args, **kwargs):
        """重写save方法，自动记录设备操作"""
        from ledger.models import DeviceLedger

        is_new = self.pk is None
        old_status = None

        if not is_new:
            try:
                old_device = Device.objects.get(pk=self.pk)
                old_status = old_device.status
            except Device.DoesNotExist:
                pass

        # 调用父类save方法
        super().save(*args, **kwargs)

        # 获取当前用户（如果有的话）
        User = get_user_model()
        current_user = None
        try:
            # 这里可以根据实际情况获取当前操作用户
            # 暂时使用系统用户或第一个管理员用户
            current_user = User.objects.filter(is_staff=True).first()
        except:
            pass

        # 记录操作到台账
        if is_new:
            # 新增设备
            DeviceLedger.objects.create(
                device=self,
                device_name=self.model,
                operation_type='other',
                operation_date=timezone.now(),
                status_after_operation=self.status,
                description=f'新增设备：{self.device_code} - {self.model}',
                operator=current_user
            )
        elif old_status and old_status != self.status:
            # 状态变更（记录所有状态变更，除了unavailable，因为已移除）
            DeviceLedger.objects.create(
                device=self,
                device_name=self.model,
                operation_type='other',
                operation_date=timezone.now(),
                status_after_operation=self.status,
                description=f'设备状态变更：{old_status} → {self.status}',
                operator=current_user
            )

    def delete(self, *args, **kwargs):
        """重写delete方法，记录设备删除操作"""
        from ledger.models import DeviceLedger

        # 获取当前用户
        User = get_user_model()
        current_user = None
        try:
            current_user = User.objects.filter(is_staff=True).first()
        except:
            pass

        # 先记录删除操作，再删除设备
        DeviceLedger.objects.create(
            device=self,
            device_name=self.model,
            operation_type='discard',
            operation_date=timezone.now(),
            status_after_operation='discarded',
            description=f'删除设备：{self.device_code} - {self.model}',
            operator=current_user,
            user=None  # 删除操作没有特定用户
        )

        # 调用父类delete方法
        super().delete(*args, **kwargs)