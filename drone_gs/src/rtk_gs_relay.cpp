#include <rclcpp/rclcpp.hpp>
#include <rtcm_msgs/msg/message.hpp>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>

class RTKGSRelayNode : public rclcpp::Node {
public:
    RTKGSRelayNode() : Node("rtk_gs_relay_node"), socket_fd_(-1) {
        this->declare_parameter<std::string>("drone_ip", "192.168.1.150");
        this->declare_parameter<int>("udp_port", 13370);

        std::string drone_ip = this->get_parameter("drone_ip").as_string();
        int udp_port = this->get_parameter("udp_port").as_int();

        // setup UDP socket
        socket_fd_ = socket(AF_INET, SOCK_DGRAM, 0);
        std::memset(&drone_addr_, 0, sizeof(drone_addr_));
        drone_addr_.sin_family = AF_INET;
        drone_addr_.sin_port = htons(udp_port);
        inet_pton(AF_INET, drone_ip.c_str(), &drone_addr_.sin_addr);

        sub_ = this->create_subscription<rtcm_msgs::msg::Message>(
            "rtcm", 10,
            std::bind(&RTKGSRelayNode::rtcmCallback, this, std::placeholders::_1)
        );

        RCLCPP_INFO(this->get_logger(), "Relaying 'rtcm' -> UDP to %s:%d",
            drone_ip.c_str(), udp_port);
    }

    ~RTKGSRelayNode() override {
        if ( socket_fd_ >= 0 ) close(socket_fd_);
    }

private:
    void rtcmCallback(const rtcm_msgs::msg::Message::SharedPtr msg) {
        if ( socket_fd_ < 0 || msg->message.empty() ) return;

        // blast raw RTCM bytes
        sendto(socket_fd_, msg->message.data(), msg->message.size(), 0,
            (struct sockaddr*)&drone_addr_, sizeof(drone_addr_));
    }

    int serial_fd_;
    int socket_fd_;
    sockaddr_in drone_addr_{};
    rclcpp::Subscription<rtcm_msgs::msg::Message>::SharedPtr sub_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<RTKGSRelayNode>());
    rclcpp::shutdown();
    return 0;
}
