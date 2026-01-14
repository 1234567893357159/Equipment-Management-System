from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from .models import Device
from .forms import DeviceForm
from ledger.models import DeviceLedger  # 保留：台账模型
from django.utils import timezone       # 保留：时间工具

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
    # 1. 处理搜索逻辑
    keyword = request.GET.get('keyword', '')
    if keyword:
        devices = Device.objects.filter(
            Q(device_code__icontains=keyword) | 
            Q(model__icontains=keyword) |
            Q(manufacturer__icontains=keyword)
        )
    else:
        devices = Device.objects.all().order_by('device_code')

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
            messages.success(request, success_msg)
            return redirect('device_manage')
        else:
            messages.error(request, "表单填写有误，请检查后重新提交！")

    # 3. 处理状态修改逻辑（保留审核逻辑并整合台账功能）
    status_action = request.GET.get('status_action')
    pk = request.GET.get('pk')
    if status_action and pk:
        device = get_object_or_404(Device, pk=pk)
        
        if status_action == 'available':
            # --- 整合功能：如果状态从不可用变为可用，自动创建归还台账 ---
            if device.status == 'unavailable' or device.status == '不可用':
                create_return_ledger(device, request.user)
            
            device.status = 'available' # 建议使用英文 key 以匹配 Model 定义
            msg = f"设备【{device.device_code}】已标记为可用！"
            
        elif status_action == 'unavailable':
            device.status = 'unavailable'
            msg = f"设备【{device.device_code}】已标记为不可用！"
            
        device.save()
        messages.success(request, msg)
        return redirect('device_manage')

    # 4. 准备表单和上下文数据
    if edit_device_id:
        device = get_object_or_404(Device, id=edit_device_id)
        form = DeviceForm(instance=device)
    else:
        form = DeviceForm()

    context = {
        'devices': devices,
        'keyword': keyword,
        'form': form,
        'edit_device_id_js': edit_device_id,
    }
    context.update(get_user_role_context(request))
    return render(request, 'admin/device_manage.html', context)

def device_delete(request, pk):
    """设备删除视图"""
    device = get_object_or_404(Device, pk=pk)
    device_code = device.device_code
    
    # 注意：Device.delete() 已在 models.py 中被重写，会自动记录“删除台账”
    device.delete()
    messages.success(request, f"设备【{device_code}】已成功删除并记入台账！")
    return redirect('device_manage')

def device_detail(request, pk):
    """设备详情/编辑页"""
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            return redirect('device_manage')
    else:
        form = DeviceForm(instance=device)

    context = {
        'device': device,
        'form': form,
    }
    context.update(get_user_role_context(request))

    # 渲染设备详情/编辑模板
    return render(request, 'admin/device_detail.html', context)

# --- 保留他人增加的功能函数：台账自动记录 ---

def create_return_ledger(device, operator):
    """创建设备归还台账记录"""
    try:
        # 查找该设备最近一次未归还的借出记录
        borrow_ledger = DeviceLedger.objects.filter(
            device=device,
            operation_type='borrow',
            actual_return_date__isnull=True
        ).order_by('-operation_date').first()
        
        if borrow_ledger:
            # 1. 创建归还台账记录
            DeviceLedger.objects.create(
                device=device,
                device_name=device.model,
                user=borrow_ledger.user,  # 关联原借用人
                operation_type='return',
                operation_date=timezone.now(),
                actual_return_date=timezone.now(),
                status_after_operation='available',
                description=f'设备归还 - 操作员：{operator.username}',
                operator=operator
            )
            
            # 2. 更新原借出记录的归还时间，完成闭环
            borrow_ledger.actual_return_date = timezone.now()
            borrow_ledger.save()
            
            print(f'已为设备 {device.device_code} 创建归还台账记录')
        else:
            # 如果没有借出记录，直接生成一条状态变更台账
            DeviceLedger.objects.create(
                device=device,
                device_name=device.model,
                operation_type='other',
                operation_date=timezone.now(),
                status_after_operation='available',
                description=f'手动恢复可用状态 - 操作员：{operator.username}',
                operator=operator
            )
            
    except Exception as e:
        # 实际生产环境建议记录到日志文件
        print(f'创建归还台账记录失败：{str(e)}')