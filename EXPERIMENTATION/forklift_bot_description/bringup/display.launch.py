from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from ros_gz_sim.actions import GzServer
from ros_gz_sim.actions.gz_spawn_model import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ros_gz_bridge.actions.ros_gz_bridge import RosGzBridge 
import os

def generate_launch_description():
    pkg_share = FindPackageShare(package='forklift_bot_description').find('forklift_bot_description')
    default_model_path = os.path.join(pkg_share, 'include', 'forklift_bot_description', 'forklift.sdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz', 'forklift.rviz')
    bridge_config_path = os.path.join(pkg_share, 'config', 'forklift_bridge_config.yaml')
    world_path = os.path.join(pkg_share, 'world', 'forklift_world.sdf')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    robot_controllers = os.path.join(pkg_share, 'config', 'lift_controller.yaml')

    robot_state_publisher_node = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[{'robot_description': Command(['xacro ', LaunchConfiguration('model')])}, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster',
                   ],
    )
    joint_trajectory_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_trajectory_controller',
            '--param-file ',
            robot_controllers,
            ],
    )

    gz_server = GzServer(
    world_sdf_file=world_path,
    container_name='ros_gz_container',
    create_own_container='True',
    use_composition='True',
    )
    ros_gz_bridge = RosGzBridge(
    bridge_name='ros_gz_bridge',
    config_file=bridge_config_path,
    container_name='ros_gz_container',
    create_own_container='False',
    use_composition='True',
    )
    spawn_entity = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_spawn_model.launch.py')),
    launch_arguments={
        'world': 'forklift_world',
        'topic': '/robot_description',
        'entity_name': 'forklift_bot',
        'z':'0.2'
    }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(name='model', default_value=default_model_path, description='Absolute path to robot model file'),
        DeclareLaunchArgument(name='rvizconfig', default_value=default_rviz_config_path, description='Absolute path to rviz config file'),
        DeclareLaunchArgument(name='use_sim_time', default_value='True', description='Flag to enable use_sim_time'),
        ExecuteProcess(cmd=['gz', 'sim', '-g'], output='screen'),
        gz_server,
        ros_gz_bridge,
        spawn_entity,
        robot_state_publisher_node,
        joint_state_broadcaster_spawner,
        joint_trajectory_controller_spawner,
        # lift_node,
        rviz_node
    ])