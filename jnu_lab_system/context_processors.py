"""Django context processors - 为所有模板提供全局上下文"""
from user.models import UserInfo
from jnu_lab_system.multi_role_session import get_role_from_path, get_user_from_role_session

def user_info_context(request):
    """为所有模板提供当前用户的UserInfo信息"""
    context = {}
    
    # 多角色支持：如果使用了角色特定的session，从那里获取用户
    role = get_role_from_path(request.path)
    current_user = request.user
    
    # 如果路径匹配某个角色，尝试从角色特定的session中获取用户
    if role:
        role_user = get_user_from_role_session(request, role)
        if role_user:
            current_user = role_user
    
    if current_user.is_authenticated:
        try:
            user_info = UserInfo.objects.get(auth_user=current_user)
            context['current_user_info'] = user_info
            # 严格检查用户类型，确保不会混淆
            context['is_teacher'] = (user_info.user_type == 'teacher')
            context['is_student'] = (user_info.user_type == 'student')
            context['is_external'] = (user_info.user_type == 'external')
            # 确保三个类型互斥
            if not (context['is_teacher'] or context['is_student'] or context['is_external']):
                # 如果用户类型不是这三种之一，全部设为False
                context['is_teacher'] = False
                context['is_student'] = False
                context['is_external'] = False
        except UserInfo.DoesNotExist:
            context['current_user_info'] = None
            context['is_teacher'] = False
            context['is_student'] = False
            context['is_external'] = False
    else:
        context['current_user_info'] = None
        context['is_teacher'] = False
        context['is_student'] = False
        context['is_external'] = False
    return context
