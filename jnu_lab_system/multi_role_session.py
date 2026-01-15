"""
多角色会话管理模块
支持在同一浏览器中同时登录多个不同角色的账户
通过使用不同的session key前缀来区分不同角色
"""
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user
from django.contrib.auth import get_user_model


# 角色到session key前缀的映射
ROLE_SESSION_PREFIXES = {
    'user': 'multi_role_user_id_user',
    'admin': 'multi_role_user_id_admin',
    'manager': 'multi_role_user_id_manager',
}

def get_role_from_path(path):
    """从URL路径判断角色"""
    if path.startswith('/labadmin/'):
        return 'admin'
    elif path.startswith('/manager/'):
        return 'manager'
    elif path.startswith('/user/'):
        return 'user'
    return None

def get_user_from_role_session(request, role=None):
    """从角色特定的session中获取用户"""
    if role is None:
        role = get_role_from_path(request.path)
    
    if not role or role not in ROLE_SESSION_PREFIXES:
        return None
    
    # 尝试从角色特定的session中获取用户ID
    role_session_key = ROLE_SESSION_PREFIXES[role]
    user_id = request.session.get(role_session_key)
    
    if user_id:
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
            # 设置backend，确保用户可以被正确认证
            backend_key = f"{role_session_key}_backend"
            backend = request.session.get(backend_key, 'django.contrib.auth.backends.ModelBackend')
            user.backend = backend
            # 标记用户为已认证（模拟Django的认证系统）
            user._state.adding = False
            return user
        except User.DoesNotExist:
            return None
    
    return None

def set_role_session_user(request, user, role=None):
    """在角色特定的session中设置用户"""
    if role is None:
        role = get_role_from_path(request.path)
    
    if not role or role not in ROLE_SESSION_PREFIXES:
        return False
    
    # 在session中存储角色特定的用户ID和backend
    role_session_key = ROLE_SESSION_PREFIXES[role]
    role_backend_key = f"{role_session_key}_backend"
    
    request.session[role_session_key] = user.id
    # 设置backend，确保用户可以被正确认证
    backend = getattr(user, 'backend', None) or 'django.contrib.auth.backends.ModelBackend'
    request.session[role_backend_key] = backend
    
    # 同时存储用户名，用于验证
    request.session[f"{role_session_key}_username"] = user.username
    
    request.session.save()
    return True

def clear_role_session(request, role=None):
    """清除角色特定的session"""
    if role is None:
        role = get_role_from_path(request.path)
    
    if not role or role not in ROLE_SESSION_PREFIXES:
        return False
    
    prefix = ROLE_SESSION_PREFIXES[role]
    keys_to_remove = [key for key in request.session.keys() if key.startswith(prefix)]
    for key in keys_to_remove:
        del request.session[key]
    request.session.save()
    return True
