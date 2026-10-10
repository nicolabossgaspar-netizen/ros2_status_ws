import signal
import time
from datetime import datetime

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QFormLayout, QLabel, QWidget
from status_interfaces.msg import SystemStatus


class StatusWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ROS 2 系统状态监看')
        self.resize(470, 310)
        layout = QFormLayout(self)
        self.labels = {}
        fields = [
            ('time', '采样时间'),
            ('host', '主机名'),
            ('cpu', 'CPU 使用率'),
            ('mem', '内存使用率'),
            ('total', '内存总大小'),
            ('available', '剩余可用内存'),
            ('recv', '网络累计接收'),
            ('sent', '网络累计发送'),
            ('state', '连接状态'),
        ]
        for key, title in fields:
            label = QLabel('--')
            label.setWordWrap(True)
            self.labels[key] = label
            layout.addRow(title, label)
        self.last_received = None

    def show_status(self, msg):
        seconds = msg.stamp.sec + msg.stamp.nanosec / 1e9
        sample_time = datetime.fromtimestamp(seconds).astimezone()
        values = {
            'time': sample_time.isoformat(sep=' ', timespec='seconds'),
            'host': msg.hostname,
            'cpu': f'{msg.cpu_percent:.1f} %',
            'mem': f'{msg.memory_percent:.1f} %',
            'total': f'{msg.memory_total / 1024**3:.2f} GiB',
            'available': f'{msg.memory_available / 1024**3:.2f} GiB',
            'recv': f'{msg.net_bytes_recv / 1024**2:.2f} MiB',
            'sent': f'{msg.net_bytes_sent / 1024**2:.2f} MiB',
            'state': '正在接收',
        }
        for key, value in values.items():
            self.labels[key].setText(value)
        self.last_received = time.monotonic()

    def check_connection(self):
        if self.last_received is None:
            self.labels['state'].setText('等待数据')
        elif time.monotonic() - self.last_received > 3.0:
            self.labels['state'].setText('超过 3 秒未收到数据')


class StatusSubscriber(Node):
    def __init__(self, window):
        super().__init__('status_gui')
        self.subscription = self.create_subscription(
            SystemStatus, '/system_status', window.show_status, 10)


def main(args=None):
    rclpy.init(args=args)
    app = QApplication([])
    window = StatusWindow()
    node = StatusSubscriber(window)
    signal.signal(signal.SIGINT, lambda _signum, _frame: app.quit())

    def process_ros():
        if not rclpy.ok():
            app.quit()
            return
        try:
            rclpy.spin_once(node, timeout_sec=0.0)
        except ExternalShutdownException:
            app.quit()
            return
        window.check_connection()

    timer = QTimer()
    timer.timeout.connect(process_ros)
    timer.start(20)
    window.show()
    try:
        app.exec_()
    finally:
        timer.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
