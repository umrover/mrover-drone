#include <cmath>
#include <cstddef>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <mavros_msgs/msg/state.hpp>
#include <mavros_msgs/srv/command_bool.hpp>
#include <mavros_msgs/srv/set_mode.hpp>
#include <rclcpp/rclcpp.hpp>

using namespace std::chrono_literals;

class StarterProjectMavros final : public rclcpp::Node
{
public:
    StarterProjectMavros()
        : Node("starter_project_mavros_node")
    {
        /**
         * These are all variables useful for our Node. Feel free to explore what changing them does to the program.
         */
        mavros_prefix_ = declare_parameter<std::string>(
            "mavros_prefix", "mavros/mavros");
        mavros_plugin_prefix_ = declare_parameter<std::string>(
            "mavros_plugin_prefix", "mavros/mavros");
        auto_offboard_ = declare_parameter<bool>("auto_offboard", false);
        auto_arm_ = declare_parameter<bool>("auto_arm", false);
        setpoint_rate_hz_ = declare_parameter<double>("setpoint_rate_hz", 20.0);
        position_tolerance_m_ = declare_parameter<double>("position_tolerance_m", 0.15);
        // Each waypoint is an x, y, z offset from the starting position.
        waypoints_ = {
            {2.0, 0.0, 0.0},
            {2.0, 2.0, 0.0},
            {0.0, 2.0, 0.0},
            {0.0, 0.0, 0.0},
        };

        if (setpoint_rate_hz_ <= 2.0) {
            throw std::invalid_argument("setpoint_rate_hz must be greater than 2 Hz");
        }

        /**
         * This is a subscription. This means that this Node will carry out some functions here
         * when it receives data from the mavros_msgs/state node. In this case, that node publishes 
         * the state (an object with various variables) that the drone is currently in whenever it changes. 
         * We mainly care abut the mode (is it offboard?), whether the drone is armed, 
         * and whether the node is connected to the drone.
         * 
        */
        state_subscription_ = create_subscription<mavros_msgs::msg::State>(
            mavros_prefix_ + "/state",
            rclcpp::QoS(10).reliable().transient_local(),
            std::bind(&StarterProjectMavros::stateCallback, this, std::placeholders::_1));

            /**
             * Implement the pose_subscription. This subscription should call poseCallback
             * to update the position of the drone stored within the node. Use the state_subscription
             * as a guideline for this subscription
             */
        pose_subscription_ = create_subscription<geometry_msgs::msg::PoseStamped>(
            /**
             * This specifies the name of the node. If you are ever unsure, you can use ROS commands to see the active nodes.
             */
            mavros_plugin_prefix_ + "/local_position/pose",
        
            /**
             * This line determines how sensitive the data from the subscription is.
             * In this case, we prioritize the newest sensor data over getting every update.
             */
             
            rclcpp::SensorDataQoS(),

            //TODO: Bind this subscription to the poseCallback function. Then, implement the poseCallback function.

            std::bind(&StarterProjectMavros::poseCallback, this, std::placeholders::_1));

        //This sends the setpoint to MAVROS, which handles sending the drone to the setpoint.
        setpoint_publisher_ = create_publisher<geometry_msgs::msg::PoseStamped>(
            mavros_plugin_prefix_ + "/setpoint_position/local", 10);

        mode_client_ = create_client<mavros_msgs::srv::SetMode>(
            mavros_plugin_prefix_ + "/set_mode");
        arm_client_ = create_client<mavros_msgs::srv::CommandBool>(
            mavros_plugin_prefix_ + "/cmd/arming");




        
        const auto timer_period = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::duration<double>(1.0 / setpoint_rate_hz_));

        //This defines a timer where after each timer period, the timerCallback function is called.
        timer_ = create_wall_timer(
            timer_period,
            std::bind(&StarterProjectMavros::timerCallback, this));
        
        RCLCPP_INFO(
            get_logger(),
            "MAVROS offboard node started; auto_offboard=%s, auto_arm=%s",
            auto_offboard_ ? "true" : "false",
            auto_arm_ ? "true" : "false");
    }

