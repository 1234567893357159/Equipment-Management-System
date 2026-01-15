"""
清除Django和Python缓存的管理命令
使用方法：python manage.py clear_cache
"""
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = '清除所有缓存文件（.pyc文件、__pycache__目录等）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的文件，不实际删除',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        base_dir = Path(settings.BASE_DIR)
        
        deleted_count = 0
        deleted_dirs = 0
        
        # 查找所有__pycache__目录和.pyc文件
        for root, dirs, files in os.walk(base_dir):
            # 跳过虚拟环境目录
            if 'venv' in root or 'env' in root or '.venv' in root:
                continue
            
            # 删除__pycache__目录
            if '__pycache__' in dirs:
                cache_dir = Path(root) / '__pycache__'
                if dry_run:
                    self.stdout.write(f'将删除目录: {cache_dir}')
                else:
                    try:
                        shutil.rmtree(cache_dir)
                        deleted_dirs += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'删除目录失败 {cache_dir}: {e}'))
                dirs.remove('__pycache__')  # 避免继续遍历
            
            # 删除.pyc文件
            for file in files:
                if file.endswith('.pyc'):
                    pyc_file = Path(root) / file
                    if dry_run:
                        self.stdout.write(f'将删除文件: {pyc_file}')
                    else:
                        try:
                            pyc_file.unlink()
                            deleted_count += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'删除文件失败 {pyc_file}: {e}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'将删除 {deleted_count} 个.pyc文件和 {deleted_dirs} 个__pycache__目录'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已清除缓存：删除了 {deleted_count} 个.pyc文件和 {deleted_dirs} 个__pycache__目录'))
            self.stdout.write(self.style.SUCCESS('建议重启Django开发服务器以确保更改生效'))
