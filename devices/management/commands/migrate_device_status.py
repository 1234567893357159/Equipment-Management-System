"""数据迁移命令：将设备状态从unavailable转换为available"""
from django.core.management.base import BaseCommand
from devices.models import Device

class Command(BaseCommand):
    help = '将数据库中状态为unavailable的设备转换为available（因为已移除unavailable状态）'
    
    def handle(self, *args, **options):
        # 查找所有状态为unavailable的设备
        unavailable_devices = Device.objects.filter(status='unavailable')
        count = unavailable_devices.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('没有需要迁移的设备（所有设备状态都是有效的）'))
            return
        
        self.stdout.write(f'找到 {count} 个状态为"unavailable"的设备，开始迁移...')
        
        # 将所有unavailable状态转换为available
        updated = unavailable_devices.update(status='available')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功将 {updated} 个设备的状态从"unavailable"转换为"available"（正常）'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '注意：设备状态现在只表示物理状态（正常/维修中/已报废），时段可用性由预约情况决定'
            )
        )
