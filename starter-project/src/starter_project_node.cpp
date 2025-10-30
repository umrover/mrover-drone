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
static const std::string kNodeName = "starter_project_node";

class StarterProject : public px4_ros2::ModeBase 
{
public:
    explicit StarterProject(rclcpp::Node & node)
    : ModeBase(node, kNodeName)
    {
        // TODO: Initialize the _goto_setpoint, _vehicle_global_position, and
        // _vehicle_local_position shared pointers here.
        _goto_setpoint = std::make_shared<px4_ros2::GotoGlobalSetpointType>(*this);
        _vehicle_global_position = std::make_shared<px4_ros2::OdometryGlobalPosition>(*this);
        _vehicle_local_position = std::make_shared<px4_ros2::OdometryLocalPosition>(*this);

        // TODO: Define some interesting setpoints to fly to.
        _setpoints = {
            {-10.0F,0.0F,10.0F},
            {-10.0F,10.0F,10.0F},
            {0.0F,10.0F,10.0F},
            {0.0F,0.0F,10.0F}
        };
    }

    void onActivate() override {
    }
    void onDeactivate() override {}


    bool positionReached(const Eigen::Vector3d & target_position, float threshold = 0.1f) {
        // TODO: Use _vehicle_global_position->position() to get the current position
        // and use px4_ros2::horizontalDistanceToGlobalPosition to check if the distance
        // to target_position is less than threshold.

        // std::vector<Eigen::Vector3f> current_pos = _vehicle_global_position->position();
        float distance = px4_ros2::horizontalDistanceToGlobalPosition(_vehicle_global_position->position(),target_position);
        return (distance < threshold);
    }

    void updateSetpoint(float dt_s) override
    {

        // If the starting setpoint has not been set yet, _starting_setpoint
        // should be set to the current global position of the vehicle.
        if (!_starting_setpoint_set) {
            // TODO: Set the _starting_setpoint variable to the current global position
            // of the vehicle
            _starting_setpoint = _vehicle_global_position->position();
            _starting_setpoint_set = true;
        }

        // TODO: Get the current position.
        Eigen::Vector3d current_position = _vehicle_global_position->position();
        

        switch (state) {
            // When we first start, get the starting position
            case State::SettlingAtStart: {

                // TODO: Check if the vehicle has reached the starting setpoint
                // using positionReached(). If it has, transition to the
                // FollowingSetpoints state.
                if(positionReached(_starting_setpoint)){
                    state = State::FollowingSetpoints;
                }
                break;
            }

            // Now, we follow setpoints.
            case State::FollowingSetpoints: {
                
                // TODO: Compute the current setpoint by adding the current vector
                // from _setpoints to _starting_setpoint using
                // px4_ros2::addVectorToGlobalPosition.
                Eigen::Vector3d current_setpoint = px4_ros2::addVectorToGlobalPosition(_starting_setpoint, _setpoints[_setpoint_index]);

                
                // TODO: Use px4_ros2::horizontalDistanceToGlobalPosition to compute
                // the distance to the current setpoint.
                float distance_to_setpoint = px4_ros2::horizontalDistanceToGlobalPosition(current_position,current_setpoint);

                if (distance_to_setpoint < 0.1f) {
                    // TODO: Increment the _setpoint_index - keep in mind we
                    // only have 4 setpoints.
                    _setpoint_index = (++_setpoint_index)%4;
                    // ----

                    RCLCPP_INFO(node().get_logger(),
                        "Reached setpoint %d, moving to next setpoint: <%f, %f, %f>",
                        _setpoint_index,
                        _setpoints[_setpoint_index].x(),
                        _setpoints[_setpoint_index].y(),
                        _setpoints[_setpoint_index].z());

                    
                }
                
                // TODO: Calculate the target heading using
                // px4_ros2::headingToGlobalPosition.
                float target_heading = px4_ros2::headingToGlobalPosition(current_position,current_setpoint);
                // TODO: Update the desired drone position using _goto_setpoint->update.
                // However, if the distance to the setpoint is less than 1.0f,
                // do not specify a heading. At close distances, the heading 
                // calculation can give an undefined result.
                if(distance_to_setpoint<1.0f)
                    _goto_setpoint->update(current_setpoint);
                else
                    _goto_setpoint->update(current_position, target_heading);
                   
                break;
                }
        }
        // TODO: Increment the time_ctr variable by dt_s.
        time_ctr+=dt_s;
    }

private:
    float time_ctr = 0.0f;

    std::shared_ptr<px4_ros2::GotoGlobalSetpointType> _goto_setpoint;
    std::shared_ptr<px4_ros2::OdometryGlobalPosition> _vehicle_global_position;
    std::shared_ptr<px4_ros2::OdometryLocalPosition> _vehicle_local_position;

    Eigen::Vector3d _starting_setpoint;
    bool _starting_setpoint_set = false;

    unsigned int _setpoint_index = 0;

    std::vector<Eigen::Vector3f> _setpoints;

    enum class State {
        SettlingAtStart,
        FollowingSetpoints
    };

    State state = State::SettlingAtStart;

};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<px4_ros2::NodeWithMode<StarterProject>>(kNodeName, true);
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}