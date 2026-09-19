# Sets a minimum CMake version and defines the project name.
cmake_minimum_required(VERSION 3.10)
project(starter-project)

# Sets C++ standard - in this case C++17, but can also be C++ 11, 14, 20, etc.
if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

# Add compiler warnings
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find package dependencies for our project
find_package(ament_cmake REQUIRED)
# TODO: add similar find_package calls for each dependency in package.xml
#   We need a find_package for each <build_depend>, <buildtool_depend>, and
#   <exec_depend> dependency from package.xml.

# Adds directories for header files.
include_directories(include ${Eigen3_INCLUDE_DIRS})
 
# Specifies an executable to build.
add_executable(starter_project_node
        src/starter_project_node.cpp)     

# TODO: Add the rest of the dependencies
ament_target_dependencies(starter_project_node Eigen3
    # We need 2 more dependencies
)

# Install executables to the correct directory.
install(TARGETS
        starter_project_node
        DESTINATION lib/${PROJECT_NAME})

# Install launch files to the correct directory.
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Enable testing
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Creates the 'ament' package. ament is a wrapper around CMake used in ROS2.
ament_package()
