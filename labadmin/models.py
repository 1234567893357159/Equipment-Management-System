from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.serializers.json import DjangoJSONEncoder # 新增导入
import json

class Report(models.Model):
    """报表模型：存储生成的周报表、月报表、年报表"""
    REPORT_TYPE_CHOICES = (
        ('week', '周报表'),
        ('month', '月报表'),
        ('year', '年报表'),
        ('custom', '自定义时间段报表'),
    )
    
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, verbose_name='报表类型')
    report_name = models.CharField(max_length=200, verbose_name='报表名称')
    start_date = models.DateField(verbose_name='统计开始日期')
    end_date = models.DateField(verbose_name='统计结束日期')
    
    # 报表数据（JSON格式存储）
    report_data = models.JSONField(verbose_name='报表数据', default=dict)
    
    # 统计信息
    total_bookings = models.IntegerField(default=0, verbose_name='总预约次数')
    total_devices = models.IntegerField(default=0, verbose_name='设备总数')
    total_users = models.IntegerField(default=0, verbose_name='用户总数')
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='总收入（元）')
    
    # 生成信息
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='生成人')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    
    # 文件路径（如果导出为文件）
    file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name='文件路径')
    
    class Meta:
        verbose_name = '报表'
        verbose_name_plural = '报表管理'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'start_date', 'end_date']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_name} ({self.start_date} 至 {self.end_date})"
    
    def is_expired(self):
        """检查报表是否已过期（超过一个月）"""
        return timezone.now() - self.generated_at > timedelta(days=30)
    
    def get_report_data(self):
        """获取报表数据（JSON格式）"""
        if isinstance(self.report_data, str):
            return json.loads(self.report_data)
        return self.report_data or {}
    
    def set_report_data(self, data):
        """设置报表数据"""
        self.report_data = data
