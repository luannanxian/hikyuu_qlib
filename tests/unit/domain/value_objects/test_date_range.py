"""
DateRange Value Object 单元测试

测试 DR-002: DateRange (日期范围) 领域模型
"""

from datetime import date

import pytest

from domain.value_objects.date_range import DateRange


class TestDateRangeCreation:
    """测试 DateRange 创建"""

    def test_valid_date_range(self):
        """测试有效日期范围创建"""
        start = date(2020, 1, 1)
        end = date(2020, 12, 31)

        date_range = DateRange(start_date=start, end_date=end)

        assert date_range.start_date == start
        assert date_range.end_date == end

    def test_same_date_range(self):
        """测试开始日期等于结束日期(单日范围)"""
        same_date = date(2020, 1, 1)
        date_range = DateRange(start_date=same_date, end_date=same_date)

        assert date_range.start_date == same_date
        assert date_range.end_date == same_date

    def test_invalid_date_range_raises_error(self):
        """测试开始日期晚于结束日期抛出异常"""
        start = date(2020, 12, 31)
        end = date(2020, 1, 1)

        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            DateRange(start_date=start, end_date=end)


class TestDateRangeImmutability:
    """测试 DateRange 不可变性"""

    def test_date_range_immutability(self):
        """验证 DateRange 值对象不可变"""
        date_range = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))

        # 尝试修改属性应该失败
        with pytest.raises(AttributeError):
            date_range.start_date = date(2021, 1, 1)

        with pytest.raises(AttributeError):
            date_range.end_date = date(2021, 12, 31)


class TestDateRangeContains:
    """测试 DateRange 包含判断"""

    def test_date_in_range(self):
        """测试日期在范围内"""
        date_range = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))

        # 边界日期
        assert date_range.contains(date(2020, 1, 1)) is True
        assert date_range.contains(date(2020, 12, 31)) is True

        # 中间日期
        assert date_range.contains(date(2020, 6, 15)) is True

    def test_date_not_in_range(self):
        """测试日期不在范围内"""
        date_range = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))

        # 早于开始日期
        assert date_range.contains(date(2019, 12, 31)) is False

        # 晚于结束日期
        assert date_range.contains(date(2021, 1, 1)) is False


class TestDateRangeOverlap:
    """测试 DateRange 重叠判断"""

    def test_ranges_overlap(self):
        """测试日期范围重叠"""
        range1 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 6, 30))
        range2 = DateRange(start_date=date(2020, 6, 1), end_date=date(2020, 12, 31))

        assert range1.overlaps(range2) is True
        assert range2.overlaps(range1) is True

    def test_ranges_do_not_overlap(self):
        """测试日期范围不重叠"""
        range1 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 6, 30))
        range2 = DateRange(start_date=date(2020, 7, 1), end_date=date(2020, 12, 31))

        assert range1.overlaps(range2) is False
        assert range2.overlaps(range1) is False

    def test_ranges_touch_but_not_overlap(self):
        """测试日期范围相邻但不重叠"""
        range1 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 6, 30))
        range2 = DateRange(start_date=date(2020, 7, 1), end_date=date(2020, 12, 31))

        # 6月30日和7月1日相邻,不算重叠
        assert range1.overlaps(range2) is False


class TestDateRangeDuration:
    """测试 DateRange 持续时间"""

    def test_duration_in_days(self):
        """测试持续时间(天数)"""
        date_range = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 1, 10))

        # 1月1日 到 1月10日 = 10 天
        assert date_range.duration_days() == 10

    def test_single_day_duration(self):
        """测试单日持续时间"""
        date_range = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 1, 1))

        assert date_range.duration_days() == 1


class TestDateRangeEquality:
    """测试 DateRange 相等性"""

    def test_date_range_equality(self):
        """验证值对象相等性"""
        range1 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        range2 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        range3 = DateRange(start_date=date(2021, 1, 1), end_date=date(2021, 12, 31))

        # 相同值的 DateRange 应该相等
        assert range1 == range2
        assert range1 is not range2

        # 不同值的 DateRange 不相等
        assert range1 != range3

    def test_date_range_hash(self):
        """验证 DateRange 可以作为字典键"""
        range1 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        range2 = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))

        # 相同值应该有相同 hash
        assert hash(range1) == hash(range2)

        # 可以作为字典键
        range_dict = {range1: "2020年"}
        assert range_dict[range2] == "2020年"


class TestDateRangeStringRepresentation:
    """测试 DateRange 字符串表示"""

    def test_date_range_string_representation(self):
        """验证字符串表示"""
        date_range = DateRange(start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))

        # __str__() 返回日期范围
        assert str(date_range) == "2020-01-01 to 2020-12-31"

        # __repr__() 返回带类名的表示
        assert "DateRange" in repr(date_range)
        assert "2020-01-01" in repr(date_range)
        assert "2020-12-31" in repr(date_range)
