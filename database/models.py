from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float
from sqlalchemy.sql import func
from .db_connection import Base
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL
from flask import jsonify

class PowerStationInfo(Base):
    __tablename__ = 'power_station_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(255), unique=True, nullable=False)
    pv_pic = Column(String(1023))
    construction_work_pic = Column(String(1023))
    installation_address = Column(String(255))
    installation_province = Column(String(255))
    installation_province_city = Column(String(255))
    installation_county = Column(String(255))
    installation_county_code = Column(String(255))
    installation_province_city_code = Column(String(255))
    installation_province_code = Column(String(255))
    max_support_wind_power = Column(Float)

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'pv_pic': self.pv_pic,
            'construction_work_pic': self.construction_work_pic,
            'installation_address': self.installation_address,
            'installation_province': self.installation_province,
            'installation_province_city': self.installation_province_city,
            'installation_county': self.installation_county,
            'installation_county_code': self.installation_county_code,
            'installation_province_city_code': self.installation_province_city_code,
            'installation_province_code': self.installation_province_code,
            'max_support_wind_power': self.max_support_wind_power
        }

class OrderOperationLog(Base):
    __tablename__ = 'order_operation_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), nullable=False)
    operation_name = Column(String(100), nullable=False)
    operation_result = Column(String(50), nullable=False)
    operation_description = Column(Text)
    ai_remark = Column(Text)
    operation_time = Column(TIMESTAMP, default=func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'operation_name': self.operation_name,
            'operation_result': self.operation_result,
            'operation_description': self.operation_description,
            'ai_remark': self.ai_remark,
            'operation_time': self.operation_time
        }

class PvStationDailyMonitor(Base):
    __tablename__ = 'pv_station_daily_monitor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), nullable=False, comment='订单编号')
    record_time = Column(DateTime, nullable=False, comment='记录时间')
    voltage = Column(DECIMAL(10, 2), comment='电压 (V)')
    current = Column(DECIMAL(10, 2), comment='电流 (A)')
    max_module_temp = Column(DECIMAL(5, 2), comment='最大组件温度 (℃)')
    avg_module_temp = Column(DECIMAL(5, 2), comment='平均组件温度 (℃)')
    avg_ambient_temp = Column(DECIMAL(5, 2), comment='平均环境温度 (℃)')
    power_ratio = Column(DECIMAL(5, 2), comment='功率比 (%) 1.1~1.3（超配比）')
    work_hour_count = Column(DECIMAL(6, 2), comment='等效利用小时数 (h)')
    power_generation = Column(DECIMAL(10, 2), comment='实际发电量 (kWh)')
    theoretical_power = Column(DECIMAL(10, 2), comment='理论发电量 (kWh)')
    system_efficiency = Column(DECIMAL(5, 2), comment='系统效率 (%) 75%~85%')

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'record_time': self.record_time,
            'voltage': float(self.voltage) if self.voltage else None,
            'current': float(self.current) if self.current else None,
            'max_module_temp': float(self.max_module_temp) if self.max_module_temp else None,
            'avg_module_temp': float(self.avg_module_temp) if self.avg_module_temp else None,
            'avg_ambient_temp': float(self.avg_ambient_temp) if self.avg_ambient_temp else None,
            'power_ratio': float(self.power_ratio) if self.power_ratio else None,
            'work_hour_count': float(self.work_hour_count) if self.work_hour_count else None,
            'power_generation': float(self.power_generation) if self.power_generation else None,
            'theoretical_power': float(self.theoretical_power) if self.theoretical_power else None,
            'system_efficiency': float(self.system_efficiency) if self.system_efficiency else None
        }
def PvStationDailyMonitor_to_string(order_monitor):
    """
    将单个 order_daily_monitor 对象/字典转为带中文备注的字符串
    """
    return (
        f"订单编号: {order_monitor.order_no}\n"
        f"记录时间: {order_monitor.record_time}\n"
        f"电压 (V): {order_monitor.voltage}\n"
        f"电流 (A): {order_monitor.current}\n"
        f"最大组件温度: {order_monitor.max_module_temp} ℃\n"
        f"平均组件温度: {order_monitor.avg_module_temp} ℃\n"
        f"平均环境温度: {order_monitor.avg_ambient_temp} ℃\n"
        f"功率比 (%): {order_monitor.power_ratio}%\n"
        f"等效利用小时数 (h): {order_monitor.work_hour_count} h\n"
        f"实际发电量 (kWh): {order_monitor.power_generation} kWh\n"
        f"理论发电量 (kWh): {order_monitor.theoretical_power} kWh"
    )

# 如果是多个数据，可以遍历处理
def list_to_string(order_daily_monitors):
    result = []
    for monitor in order_daily_monitors:
        result.append(PvStationDailyMonitor_to_string(monitor))
    return "\n\n---\n\n".join(result)
