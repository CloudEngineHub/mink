import mujoco


def set_mocap_pose_from_site(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    mocap_name: str,
    site_name: str,
):
    mocap_id = model.body(mocap_name).mocapid[0]
    site_id = data.site(site_name).id
    data.mocap_pos[mocap_id] = data.site_xpos[site_id]
    mujoco.mju_mat2Quat(data.mocap_quat[mocap_id], data.site_xmat[site_id])


def set_mocap_pose_from_body(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    mocap_name: str,
    body_name: str,
):
    mocap_id = model.body(mocap_name).mocapid[0]
    body_id = data.body(body_name).id
    data.mocap_pos[mocap_id] = data.xpos[body_id]
    mujoco.mju_mat2Quat(data.mocap_quat[mocap_id], data.xmat[body_id])
