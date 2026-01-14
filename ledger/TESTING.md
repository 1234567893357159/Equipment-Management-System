# 测试使用指南

本文档说明如何运行和使用台账模块的测试。

## 快速开始

### 运行所有台账测试

```bash
python manage.py test ledger.tests
```

### 运行特定测试类

```bash
# 只运行模型测试
python manage.py test ledger.tests.LedgerModelTestCase

# 只运行视图测试
python manage.py test ledger.tests.LedgerViewTestCase

# 只运行导出功能测试
python manage.py test ledger.tests.LedgerExportTestCase

# 只运行分页测试
python manage.py test ledger.tests.LedgerPaginationTestCase

# 只运行集成测试
python manage.py test ledger.tests.LedgerIntegrationTestCase
```

### 运行特定测试方法

```bash
# 运行单个测试方法
python manage.py test ledger.tests.LedgerModelTestCase.test_device_ledger_creation

# 运行多个测试方法
python manage.py test ledger.tests.LedgerModelTestCase.test_device_ledger_creation ledger.tests.LedgerModelTestCase.test_device_ledger_return_operation
```

## 测试选项

### 详细输出模式

```bash
# 显示详细输出（推荐）
python manage.py test ledger.tests --verbosity=2

# 显示简洁输出
python manage.py test ledger.tests --verbosity=1

# 不显示输出（只显示结果）
python manage.py test ledger.tests --verbosity=0
```

### 保留测试数据库

```bash
# 保留测试数据库（用于调试）
python manage.py test ledger.tests --keepdb
```

### 并行运行测试

```bash
# 使用多个进程并行运行（加快测试速度）
python manage.py test ledger.tests --parallel
```

### 只运行失败的测试

```bash
# 只运行上次失败的测试
python manage.py test ledger.tests --failfast
```

## 测试覆盖范围

当前测试文件包含以下测试类：

### 1. LedgerModelTestCase（模型测试）
- ✅ 测试设备台账记录的创建
- ✅ 测试所有操作类型（借出、归还、维护、维修、报废、其他）
- ✅ 测试归还操作
- ✅ 测试台账记录的字符串表示

### 2. LedgerViewTestCase（视图测试）
- ✅ 测试台账首页的访问权限
- ✅ 测试设备台账列表及筛选
- ✅ 测试设备操作历史列表及筛选
- ✅ 测试设备台账详情
- ✅ 测试教师/学生/校外人员台账列表及筛选
- ✅ 测试预约台账列表及筛选

### 3. LedgerExportTestCase（导出功能测试）
- ✅ 测试所有台账的Excel导出功能

### 4. LedgerPaginationTestCase（分页测试）
- ✅ 测试设备台账列表的分页功能

### 5. LedgerIntegrationTestCase（集成测试）
- ✅ 测试预约与台账的联动

## 测试输出说明

### 成功示例

```
Creating test database for alias 'default'...
....................
----------------------------------------------------------------------
Ran 28 tests in 129.163s

OK
Destroying test database for alias 'default'...
```

### 失败示例

```
FAIL: test_device_ledger_creation (ledger.tests.LedgerModelTestCase.test_device_ledger_creation)
测试设备台账记录创建
----------------------------------------------------------------------
Traceback (most recent call last):
  File "...", line 42, in test_device_ledger_creation
    self.assertEqual(self.ledger.device.device_code, 'DEV001')
AssertionError: 'DEV002' != 'DEV001'
```

## 常见问题

### Q: 测试运行很慢怎么办？

A: 可以使用 `--parallel` 选项并行运行测试，或者只运行特定的测试类。

```bash
python manage.py test ledger.tests --parallel
```

### Q: 如何调试失败的测试？

A: 使用 `--keepdb` 选项保留测试数据库，然后可以在Django shell中查看数据：

```bash
# 运行测试并保留数据库
python manage.py test ledger.tests.LedgerModelTestCase --keepdb

# 在另一个终端中查看测试数据库
python manage.py shell --settings=your_project.settings
```

### Q: 如何查看测试覆盖率？

A: 可以使用 `coverage.py` 工具：

```bash
# 安装coverage
pip install coverage

# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test ledger.tests
coverage report
coverage html  # 生成HTML报告
```

### Q: 测试数据库在哪里？

A: 测试使用独立的测试数据库，默认在内存中（SQLite），测试结束后会自动销毁。使用 `--keepdb` 可以保留数据库用于调试。

## 编写新测试

如果需要添加新的测试，可以参考现有测试的结构：

```python
from django.test import TestCase
from ledger.models import DeviceLedger

class MyNewTestCase(TestCase):
    def setUp(self):
        """设置测试数据"""
        # 创建测试数据
        pass
    
    def test_my_feature(self):
        """测试我的功能"""
        # 编写测试逻辑
        self.assertEqual(1, 1)
```

## 最佳实践

1. **测试隔离**：每个测试方法应该是独立的，不依赖其他测试的执行顺序
2. **使用setUp**：在 `setUp` 方法中创建测试数据，避免重复代码
3. **清晰的测试名称**：使用描述性的测试方法名称，说明测试的内容
4. **测试边界情况**：不仅要测试正常情况，还要测试边界和异常情况
5. **保持测试快速**：避免在测试中进行耗时的操作

## 相关命令速查

```bash
# 运行所有测试
python manage.py test

# 运行特定app的测试
python manage.py test ledger

# 运行特定测试类
python manage.py test ledger.tests.LedgerModelTestCase

# 运行特定测试方法
python manage.py test ledger.tests.LedgerModelTestCase.test_device_ledger_creation

# 详细输出
python manage.py test ledger.tests --verbosity=2

# 保留测试数据库
python manage.py test ledger.tests --keepdb

# 并行运行
python manage.py test ledger.tests --parallel

# 只运行失败的测试
python manage.py test ledger.tests --failfast
```
