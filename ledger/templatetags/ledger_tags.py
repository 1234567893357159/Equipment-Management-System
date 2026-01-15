from django import template

register = template.Library()

@register.filter
def extract_device_code(description):
    """从删除设备的描述中提取设备编号"""
    if not description:
        return ''
    if '删除设备：' in description:
        parts = description.split('删除设备：')
        if len(parts) > 1:
            last_part = parts[1]
            subparts = last_part.split(' - ')
            if subparts:
                return subparts[0]
    return ''

@register.filter
def get_item(dictionary, key):
    """从字典中获取值"""
    if dictionary is None:
        return None
    return dictionary.get(key)