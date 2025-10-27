#include <string>

#include "rclcpp/rclcpp.hpp"

#include <drone_fc/SearchMode.hpp>
#include <px4_ros2/components/node_with_mode.hpp>

using SearchNode = px4_ros2::NodeWithMode<SearchMode>;

static const std::string kNodeName = "fc_search_mode";
static const bool kEnableDebugOutput = true;
static const uint32_t num_spiral_iterations = 20;

// PUBLIC INTERFACE

SearchMode::SearchMode(rclcpp::Node &node) : ModeBase(node, kNodeName) {
    _goto_setpoint = std::make_shared<px4_ros2::GotoSetpointType>(*this);
    _vehicle_local_position = std::make_shared<px4_ros2::OdometryLocalPosition>(*this);
}

void SearchMode::onActivate() {
    _state = State::SettlingAtStart;
    _start_position_set = false;
    _spiral_idx = 0;
}

void SearchMode::onDeactivate() {}
void SearchMode::updateSetpoint(float dt_s) {
    (void)(dt_s);// unused parameter

    if (!_start_position_set) {
        _start_position = _vehicle_local_position->positionNed();
        _start_position_set = true;
    };

    switch(_state) {
        case State::SettlingAtStart: {
            _goto_setpoint->update(_start_position, 0);
            if (positionReached(_start_position)) {
                nextSpiralTarget();
                _state = State::InTransit;
            }
            break;
        }

        case State::InTransit: {
            _goto_setpoint->update(_target_position, 0); 

            if (positionReached(_target_position)) {
                nextSpiralTarget();

                if (_spiral_idx == num_spiral_iterations) {
                    _state = State::CompletedSearch;
                }
            }

            break;
        }

        case State::CompletedSearch: {
            _goto_setpoint->update(_start_position, 0);

            if (positionReached(_start_position)) {
                completed(px4_ros2::Result::Success);
            }

            break;
        }
    }
}

// PRIVATE METHODS

bool SearchMode::positionReached(Eigen::Vector3f &targetPosition) {
    static constexpr float kPositionErrorThreshold = 0.5;

    const Eigen::Vector3f position_error = targetPosition - _vehicle_local_position->positionNed();

    return (position_error.norm() < kPositionErrorThreshold);
}

void SearchMode::nextSpiralTarget() {
    if (_spiral_idx == 0) {
        _delta_vector = Eigen::Vector3f(1., 0, 0);
        _target_position = _start_position;
    } else {
        // rotate and scale _delta_vector
        _delta_vector = _rotation * _delta_vector;
        _delta_vector = _delta_vector.normalized() * (1 + _spiral_idx / 2);
    }

    _target_position = _target_position + _delta_vector;

    _spiral_idx += 1;
}

// constexpr to make a 90 degree rotation matrix
Eigen::Matrix3f SearchMode::make90DegreeRotation() const {
    Eigen::AngleAxisf rot(M_PI_2, Eigen::Vector3f::UnitZ());
    return rot.toRotationMatrix();
}

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SearchNode>(kNodeName, kEnableDebugOutput));
    rclcpp::shutdown();

    return 0;
}