from django.db import models
from django.contrib.auth.models import User  # 导入内置User模型

class UserInfo(models.Model):
    """系统用户信息模型（包含学生、教师、校外人员）"""
    # 用户类型枚举（固定选项）
    USER_TYPE_CHOICES = (
        ('student', '校内学生'),
        ('teacher', '校内教师'),
        ('external', '校外人员'),
    )
    
    # 核心字段
    user_code = models.CharField(
        max_length=20, 
        verbose_name='用户编号/学号/工号',
        unique=True,  # 编号唯一，避免重复
        help_text='学生填学号，教师填工号，校外人员填自定义编号（如O开头）'
    )
    name = models.CharField(max_length=50, verbose_name='姓名')
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        verbose_name='用户类型'
    )
    department = models.CharField(max_length=100, verbose_name='所在学院/单位')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    gender = models.CharField(max_length=2, choices=[('男', '男'), ('女', '女')], default='男', verbose_name='性别')
    
    # 学生专属字段
    major = models.CharField(max_length=50, blank=True, null=True, verbose_name='专业')
    # 指导教师改为多对多关系，支持多个指导教师
    advisors = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        limit_choices_to={'user_type': 'teacher'},
        related_name='students',
        verbose_name='指导教师'
    )
    
    # 教师专属字段
    title = models.CharField(max_length=20, blank=True, null=True, verbose_name='职称')
    research_field = models.CharField(max_length=100, blank=True, null=True, verbose_name='研究方向')
    
    # 校外人员专属字段
    position = models.CharField(max_length=50, blank=True, null=True, verbose_name='职务')
    company_address = models.CharField(max_length=200, blank=True, null=True, verbose_name='单位地址')
    
    is_active = models.BooleanField(default=True, verbose_name='借用资格（正常/禁用）')
    # 注册审核状态（教师和管理员需要审核）
    APPROVAL_STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='approved',  # 学生默认已通过，教师和管理员默认待审核
        verbose_name='注册审核状态'
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 【关键新增】一对一关联Django内置User模型（登录账号）
    auth_user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # 删除UserInfo时，自动删除关联的User
        null=True, 
        blank=True, 
        verbose_name='关联登录账号'
    )

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return f'{self.name}（{self.get_user_type_display()}）'