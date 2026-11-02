#include <rclcpp/rclcpp.hpp>
#include <mavros_msgs/msg/rtcm.hpp>

#include <sys/socket.h>
#include <netinet/in.h>
#include <fcntl.h>

class RTKReceiverNode : public rclcpp::Node {
public:
    RTKReceiverNode() : Node("rtk_receiver_node"), socket_fd_(-1) {
        // declaring ROS2 params allows for commands like --ros-args -p udp_port:=15000 to edit them
        // default UDP RTCM input port for QGroundControl
        this->declare_parameter<int>("udp_port", 13370);
        this->declare_parameter<std::string>("rtcm_topic", "/mavros/gps_rtk/send_rtcm");

        int udp_port = this->get_parameter("udp_port").as_int();
        std::string rtcm_topic = this->get_parameter("rtcm_topic").as_string();

        // send RTCM msgs with queue of size 10
        rtcm_pub_ = this->create_publisher<mavros_msgs::msg::RTCM>(rtcm_topic, 10);

        // create IPv4 UDP socket
        socket_fd_ = socket(AF_INET, SOCK_DGRAM, 0);
        // O_NONBLOCK to return if no data found in socket (non-blocking socket)
        fcntl(socket_fd_, F_SETFL, fcntl(socket_fd_, F_GETFL, 0) | O_NONBLOCK);

        // struct holding IP addresses and port config
        sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_addr.s_addr = INADDR_ANY; // all network cards
        server_addr.sin_port = htons(udp_port); // convert 13370 to network byte order

        // claim port 13370
        if (bind(socket_fd_, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            RCLCPP_ERROR(this->get_logger(), "Failed to bind UDP socket to port %d\n", udp_port);
            return;
        }

        RCLCPP_INFO(this->get_logger(), "RTK receiver listening to UDP port %d\n", udp_port);

        // fast polling
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(20),
            std::bind(&RTKReceiverNode::readAndPublish, this)
        );
    }

    ~RTKReceiverNode() override {
        if (socket_fd_ >= 0) close(socket_fd_);
    }

private:
    void readAndPublish() {
        if (socket_fd_ < 0) return;

        uint8_t buffer[2048];
        while (true) {
            ssize_t bytes_read = recvfrom(socket_fd_, buffer, sizeof(buffer), 0, nullptr, nullptr);
            if (bytes_read > 0) {
                auto msg = mavros_msgs::msg::RTCM();
                msg.header.stamp = this->now();
                msg.header.frame_id = "base_link";
                // copy raw bytes directly to ROS msg without parsing/modifying
                msg.data.assign(buffer, buffer + bytes_read);
                // send to mavros
                rtcm_pub_->publish(msg);
            } else {
                break;
            }
        }
    }

    int socket_fd_;
    rclcpp::Publisher<mavros_msgs::msg::RTCM>::SharedPtr rtcm_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<RTKReceiverNode>());
    rclcpp::shutdown();
    return 0;
}
