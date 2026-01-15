# manager/admin.py
from django.contrib import admin
from .models import  UserInfo  # 导入UserInfo模型（同时保留之前的Device）


# ---------------------- 用户信息模型注册（新增） ----------------------
@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    # 列表页显示的核心字段（优先展示关键信息）
    list_display = [
        'user_code', 'name', 'user_type', 'get_user_type_display',  # 显示用户类型的中文名称
        'department', 'phone', 'is_active', 'create_time'
    ]
    
    # 支持搜索的字段（按编号、姓名、单位搜索）
    search_fields = ['user_code', 'name', 'department', 'phone']
    
    # 右侧筛选栏（按用户类型、是否启用筛选）
    list_filter = ['user_type', 'is_active']
    
    # 排序方式（按创建时间倒序，最新的用户在最前面）
    ordering = ['-create_time']
    
    # 只读字段（系统自动生成的时间字段）
    readonly_fields = ['create_time', 'update_time']
    
    # 编辑页字段分组（按用户类型拆分，隐藏无关字段）
    fieldsets = (
        ('基础信息（所有用户必填）', {
            'fields': ('user_code', 'name', 'user_type', 'department', 'phone', 'gender', 'is_active')
        }),
        ('学生专属信息（仅学生填写）', {
            'fields': ('major', 'advisors'),
            'classes': ('collapse',)  # 可折叠，默认收起
        }),
        ('教师专属信息（仅教师填写）', {
            'fields': ('title', 'research_field'),
            'classes': ('collapse',)
        }),
        ('校外人员专属信息（仅校外人员填写）', {
            'fields': ('position', 'company_address'),
            'classes': ('collapse',)
        }),
        ('账号关联（系统内部）', {
            'fields': ('auth_user',),
            'classes': ('collapse',)
        }),
        ('系统记录', {
            'fields': ('create_time', 'update_time'),
            'classes': ('collapse',)
        }),
    )
    
    # 可选：自定义列表页显示的用户类型中文名称（增强可读性）
    def get_user_type_display(self, obj):
        return obj.get_user_type_display()
    get_user_type_display.short_description = '用户类型（中文）'