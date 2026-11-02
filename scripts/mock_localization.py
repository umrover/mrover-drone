#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rtcm_msgs.msg import Message as RTCMMessage

class MockLocalizationNode(Node):
    def __init__(self):
        super().__init__("mock_localization_node")

        self.publisher_ = self.create_publisher(RTCMMessage, "rtcm", 10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.sample_rtcm = bytes.fromhex("d300133ed000038a47702bf9283f6be731b539999000a6e7df")
        self.get_logger().info("Mock base station running! Publishing to 'rtcm' topic...\n")

    def timer_callback(self):
        msg = RTCMMessage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_station"
        msg.message = list(self.sample_rtcm)

        self.publisher_.publish(msg)
        self.get_logger().info(f"Published {len(msg.message)} RTCM bytes to 'rtcm'\n")

def main(args=None):
    rclpy.init(args=args)
    node = MockLocalizationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
