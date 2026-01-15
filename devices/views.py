from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages  # 新增：用于提示操作结果
from .models import Device
from .forms import DeviceForm
from ledger.models import DeviceLedger
from django.utils import timezone

def get_user_role_context(request):
    """辅助函数：获取用户角色信息"""
    is_admin = request.user.groups.filter(name='设备管理员').exists()
    is_manager = request.user.groups.filter(name='实验室负责人').exists()
    return {
        'is_admin': is_admin,
        'is_manager': is_manager,
    }

def device_manage(request):
    """
    设备管理主视图（一体化：列表、新增、编辑、搜索、状态修改）
    对应路径：/labadmin/device/manage/
    """
    # 1. 处理搜索逻辑（GET 请求，keyword 参数）
    keyword = request.GET.get('keyword', '')
    if keyword:
        # 按设备编号/型号/厂商模糊搜索（增强搜索体验）
        devices = Device.objects.filter(
            Q(device_code__icontains=keyword) | 
            Q(model__icontains=keyword) |
            Q(manufacturer__icontains=keyword)
        )
    else:
        # 无搜索时显示所有设备，按编号排序
        devices = Device.objects.all().order_by('device_code')

    # 初始化编辑状态标识
    edit_device_id = None

    # 2. 处理新增/编辑设备逻辑（POST 请求）
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        if device_id:
            # 编辑现有设备
            device = get_object_or_404(Device, id=device_id)
            form = DeviceForm(request.POST, instance=device)
            edit_device_id = device_id
            success_msg = f"设备【{device.device_code}】编辑成功！"
        else:
            # 新增设备
            form = DeviceForm(request.POST)
            success_msg = "设备新增成功！"
        
        if form.is_valid():
            form.save()
            messages.success(request, success_msg)  # 新增操作提示
            return redirect('device_manage')  # 保存后返回列表顶部
        else:
            # 表单验证失败时提示错误
            messages.error(request, "表单填写有误，请检查后重新提交！")

    # 3. 处理状态修改逻辑（GET 请求，status_action 和 pk 参数）
    status_action = request.GET.get('status_action')
    pk = request.GET.get('pk')
    if status_action and pk:
        device = get_object_or_404(Device, pk=pk)
        if status_action == 'available':
            # 如果是从不可用改为可用，创建归还记录
            if device.status == 'unavailable':
                create_return_ledger(device, request.user)
            device.status = 'available'
            msg = f"设备【{device.device_code}】已标记为可用！"
        elif status_action == 'unavailable':
            device.status = 'unavailable'
            msg = f"设备【{device.device_code}】已标记为不可用！"
        device.save()
        messages.success(request, msg)
        return redirect('device_manage')

    # 4. 准备表单和上下文数据（编辑时自动填充表单）
    # 如果是编辑状态，初始化表单为对应设备数据
    if edit_device_id:
        device = get_object_or_404(Device, id=edit_device_id)
        form = DeviceForm(instance=device)
    else:
        form = DeviceForm()  # 空表单用于新增

    context = {
        'devices': devices,
        'keyword': keyword,
        'form': form,
        'edit_device_id_js': edit_device_id,  # 传给模板标识编辑状态
    }
    context.update(get_user_role_context(request))
    return render(request, 'admin/device_manage.html', context)

def device_delete(request, pk):
    """
    设备删除视图（独立视图，处理删除请求）
    对应路径：/labadmin/device/delete/<int:pk>/
    """
    # 获取要删除的设备，不存在则返回404
    device = get_object_or_404(Device, pk=pk)
    device_code = device.device_code  # 保存设备编号用于提示
    
    # 执行删除操作（仅处理GET请求，适配模板中的删除链接）
    device.delete()
    messages.success(request, f"设备【{device_code}】已成功删除！")
    
    # 删除后返回设备管理列表页
    return redirect('device_manage')

def device_detail(request, pk):
    """
    设备详情/编辑页
    pk: 设备ID
    功能：1. 展示设备详情 2. 处理设备编辑提交
    """
    # 获取当前设备数据，不存在则返回404
    device = get_object_or_404(Device, pk=pk)

    # 处理编辑提交逻辑（POST 请求）
    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            # 编辑成功后，跳回设备管理页
            return redirect('device_manage')
    else:
        # GET 请求：初始化表单，填充当前设备数据
        form = DeviceForm(instance=device)

    # 准备上下文
    context = {
        'device': device,
        'form': form,
    }
    context.update(get_user_role_context(request))

    # 渲染设备详情/编辑模板
    return render(request, 'admin/device_detail.html', context)

def create_return_ledger(device, operator):
    """创建设备归还台账记录"""
    try:
        # 查找最近的借出记录（未归还的）
        borrow_ledger = DeviceLedger.objects.filter(
            device=device,
            operation_type='borrow',
            actual_return_date__isnull=True
        ).order_by('-operation_date').first()
        
        if borrow_ledger:
            # 创建归还记录
            DeviceLedger.objects.create(
                device=device,
                device_name=device.model,
                user=borrow_ledger.user,
                operation_type='return',
                operation_date=timezone.now(),
                actual_return_date=timezone.now(),
                status_after_operation='available',
                description=f'设备归还 - 操作员：{operator.username}',
                operator=operator
            )
            
            # 更新借出记录的实际归还时间
            borrow_ledger.actual_return_date = timezone.now()
            borrow_ledger.save()
            
            print(f'已为设备 {device.device_code} 创建归还台账记录')
        else:
            print(f'未找到设备 {device.device_code} 的借出记录')
            
    except Exception as e:
        print(f'创建归还台账记录失败：{str(e)}')
