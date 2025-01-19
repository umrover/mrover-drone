/**
 * @brief Node that sends the 'hearbeat' which confirms offboard control should be active
 * @file HearbeatNode.hpp
 */

#include <rclcpp/rclcpp.hpp>

#include <px4_msgs/msg/vehicle_command.hpp>
#include <px4_msgs/msg/vehicle_control_mode.hpp>
#include <px4_msgs/msg/offboard_control_mode.hpp>


using namespace px4_msgs::msg;

class HeartbeatNode : public rclcpp::Node {
    public:
    HeartbeatNode();


    private:
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<OffboardControlMode>::SharedPtr offboard_control_mode_publisher_;


    void publish_offboard_control_mode();
};
