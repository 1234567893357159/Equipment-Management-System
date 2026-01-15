"""定时任务：处理过期预约（设备状态不再自动更新，时段可用性由预约情况决定）"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from booking.models import Booking
from devices.models import Device

class Command(BaseCommand):
    help = '处理过期预约：自动取消过期未使用的预约。设备状态不再自动更新，时段可用性由预约情况决定。'
    
    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        
        # 处理过期未使用的预约：自动取消
        expired_bookings = Booking.objects.filter(
            booking_date__lt=today,
            status__in=['manager_approved', 'payment_pending']
        )
        
        for booking in expired_bookings:
            booking.status = 'cancelled'
            booking.save()
            self.stdout.write(
                self.style.WARNING(
                    f'预约 {booking.booking_code} 已过期，自动取消'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('过期预约处理完成'))
        self.stdout.write(self.style.SUCCESS('注意：设备状态不再自动更新，时段可用性由预约情况决定'))
