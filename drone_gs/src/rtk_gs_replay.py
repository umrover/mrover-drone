#!/usr/bin/env python3
import socket
import rclpy
from rclpy.node import Node
from rtcm_msgs.msg import Message as RTCMMessage

DRONE_LAPTOP_IP = "192.168.1.20"  # Laptop 2's Ethernet IP
UDP_PORT = 13370

class SimpleRTKRelay(Node):
    def __init__(self):
        super().__init__("rtk_relay_node")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Subscribe to the Localization team's topic
        self.sub = self.create_subscription(
            RTCMMessage, "rtcm", self.rtcm_callback, 10
        )
        self.get_logger().info(f"Relaying 'rtcm' -> UDP to {DRONE_LAPTOP_IP}:{UDP_PORT}")

    def rtcm_callback(self, msg):
        if msg.message:
            # Blast raw bytes across the Ethernet cable to Laptop 2
            self.sock.sendto(bytes(msg.message), (DRONE_LAPTOP_IP, UDP_PORT))

def main():
    rclpy.init()
    node = SimpleRTKRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
