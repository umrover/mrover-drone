from setuptools import setup

package_name = 'drone_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    py_modules=[],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/px4_sitl_gz_ros2.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='PX4 SITL simulation package for Gazebo 8.1.0 and ROS 2 bridge.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [],
    },
)
