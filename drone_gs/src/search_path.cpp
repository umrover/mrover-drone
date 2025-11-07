// Demonstration of setpoint tracking for a drone using ROS2 and PX4-ROS2 
// interface library

#include <rclcpp/rclcpp.hpp>
#include <px4_ros2/components/node_with_mode.hpp>
#include <px4_ros2/components/mode.hpp>
#include <px4_ros2/control/setpoint_types/goto.hpp>
#include <px4_ros2/control/peripheral_actuators.hpp>
#include <px4_ros2/odometry/global_position.hpp>
#include <px4_ros2/odometry/local_position.hpp>
#include <px4_ros2/utils/geometry.hpp>
#include <Eigen/Eigen>
#include <vector>

using namespace std::chrono_literals;
static const std::string kNodeName = "setpoint_tracking_demo";

class SetpointTrackingDemo : public px4_ros2::ModeBase 
{
public:
    explicit SetpointTrackingDemo(rclcpp::Node & node)
    : ModeBase(node, kNodeName)
    {
        _goto_setpoint = std::make_shared<px4_ros2::GotoGlobalSetpointType>(*this);
        _vehicle_global_position = std::make_shared<px4_ros2::OdometryGlobalPosition>(*this);
        _vehicle_local_position = std::make_shared<px4_ros2::OdometryLocalPosition>(*this);
    }

    void onActivate() override {
    }
    void onDeactivate() override {}

    void updateSetpoint(float dt_s) override
    {

        if (!_starting_setpoint_set) {
            _starting_setpoint = _vehicle_global_position->position();
            RCLCPP_INFO(node().get_logger(), 
                "Current Global Position: <%f, %f, %f>",
                _starting_setpoint.x(), _starting_setpoint.y(), _starting_setpoint.z());
            _starting_setpoint_set = true;
        }


        
        auto current_position = _vehicle_global_position->position();
        
        switch (state) {
            case State::SettlingAtStart: {
                if (positionReached(_starting_setpoint, 0.1f)) {
                    state = State::FollowingSetpoints;
                    RCLCPP_INFO(node().get_logger(), "Settling at start complete, moving to setpoints.");
                } else {
                    RCLCPP_INFO(node().get_logger(), "Waiting for drone to settle at start position.");
                    return; // Wait until the drone settles
                }
                break;
            }
            case State::FollowingSetpoints: {
                    
                auto current_setpoint = px4_ros2::addVectorToGlobalPosition(
                    _starting_setpoint, _setpoints[_setpoint_index]);

                
                float distance_to_setpoint = px4_ros2::horizontalDistanceToGlobalPosition(current_position, current_setpoint);

                if (distance_to_setpoint < 0.1f) {
                    _setpoint_index++;
                    if (_setpoint_index >= _setpoints.size()) {
                        _setpoint_index = 0; // Loop back to the first setpoint
                    }
                    RCLCPP_INFO(node().get_logger(),
                        "Reached setpoint %d, moving to next setpoint: <%f, %f, %f>",
                        _setpoint_index,
                        _setpoints[_setpoint_index].x(),
                        _setpoints[_setpoint_index].y(),
                        _setpoints[_setpoint_index].z());
                }
                
                float target_heading = px4_ros2::headingToGlobalPosition(
                    current_position, current_setpoint);

                _goto_setpoint->update({(float)current_setpoint.x(),
                                        (float)current_setpoint.y(),
                                        (float)current_setpoint.z()}, target_heading);
                   
                break;
                }
        }
        
        time_ctr += dt_s;
    }

private:
    float time_ctr = 0.0f;
    std::shared_ptr<px4_ros2::GotoGlobalSetpointType> _goto_setpoint;
    std::shared_ptr<px4_ros2::OdometryGlobalPosition> _vehicle_global_position;
    std::shared_ptr<px4_ros2::OdometryLocalPosition> _vehicle_local_position;

    Eigen::Vector3d _starting_setpoint;
    bool _starting_setpoint_set = false;

    unsigned int _setpoint_index = 0;
    std::vector<Eigen::Vector3f> _setpoints = {
        {20.0f, 0.0f, 0.0f}, // Example setpoint 1
        {20.0f, 20.0f, 0.0f}, // Example setpoint 2
        {0.0f, 20.0f, 0.0f}, // Example setpoint 2
        {0.0f, 0.0f, 0.0f} // Example setpoint 3
    }; // Store setpoints

    enum class State {
        SettlingAtStart,
        FollowingSetpoints
    };

    State state = State::SettlingAtStart;

    bool positionReached(const Eigen::Vector3d & target_position, float threshold = 0.1f) {
        return px4_ros2::horizontalDistanceToGlobalPosition(
            _vehicle_global_position->position(), target_position) < threshold;
    }
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<px4_ros2::NodeWithMode<SetpointTrackingDemo>>(kNodeName, true);
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
