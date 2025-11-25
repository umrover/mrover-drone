from setuptools import setup

package_name = 'drone_gs'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Drone ground station with camera publisher',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # This line is the important one:
            'camera_publisher = drone_gs.camera_publisher:main',
            'camera_subscriber = drone_gs.camera_subscriber:main'
        ],
    },
)
