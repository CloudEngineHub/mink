import mujoco
import mujoco.viewer
import mink
from pathlib import Path
from loop_rate_limiters import RateLimiter
from mink.utils import set_mocap_pose_from_site

_HERE = Path(__file__).parent
_XML = _HERE / "unitree_g1" / "scene.xml"


if __name__ == "__main__":
    model = mujoco.MjModel.from_xml_path(_XML.as_posix())

    configuration = mink.Configuration(model)

    feet = ["right_foot", "left_foot"]
    hands = ["right_palm", "left_palm"]

    tasks = [
        pelvis_orientation_task := mink.FrameTask(
            frame_name="pelvis",
            frame_type="body",
            position_cost=0.0,
            orientation_cost=10.0,
        ),
        posture_task := mink.PostureTask(cost=1e-1),
        com_task := mink.ComTask(cost=200.0),
    ]

    feet_tasks = []
    for foot in feet:
        task = mink.FrameTask(
            frame_name=foot,
            frame_type="site",
            position_cost=200.0,
            orientation_cost=10.0,
            lm_damping=1.0,
        )
        feet_tasks.append(task)
    tasks.extend(feet_tasks)

    hand_tasks = []
    for hand in hands:
        task = mink.FrameTask(
            frame_name=hand,
            frame_type="site",
            position_cost=4.0,
            orientation_cost=0.0,
            lm_damping=1.0,
        )
        hand_tasks.append(task)
    tasks.extend(hand_tasks)

    collision_pairs = [
        # (["wrist_3_link"], ["floor", "wall"]),
        (["wrist_2_link_1", "wrist_2_link_2"], ["floor", "wall"]),
    ]

    limits = [
        mink.ConfigurationLimit(model=model),
        mink.CollisionAvoidanceLimit(model=model, geom_pairs=collision_pairs),
    ]

    com_mid = model.body("com_target").mocapid[0]
    feet_mid = [model.body(f"{foot}_target").mocapid[0] for foot in feet]
    hands_mid = [model.body(f"{hand}_target").mocapid[0] for hand in hands]

    model = configuration.model
    data = configuration.data

    with mujoco.viewer.launch_passive(
        model=model, data=data, show_left_ui=False, show_right_ui=False
    ) as viewer:
        mujoco.mjv_defaultFreeCamera(model, viewer.cam)

        # Initialize to the home keyframe.
        configuration.update_from_keyframe("stand")
        posture_task.set_target_from_configuration(configuration)
        pelvis_orientation_task.set_target_from_configuration(configuration)

        # Initialize mocap bodies at their respective sites.
        for hand, foot in zip(hands, feet):
            set_mocap_pose_from_site(model, data, f"{foot}_target", foot)
            set_mocap_pose_from_site(model, data, f"{hand}_target", hand)
        data.mocap_pos[com_mid] = data.subtree_com[1]

        rate = RateLimiter(frequency=500.0)
        vel = None
        while viewer.is_running():
            # Update task targets.
            com_task.set_target_from_mocap(data, com_mid)
            for i, (hand_task, foot_task) in enumerate(zip(hand_tasks, feet_tasks)):
                foot_task.set_target_from_mocap(data, feet_mid[i])
                hand_task.set_target_from_mocap(data, hands_mid[i])

            vel = mink.solve_ik(configuration, tasks, limits, rate.dt, 1e-1, vel)
            configuration.integrate_inplace(vel, rate.dt)

            # Visualize at fixed FPS.
            viewer.sync()
            rate.sleep()
