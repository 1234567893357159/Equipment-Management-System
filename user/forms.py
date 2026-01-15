from django import forms
from django.contrib.auth.hashers import make_password
from .models import UserInfo

class UserInfoForm(forms.ModelForm):
    """用户信息新增/编辑表单"""
    # 【新增】密码重置字段（可选，编辑时显示）
    reset_password = forms.CharField(
        max_length=50, 
        required=False, 
        label='重置密码（留空则不修改）',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserInfo
        fields = ['user_code', 'name', 'user_type', 'department', 'phone', 'is_active']
        labels = {
            'is_active': '借用资格（勾选=正常，取消=禁用）',
        }
        widgets = {
            'user_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user_info = super().save(commit=False)
        
        # 如果填写了重置密码，更新登录账号的密码
        reset_pwd = self.cleaned_data.get('reset_password')
        if reset_pwd and user_info.auth_user:
            user_info.auth_user.password = make_password(reset_pwd)
            user_info.auth_user.save()
        
        if commit:
            user_info.save()
        return user_info
    
# 用户注册功能

class RegistrationForm(forms.ModelForm):
    """用户注册表单"""
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='密码',
        required=True
    )
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='确认密码',
        required=True
    )
    
    class Meta:
        model = UserInfo
        fields = ['user_code', 'name', 'gender', 'user_type', 'department', 'phone']
        labels = {
            'user_code': '用户编号/学号/工号',
            'name': '姓名',
            'gender': '性别',
            'user_type': '用户类型',
            'department': '所在学院/单位',
            'phone': '联系电话',
        }
        widgets = {
            'user_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """表单验证"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        user_code = cleaned_data.get('user_code')
        user_type = cleaned_data.get('user_type')
        
        # 验证密码一致性
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('两次输入的密码不一致！')
        
        # 验证用户编号唯一性
        if user_code and UserInfo.objects.filter(user_code=user_code).exists():
            raise forms.ValidationError('该用户编号已被注册！')
        
        
        return cleaned_data

# 教师维护学生列表
class StudentForm(forms.ModelForm):
    """学生信息表单（用于教师添加/编辑学生）"""
    class Meta:
        model = UserInfo
        fields = ['user_code', 'name', 'gender', 'department', 'phone', 'major', 'advisor']
        labels = {
            'user_code': '学号',
            'name': '姓名',
            'gender': '性别',
            'department': '所在学院',
            'phone': '联系电话',
            'major': '专业',
            'advisor': '指导教师',
        }
        widgets = {
            'user_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'advisor': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
    
    def __init__(self, *args, **kwargs):
        # 获取教师姓名并设置到表单中
        teacher_name = kwargs.pop('teacher_name', None)
        super().__init__(*args, **kwargs)
        
        if teacher_name:
            # 设置指导教师字段为教师姓名，并设为只读
            self.fields['advisor'].initial = teacher_name
        
        # 如果是编辑模式（有实例且已保存），将学号字段设为只读
        if self.instance and self.instance.pk:
            self.fields['user_code'].widget.attrs['readonly'] = True
            self.fields['user_code'].widget.attrs['class'] = 'form-control readonly'
    
    def clean_user_code(self):
        """验证学号"""
        user_code = self.cleaned_data.get('user_code')
        
        # 如果是编辑模式（有实例且已保存）
        if self.instance and self.instance.pk:
            # 检查提交的学号是否与实例的学号一致
            if user_code != self.instance.user_code:
                raise forms.ValidationError('不能修改学号！')
        else:
            # 新增模式：检查学号是否已存在
            if UserInfo.objects.filter(user_code=user_code).exists():
                raise forms.ValidationError('该学号已被注册！')
        
        return user_code
    
# 添加学号检查表单
class StudentIdForm(forms.Form):
    """第一步：学号检查表单"""
    user_code = forms.CharField(
        max_length=20,
        label='学号',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='请输入学生的学号'
    )
    
    def clean_user_code(self):
        """验证学号"""
        user_code = self.cleaned_data.get('user_code')
        # 检查学号格式（可选）
        if not user_code:
            raise forms.ValidationError('请输入学号！')
        return user_code