private:
    //A struct is a type of class that holds multiple variables, in this case an x, y, and z coordinate. 
    struct Waypoint
    {
        double x;
        double y;
        double z;
    };

    using Pose = geometry_msgs::msg::PoseStamped;
    using State = mavros_msgs::msg::State;

    //This is called every time the stateCallback 
    void stateCallback(const State::SharedPtr message)
    {
        state_ = *message;
    }
    //Every time the pose(drone location) is updated this function is called.
    void poseCallback(const Pose::SharedPtr message)
    {
        //Updates the pose stored in the node to the received pose
        current_pose_ = *message;
        //Verifies that we have received a pose before
        pose_received_ = true;

        //If we have never set a pose before
        if (!start_pose_set_) {
            //Set the start pose to the first pose received
            start_pose_ = *message;
            //Set the target as the start pose (this allows the drone to be stationary before following points)
            target_pose_ = start_pose_;
            //Keeps track that the start pose has been set
            start_pose_set_ = true;
            RCLCPP_INFO(get_logger(), "Received the starting local position");
        }
    }

    //Every timerPeriod this function is called
    void timerCallback()
    {
        //If the node doesn't have the drone's position, nothing happens
        if (!pose_received_) {
            RCLCPP_WARN_THROTTLE(
                get_logger(), *get_clock(), 5000,
                "Waiting for %s/local_position/pose", mavros_plugin_prefix_.c_str());
            return;
        }
        //Publishes (sends to MAVROS) the current target setpoint.
        publishTarget();
        //If the node isn't able to control the drone, nothing happens
        if (!state_.connected) {
            RCLCPP_WARN_THROTTLE(
                get_logger(), *get_clock(), 5000,
                "Waiting for MAVROS to connect to the flight controller");
            return;
        }

        // PX4 requires a stream of setpoints before accepting OFFBOARD.
        if (warmup_cycles_ < kWarmupCycles) {
            ++warmup_cycles_;
            return;
        }

        //To operate the drone through this node, it needs to be granted offboard control. This call requests offboard control from PX4.
        if (auto_offboard_ && state_.mode != "OFFBOARD") {
            requestOffboard();
            return;
        }
        //Arming the drone means allowing the motors to be enabled. If we have offboard control but the drone is not armed, we request to arm it.
        if (auto_arm_ && state_.mode == "OFFBOARD" && !state_.armed) {
            requestArming();
            return;
        }
        //If the node is granted offboard control and armed, we can send setpoints
        if (state_.mode == "OFFBOARD" && state_.armed) {
            updateTargetIfReached();
        }
    }

        //This sends the target location held in the Node 
    void publishTarget()
    {
        target_pose_.header.stamp = now();
        target_pose_.header.frame_id = "map";
        setpoint_publisher_->publish(target_pose_);
    }

    //This function checks if the drone has arrived at its target and should now target the next setpoint
    void updateTargetIfReached()
    {
        //TODO: 1. Calculate the values dx, dy, dz. 
        // 2. calculate the distance from the target setpoint
        // 3. This distance is used to determine whether we are close enough to the target to change to the next setpoint

        const double dx = current_pose_.pose.position.x - target_pose_.pose.position.x;
        const double dy = current_pose_.pose.position.y - target_pose_.pose.position.y;
        const double dz = current_pose_.pose.position.z - target_pose_.pose.position.z;
        const double distance = std::sqrt(dx * dx + dy * dy + dz * dz);

        if (distance > position_tolerance_m_) {
            return;
        }

        //this ensures that if we have not initialized a target that we set the waypoint to the first target instead of incrementing.
        if (!target_initialized_) {
            waypoint_index_ = 0;
            target_initialized_ = true;
        } else {
            waypoint_index_ = (waypoint_index_ + 1) % waypoints_.size();
        }

        //Sets the target equal to the waypoint in the array that we want
        const Waypoint & waypoint = waypoints_[waypoint_index_];
        target_pose_ = start_pose_;
        target_pose_.pose.position.x += waypoint.x;
        target_pose_.pose.position.y += waypoint.y;
        target_pose_.pose.position.z += waypoint.z;

        RCLCPP_INFO(
            get_logger(),
            "Reached waypoint; moving to point %zu of %zu",
            waypoint_index_ + 1,
            waypoints_.size());
    }

    void requestOffboard()
    {
        if (request_cooldown_cycles_ > 0) {
            --request_cooldown_cycles_;
            return;
        }

        if (!mode_client_->service_is_ready()) {
            return;
        }

        auto request = std::make_shared<mavros_msgs::srv::SetMode::Request>();
        request->custom_mode = "OFFBOARD";
        mode_client_->async_send_request(request);
        request_cooldown_cycles_ = kRequestCooldownCycles;
        RCLCPP_INFO(get_logger(), "Requesting OFFBOARD mode");
    }

    void requestArming()
    {
        if (request_cooldown_cycles_ > 0) {
            --request_cooldown_cycles_;
            return;
        }

        if (!arm_client_->service_is_ready()) {
            return;
        }

        auto request = std::make_shared<mavros_msgs::srv::CommandBool::Request>();
        request->value = true;
        arm_client_->async_send_request(request);
        request_cooldown_cycles_ = kRequestCooldownCycles;
        RCLCPP_INFO(get_logger(), "Requesting arming");
    }

    static constexpr std::size_t kWarmupCycles = 100;
    static constexpr int kRequestCooldownCycles = 40;

    std::string mavros_prefix_;
    std::string mavros_plugin_prefix_;
    bool auto_offboard_ = false;
    bool auto_arm_ = false;
    double setpoint_rate_hz_ = 20.0;
    double position_tolerance_m_ = 0.15;

    State state_;
    Pose current_pose_;
    Pose start_pose_;
    Pose target_pose_;
    bool pose_received_ = false;
    bool start_pose_set_ = false;
    bool target_initialized_ = false;
    std::size_t warmup_cycles_ = 0;
    std::size_t waypoint_index_ = 0;
    int request_cooldown_cycles_ = 0;

    // MAVROS uses ENU local coordinates: x=east, y=north, z=up.
    std::vector<Waypoint> waypoints_;

    rclcpp::Subscription<State>::SharedPtr state_subscription_;
    rclcpp::Subscription<Pose>::SharedPtr pose_subscription_;
    rclcpp::Publisher<Pose>::SharedPtr setpoint_publisher_;
    rclcpp::Client<mavros_msgs::srv::SetMode>::SharedPtr mode_client_;
    rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedPtr arm_client_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<StarterProjectMavros>());
    rclcpp::shutdown();
    return 0;
    
}
