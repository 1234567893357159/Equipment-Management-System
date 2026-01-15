"""访问控制中间件：工作人员只能在局域网访问"""
from django.http import HttpResponseForbidden
from django.contrib.auth.models import Group
from ipaddress import ip_address, ip_network

# 局域网IP段（根据实际网络配置修改）
LAN_NETWORKS = [
    ip_network('192.168.0.0/16'),  # 192.168.x.x
    ip_network('10.0.0.0/8'),      # 10.x.x.x
    ip_network('172.16.0.0/12'),   # 172.16.x.x - 172.31.x.x
    ip_network('127.0.0.0/8'),     # localhost
]

def is_lan_ip(ip_str):
    """检查IP地址是否在局域网内"""
    try:
        ip = ip_address(ip_str)
        return any(ip in network for network in LAN_NETWORKS)
    except ValueError:
        return False

def get_client_ip(request):
    """获取客户端真实IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class StaffAccessControlMiddleware:
    """工作人员访问控制中间件"""
    
    # 访问控制开关：True=启用IP限制，False=允许所有访问（保留功能但暂时禁用）
    ENABLE_IP_RESTRICTION = False  # 暂时禁用，允许所有人访问
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 如果禁用了IP限制，直接允许访问
        if not self.ENABLE_IP_RESTRICTION:
            response = self.get_response(request)
            return response
        
        # 检查用户是否是工作人员（管理员或负责人）
        if request.user.is_authenticated:
            is_admin = request.user.groups.filter(name='设备管理员').exists()
            is_manager = request.user.groups.filter(name='实验室负责人').exists()
            
            if is_admin or is_manager:
                # 工作人员只能从局域网访问
                client_ip = get_client_ip(request)
                if not is_lan_ip(client_ip):
                    # 不在局域网内，拒绝访问
                    return HttpResponseForbidden(
                        '<h1>访问被拒绝</h1>'
                        '<p>实验室工作人员（设备管理员、实验室负责人）只能在局域网内访问系统。</p>'
                        '<p>您的IP地址：' + client_ip + '</p>'
                        '<p>请联系系统管理员获取访问权限。</p>'
                    )
        
        response = self.get_response(request)
        return response
