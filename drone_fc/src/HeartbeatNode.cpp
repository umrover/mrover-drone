/**
 * @brief Node that sends the 'hearbeat' which confirms offboard control should be active
 * @file HearbeatNode.cpp
 */

#include "HeartbeatNode.hpp"

#include <chrono>

using namespace std::chrono_literals;
using namespace px4_msgs::msg;

HeartbeatNode::HeartbeatNode() : Node("fc_hearbeat") {
    offboard_control_mode_publisher_ = this->create_publisher<OffboardControlMode>("/fmu/in/offboard_control_mode", 10);
    
    auto timer_callback = [this]() -> void {
    };

    timer_ = this->create_wall_timer(100ms, timer_callback);
}

int main(int argc, char *argv[]) {

    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<HeartbeatNode>());
    
    rclcpp::shutdown();
    return 0;
}