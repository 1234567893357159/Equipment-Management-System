"""
多角色会话中间件
支持在同一浏览器中同时登录多个不同角色的账户
根据URL路径自动切换到对应角色的用户身份
"""
from django.contrib.auth import get_user
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from jnu_lab_system.multi_role_session import get_user_from_role_session, get_role_from_path


class MultiRoleSessionMiddleware:
    """
    多角色会话中间件
    根据URL路径自动切换到对应角色的用户身份
    这样可以在同一浏览器中同时保持多个角色的登录状态
    
    注意：此中间件必须在AuthenticationMiddleware之后运行
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 从URL路径判断当前请求应该使用哪个角色
        role = get_role_from_path(request.path)
        
        # 如果路径匹配某个角色，尝试从角色特定的session中获取用户
        if role:
            role_user = get_user_from_role_session(request, role)
            if role_user:
                # 直接替换request.user为角色特定的用户
                # 这样@login_required装饰器就能正确识别
                # 注意：这发生在AuthenticationMiddleware之后，所以可以安全替换
                request.user = role_user
                request._using_role_session = True
                request._current_role = role
            else:
                # 如果没有找到角色特定的用户，保持原有的request.user（可能是标准登录）
                request._using_role_session = False
                request._current_role = role
        else:
            request._using_role_session = False
            request._current_role = None
        
        response = self.get_response(request)
        return response
