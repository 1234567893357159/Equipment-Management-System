from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.urls import reverse
from datetime import date, timedelta
from decimal import Decimal

from devices.models import Device
from user.models import UserInfo
from booking.models import Booking
from ledger.models import DeviceLedger


class LedgerModelTestCase(TestCase):
    """台账模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户组
        self.admin_group = Group.objects.create(name='设备管理员')
        self.manager_group = Group.objects.create(name='实验室负责人')
        
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='admin123',
            email='admin@test.com'
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.manager_user = User.objects.create_user(
            username='manager', 
            password='manager123',
            email='manager@test.com'
        )
        self.manager_user.groups.add(self.manager_group)
        
        self.normal_user = User.objects.create_user(
            username='normal', 
            password='normal123',
            email='normal@test.com'
        )
        
        # 创建用户信息
        self.teacher = UserInfo.objects.create(
            user_code='T001',
            name='张老师',
            user_type='teacher',
            department='计算机学院',
            phone='13800138001',
            gender='男',
            title='教授',
            research_field='人工智能',
            auth_user=self.admin_user
        )
        
        self.student = UserInfo.objects.create(
            user_code='S001',
            name='李同学',
            user_type='student',
            department='计算机学院',
            phone='13800138002',
            gender='女',
            major='计算机科学',
            advisor='张老师',
            auth_user=self.normal_user
        )
        
        self.external = UserInfo.objects.create(
            user_code='E001',
            name='王先生',
            user_type='external',
            department='外部公司',
            phone='13800138003',
            gender='男',
            auth_user=self.manager_user
        )
        
        # 创建设备
        self.device1 = Device.objects.create(
            device_code='DEV001',
            model='测试设备A',
            manufacturer='测试厂商',
            status='available',
            price_internal=Decimal('100.00'),
            price_external=Decimal('200.00')
        )
        
        self.device2 = Device.objects.create(
            device_code='DEV002',
            model='测试设备B',
            manufacturer='测试厂商',
            status='available',
            price_internal=Decimal('150.00'),
            price_external=Decimal('300.00')
        )
    
    def test_device_ledger_creation(self):
        """测试设备台账记录创建"""
        ledger = DeviceLedger.objects.create(
            device=self.device1,
            device_name=self.device1.model,
            user=self.teacher,
            operation_type='borrow',
            operation_date=timezone.now(),
            expected_return_date=timezone.now() + timedelta(days=7),
            status_after_operation='unavailable',
            description='测试借出',
            operator=self.admin_user
        )
        
        self.assertEqual(ledger.device.device_code, 'DEV001')
        self.assertEqual(ledger.device_name, '测试设备A')
        self.assertEqual(ledger.user.name, '张老师')
        self.assertEqual(ledger.operation_type, 'borrow')
        self.assertEqual(ledger.status_after_operation, 'unavailable')
        self.assertIsNotNone(ledger.expected_return_date)
        self.assertIsNotNone(ledger.created_at)
    
    def test_device_ledger_operation_types(self):
        """测试所有操作类型"""
        operation_types = ['borrow', 'return', 'maintenance', 'repair', 'discard', 'other']
        
        for op_type in operation_types:
            ledger = DeviceLedger.objects.create(
                device=self.device1,
                device_name=self.device1.model,
                user=self.teacher,
                operation_type=op_type,
                operation_date=timezone.now(),
                status_after_operation='available',
                operator=self.admin_user
            )
            self.assertEqual(ledger.operation_type, op_type)
    
    def test_device_ledger_return_operation(self):
        """测试归还操作"""
        # 先创建借出记录
        borrow_ledger = DeviceLedger.objects.create(
            device=self.device1,
            device_name=self.device1.model,
            user=self.teacher,
            operation_type='borrow',
            operation_date=timezone.now(),
            expected_return_date=timezone.now() + timedelta(days=7),
            status_after_operation='unavailable',
            operator=self.admin_user
        )
        
        # 创建归还记录
        return_ledger = DeviceLedger.objects.create(
            device=self.device1,
            device_name=self.device1.model,
            user=self.teacher,
            operation_type='return',
            operation_date=timezone.now(),
            actual_return_date=timezone.now(),
            status_after_operation='available',
            operator=self.admin_user
        )
        
        self.assertEqual(return_ledger.operation_type, 'return')
        self.assertIsNotNone(return_ledger.actual_return_date)
        self.assertEqual(return_ledger.status_after_operation, 'available')
    
    def test_device_ledger_str_representation(self):
        """测试台账记录的字符串表示"""
        ledger = DeviceLedger.objects.create(
            device=self.device1,
            device_name=self.device1.model,
            user=self.teacher,
            operation_type='borrow',
            operation_date=timezone.now(),
            status_after_operation='unavailable',
            operator=self.admin_user
        )
        
        str_repr = str(ledger)
        self.assertIn('DEV001', str_repr)
        self.assertIn('测试设备A', str_repr)
        self.assertIn('借出', str_repr)


class LedgerViewTestCase(TestCase):
    """台账视图测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户组
        self.admin_group = Group.objects.create(name='设备管理员')
        self.manager_group = Group.objects.create(name='实验室负责人')
        
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='admin123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.manager_user = User.objects.create_user(
            username='manager', 
            password='manager123'
        )
        self.manager_user.groups.add(self.manager_group)
        
        self.normal_user = User.objects.create_user(
            username='normal', 
            password='normal123'
        )
        
        # 创建用户信息
        self.teacher = UserInfo.objects.create(
            user_code='T001',
            name='张老师',
            user_type='teacher',
            department='计算机学院',
            phone='13800138001',
            gender='男',
            title='教授',
            research_field='人工智能',
            auth_user=self.admin_user
        )
        
        self.student = UserInfo.objects.create(
            user_code='S001',
            name='李同学',
            user_type='student',
            department='计算机学院',
            phone='13800138002',
            gender='女',
            major='计算机科学',
            advisor='张老师',
            auth_user=self.normal_user
        )
        
        self.external = UserInfo.objects.create(
            user_code='E001',
            name='王先生',
            user_type='external',
            department='外部公司',
            phone='13800138003',
            gender='男',
            auth_user=self.manager_user
        )
        
        # 创建设备
        self.device1 = Device.objects.create(
            device_code='DEV001',
            model='测试设备A',
            manufacturer='测试厂商',
            status='available',
            price_internal=Decimal('100.00'),
            price_external=Decimal('200.00')
        )
        
        self.device2 = Device.objects.create(
            device_code='DEV002',
            model='测试设备B',
            manufacturer='测试厂商',
            status='unavailable',
            price_internal=Decimal('150.00'),
            price_external=Decimal('300.00')
        )
        
        # 创建预约记录
        self.booking1 = Booking.objects.create(
            booking_code='BOOK001',
            applicant=self.teacher,
            device=self.device1,
            booking_date=date.today(),
            time_slot='上午',
            purpose='教学使用',
            status='manager_approved'
        )
        
        self.booking2 = Booking.objects.create(
            booking_code='BOOK002',
            applicant=self.student,
            device=self.device1,
            booking_date=date.today(),
            time_slot='下午',
            purpose='实验使用',
            status='manager_approved'
        )
        
        self.booking3 = Booking.objects.create(
            booking_code='BOOK003',
            applicant=self.external,
            device=self.device2,
            booking_date=date.today(),
            time_slot='全天',
            purpose='研究使用',
            status='manager_approved'
        )
        
        # 创建台账记录
        self.ledger1 = DeviceLedger.objects.create(
            device=self.device1,
            device_name=self.device1.model,
            user=self.teacher,
            operation_type='borrow',
            operation_date=timezone.now(),
            expected_return_date=timezone.now() + timedelta(days=7),
            status_after_operation='unavailable',
            description='测试借出1',
            operator=self.admin_user
        )
        
        self.ledger2 = DeviceLedger.objects.create(
            device=self.device2,
            device_name=self.device2.model,
            user=self.student,
            operation_type='borrow',
            operation_date=timezone.now(),
            expected_return_date=timezone.now() + timedelta(days=5),
            status_after_operation='unavailable',
            description='测试借出2',
            operator=self.admin_user
        )
        
        # 创建客户端
        self.client = Client()
    
    def test_ledger_home_admin_access(self):
        """测试管理员访问台账首页"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:ledger_home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_admin', response.context)
        self.assertTrue(response.context['is_admin'])
    
    def test_ledger_home_manager_access(self):
        """测试负责人访问台账首页"""
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('ledger:ledger_home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_manager', response.context)
        self.assertTrue(response.context['is_manager'])
    
    def test_ledger_home_permission_denied(self):
        """测试普通用户无法访问台账首页"""
        self.client.login(username='normal', password='normal123')
        response = self.client.get(reverse('ledger:ledger_home'))
        # 应该被重定向或返回403
        self.assertIn(response.status_code, [302, 403])
    
    def test_device_ledger_list(self):
        """测试设备台账列表"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:device_ledger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 应该包含两个设备
        self.assertEqual(response.context['page_obj'].paginator.count, 2)
    
    def test_device_ledger_list_filter(self):
        """测试设备台账列表筛选"""
        self.client.login(username='admin', password='admin123')
        # 按设备编号筛选
        response = self.client.get(reverse('ledger:device_ledger_list'), {'device_code': 'DEV001'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        
        # 按状态筛选
        response = self.client.get(reverse('ledger:device_ledger_list'), {'status': 'available'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_device_operation_history_list(self):
        """测试设备操作历史列表"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:device_operation_history_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 设备保存时会自动创建台账记录，所以实际记录数可能多于手动创建的
        # 至少应该包含我们手动创建的两个台账记录
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 2)
    
    def test_device_operation_history_list_filter(self):
        """测试设备操作历史列表筛选"""
        self.client.login(username='admin', password='admin123')
        # 按设备编号筛选
        response = self.client.get(
            reverse('ledger:device_operation_history_list'), 
            {'device_code': 'DEV001'}
        )
        self.assertEqual(response.status_code, 200)
        # 设备保存时会自动创建台账记录，所以实际记录数可能多于手动创建的
        # 至少应该包含我们手动创建的一个台账记录
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_device_ledger_detail(self):
        """测试设备台账详情"""
        self.client.login(username='admin', password='admin123')
        # 使用台账记录的ID而不是设备的ID
        response = self.client.get(
            reverse('ledger:device_ledger_detail', args=[self.ledger1.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('ledger', response.context)
        self.assertEqual(response.context['ledger'].device.device_code, 'DEV001')
    
    def test_teacher_ledger_list(self):
        """测试教师台账列表"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:teacher_ledger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 教师有预约记录，应该出现在列表中
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_teacher_ledger_list_filter(self):
        """测试教师台账列表筛选"""
        self.client.login(username='admin', password='admin123')
        # 按姓名筛选
        response = self.client.get(reverse('ledger:teacher_ledger_list'), {'name': '张老师'})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_student_ledger_list(self):
        """测试学生台账列表"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:student_ledger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 学生有预约记录，应该出现在列表中
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_student_ledger_list_filter(self):
        """测试学生台账列表筛选"""
        self.client.login(username='admin', password='admin123')
        # 按学号筛选
        response = self.client.get(reverse('ledger:student_ledger_list'), {'user_code': 'S001'})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_external_ledger_list(self):
        """测试校外人员台账列表"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:external_ledger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 校外人员有预约记录，应该出现在列表中
        self.assertGreaterEqual(response.context['page_obj'].paginator.count, 1)
    
    def test_booking_ledger_list(self):
        """测试预约台账列表"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:booking_ledger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 应该包含3个预约记录
        self.assertEqual(response.context['page_obj'].paginator.count, 3)
    
    def test_booking_ledger_list_filter(self):
        """测试预约台账列表筛选"""
        self.client.login(username='admin', password='admin123')
        # 按预约编号筛选
        response = self.client.get(reverse('ledger:booking_ledger_list'), {'booking_code': 'BOOK001'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        
        # 按设备编号筛选
        response = self.client.get(reverse('ledger:booking_ledger_list'), {'device_code': 'DEV001'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 2)


class LedgerExportTestCase(TestCase):
    """台账导出功能测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户组
        self.admin_group = Group.objects.create(name='设备管理员')
        
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='admin123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        # 创建额外的用户用于UserInfo
        self.teacher_user = User.objects.create_user(
            username='teacher_user', 
            password='teacher123'
        )
        self.student_user = User.objects.create_user(
            username='student_user', 
            password='student123'
        )
        self.external_user = User.objects.create_user(
            username='external_user', 
            password='external123'
        )
        
        # 创建用户信息
        self.teacher = UserInfo.objects.create(
            user_code='T001',
            name='张老师',
            user_type='teacher',
            department='计算机学院',
            phone='13800138001',
            gender='男',
            title='教授',
            research_field='人工智能',
            auth_user=self.teacher_user
        )
        
        self.student = UserInfo.objects.create(
            user_code='S001',
            name='李同学',
            user_type='student',
            department='计算机学院',
            phone='13800138002',
            gender='女',
            major='计算机科学',
            advisor='张老师',
            auth_user=self.student_user
        )
        
        self.external = UserInfo.objects.create(
            user_code='E001',
            name='王先生',
            user_type='external',
            department='外部公司',
            phone='13800138003',
            gender='男',
            auth_user=self.external_user
        )
        
        # 创建设备
        self.device1 = Device.objects.create(
            device_code='DEV001',
            model='测试设备A',
            manufacturer='测试厂商',
            status='available',
            price_internal=Decimal('100.00'),
            price_external=Decimal('200.00')
        )
        
        # 创建预约记录
        self.booking1 = Booking.objects.create(
            booking_code='BOOK001',
            applicant=self.teacher,
            device=self.device1,
            booking_date=date.today(),
            time_slot='上午',
            purpose='教学使用',
            status='manager_approved'
        )
        
        self.booking2 = Booking.objects.create(
            booking_code='BOOK002',
            applicant=self.student,
            device=self.device1,
            booking_date=date.today(),
            time_slot='下午',
            purpose='实验使用',
            status='manager_approved'
        )
        
        # 创建台账记录
        self.ledger1 = DeviceLedger.objects.create(
            device=self.device1,
            device_name=self.device1.model,
            user=self.teacher,
            operation_type='borrow',
            operation_date=timezone.now(),
            expected_return_date=timezone.now() + timedelta(days=7),
            status_after_operation='unavailable',
            description='测试借出',
            operator=self.admin_user
        )
        
        # 创建客户端
        self.client = Client()
    
    def test_export_device_ledger_excel(self):
        """测试导出设备台账Excel"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:export_device_ledger_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])
    
    def test_export_teacher_ledger_excel(self):
        """测试导出教师台账Excel"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:export_teacher_ledger_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])
    
    def test_export_student_ledger_excel(self):
        """测试导出学生台账Excel"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:export_student_ledger_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])
    
    def test_export_external_ledger_excel(self):
        """测试导出校外人员台账Excel"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:export_external_ledger_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])
    
    def test_export_booking_ledger_excel(self):
        """测试导出预约台账Excel"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:export_booking_ledger_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])
    
    def test_export_device_operation_history_excel(self):
        """测试导出设备操作历史Excel"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:export_ledger_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])


class LedgerPaginationTestCase(TestCase):
    """台账分页测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户组
        self.admin_group = Group.objects.create(name='设备管理员')
        
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='admin123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        # 创建多个设备用于测试分页
        for i in range(25):
            Device.objects.create(
                device_code=f'DEV{i:03d}',
                model=f'测试设备{i}',
                manufacturer='测试厂商',
                status='available',
                price_internal=Decimal('100.00'),
                price_external=Decimal('200.00')
            )
        
        # 创建客户端
        self.client = Client()
    
    def test_device_ledger_list_pagination(self):
        """测试设备台账列表分页"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:device_ledger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        # 每页20条，25条数据应该有2页
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 2)
        self.assertEqual(response.context['page_obj'].paginator.count, 25)
    
    def test_device_ledger_list_page_navigation(self):
        """测试设备台账列表翻页"""
        self.client.login(username='admin', password='admin123')
        # 第一页
        response = self.client.get(reverse('ledger:device_ledger_list'), {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_next())
        
        # 第二页
        response = self.client.get(reverse('ledger:device_ledger_list'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_previous())


class LedgerIntegrationTestCase(TestCase):
    """台账集成测试：测试预约与台账的联动"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户组
        self.admin_group = Group.objects.create(name='设备管理员')
        
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='admin123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        # 创建额外的用户用于UserInfo
        self.teacher_user = User.objects.create_user(
            username='teacher_user2', 
            password='teacher123'
        )
        
        # 创建用户信息
        self.teacher = UserInfo.objects.create(
            user_code='T001',
            name='张老师',
            user_type='teacher',
            department='计算机学院',
            phone='13800138001',
            gender='男',
            title='教授',
            research_field='人工智能',
            auth_user=self.teacher_user
        )
        
        # 创建设备
        self.device1 = Device.objects.create(
            device_code='DEV001',
            model='测试设备A',
            manufacturer='测试厂商',
            status='available',
            price_internal=Decimal('100.00'),
            price_external=Decimal('200.00')
        )
        
        # 创建客户端
        self.client = Client()
    
    def test_booking_creates_ledger_integration(self):
        """测试预约审批通过后，用户台账应该显示该预约"""
        # 创建预约
        booking = Booking.objects.create(
            booking_code='BOOK001',
            applicant=self.teacher,
            device=self.device1,
            booking_date=date.today(),
            time_slot='上午',
            purpose='教学使用',
            status='manager_approved'
        )
        
        # 登录并查看教师台账
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ledger:teacher_ledger_list'))
        self.assertEqual(response.status_code, 200)
        
        # 教师台账应该包含这个教师（因为有预约记录）
        teachers = response.context['page_obj'].object_list
        teacher_codes = [t.user_code for t in teachers]
        self.assertIn('T001', teacher_codes)
        
        # 预约台账应该包含这个预约
        response = self.client.get(reverse('ledger:booking_ledger_list'))
        self.assertEqual(response.status_code, 200)
        bookings = response.context['page_obj'].object_list
        booking_codes = [b.booking_code for b in bookings]
        self.assertIn('BOOK001', booking_codes)
