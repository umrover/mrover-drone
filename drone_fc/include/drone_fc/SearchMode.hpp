
#include "rclcpp/rclcpp.hpp"
#include <px4_ros2/components/mode.hpp>
#include <px4_ros2/control/setpoint_types/goto.hpp>
#include <px4_ros2/odometry/local_position.hpp>

#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Geometry>

#define M_PI_2 1.57079632679489661923

// Super Simple Square Search Mode 
class SearchMode : public px4_ros2::ModeBase {
    public:
        explicit SearchMode(rclcpp::Node &node);

        void onActivate() override;
        void onDeactivate() override;
        void updateSetpoint(float dt_s) override;

    private:

        bool positionReached(Eigen::Vector3f &targetPosition);
        void nextSpiralTarget();

        Eigen::Matrix3f make90DegreeRotation() const;

        enum class State {
            SettlingAtStart = 0,
            InTransit,
            CompletedSearch
        } _state;

        Eigen::Vector3f _start_position;
        Eigen::Vector3f _delta_vector;

        // Eigen::AngleAxisf _rotation(0.5*M_PI, Eigen::Vector3f::UnitZ()).toR;
        // const Eigen::AngleAxisf _rotation = make90DegreeRotation();
        const Eigen::Matrix3f _rotation = make90DegreeRotation();

        uint32_t _spiral_idx;
        Eigen::Vector3f _target_position;

        std::shared_ptr<px4_ros2::GotoSetpointType> _goto_setpoint;
        std::shared_ptr<px4_ros2::OdometryLocalPosition> _vehicle_local_position;

        bool _start_position_set;
};
