import platform
import time

import psutil
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from status_interfaces.msg import SystemStatus


class StatusPublisher(Node):
    def __init__(self):
        super().__init__('status_publisher')
        self.pub = self.create_publisher(
            SystemStatus, '/system_status', 10)
        self.hostname = platform.node()
        psutil.cpu_percent(interval=None)
        self.timer = self.create_timer(1.0, self.publish_status)

    def publish_status(self):
        stamp_ns = time.time_ns()
        memory = psutil.virtual_memory()
        network = psutil.net_io_counters()

        msg = SystemStatus()
        msg.stamp.sec = stamp_ns // 1_000_000_000
        msg.stamp.nanosec = stamp_ns % 1_000_000_000
        msg.hostname = self.hostname
        msg.cpu_percent = float(psutil.cpu_percent(interval=None))
        msg.memory_percent = float(memory.percent)
        msg.memory_total = int(memory.total)
        msg.memory_available = int(memory.available)
        msg.net_bytes_recv = int(network.bytes_recv) if network else 0
        msg.net_bytes_sent = int(network.bytes_sent) if network else 0
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = StatusPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
