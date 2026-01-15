"""财务处系统集成模块"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from booking.models import Booking
from django.utils import timezone
import json

@csrf_exempt
@require_http_methods(["POST"])
def finance_payment_callback(request):
    """财务处缴费确认回调接口"""
    try:
        data = json.loads(request.body)
        booking_code = data.get('booking_code')
        payment_status = data.get('payment_status')  # 'paid' 或 'failed'
        payment_time = data.get('payment_time')
        
        if not booking_code:
            return JsonResponse({'success': False, 'error': '缺少预约编号'}, status=400)
        
        try:
            booking = Booking.objects.get(booking_code=booking_code)
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': '预约不存在'}, status=404)
        
        if payment_status == 'paid':
            # 缴费成功
            booking.payment_status = 'paid'
            booking.finance_confirmed = True
            booking.save()
            
            # 如果状态是待缴费，更新为全部审批通过
            if booking.status == 'payment_pending':
                booking.status = 'manager_approved'
                booking.save()
            
            return JsonResponse({
                'success': True,
                'message': '缴费确认成功',
                'booking_code': booking_code
            })
        else:
            # 缴费失败
            return JsonResponse({
                'success': False,
                'error': '缴费失败',
                'booking_code': booking_code
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON格式错误'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def send_payment_request_to_finance(booking):
    """发送缴费请求到财务处系统（模拟）"""
    # 在实际环境中，这里应该调用财务处的API
    # 这里只是模拟，实际需要根据财务处系统的API文档实现
    
    payment_data = {
        'booking_code': booking.booking_code,
        'applicant_name': booking.applicant.name,
        'applicant_code': booking.applicant.user_code,
        'device_code': booking.device.device_code,
        'device_name': booking.device.model,
        'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
        'time_slot': booking.time_slot,
        'payment_amount': float(booking.payment_amount),
        'callback_url': f'/booking/finance/callback/'  # 财务处确认后的回调地址
    }
    
    # TODO: 实际调用财务处API
    # response = requests.post('https://finance.jnu.edu.cn/api/payment', json=payment_data)
    
    # 模拟：直接返回成功（实际应该等待财务处回调）
    return {
        'success': True,
        'message': '缴费请求已发送到财务处',
        'payment_data': payment_data
    }
