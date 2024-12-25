from mathutils import Quaternion, Euler

from ..utils import *


class FlipBoneOperator(bpy.types.Operator):
    bl_idname = "mmd_kafei_tools.flip_bone"
    bl_label = "翻转姿态"
    bl_description = "翻转姿态"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):
        option = "FLIP_BONE"
        if check_props(self, option) is False:
            return {'FINISHED'}
        mirror_pose()
        return {'FINISHED'}


class DeleteInvalidRigidbodyJointOperator(bpy.types.Operator):
    bl_idname = "mmd_kafei_tools.delete_invalid_rigidbody_joint"
    bl_label = "清理无效刚体Joint"
    bl_description = "清理无效的刚体和关节。如果刚体所关联的骨骼不存在，则删除该刚体及与之关联的关节；如果刚体没有关联的骨骼，则不处理"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):
        option = "INVALID_RIGIDBODY_JOINT"
        if check_props(self, option) is False:
            return {'FINISHED'}
        remove_invalid_rigidbody_joint()
        return {'FINISHED'}


class SelectPhysicalBoneOperator(bpy.types.Operator):
    bl_idname = "mmd_kafei_tools.select_physical_bone"
    bl_label = "物理骨骼"
    bl_description = "选择受物理影响的MMD骨骼"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):
        option = "PHYSICAL_BONE"
        if check_props(self, option) is False:
            return {'FINISHED'}
        select_physical_bone()
        return {'FINISHED'}


class SelectBakeBoneOperator(bpy.types.Operator):
    bl_idname = "mmd_kafei_tools.select_bake_bone"
    bl_label = "K帧骨骼"
    bl_description = "选择用于K帧的MMD骨骼"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):
        option = "BAKE_BONE"
        if check_props(self, option) is False:
            return {'FINISHED'}
        select_bake_bone()
        return {'FINISHED'}


class SelectLinkedBoneOperator(bpy.types.Operator):
    bl_idname = "mmd_kafei_tools.select_linked_bone"
    bl_label = "关联骨骼"
    bl_description = "选择以父/子关系关联到当前选中项的所有骨骼"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):
        option = "LINKED_BONE"
        if check_props(self, option) is False:
            return {'FINISHED'}
        select_bone_by_input(option)
        return {'FINISHED'}


class SelectRingBoneOperator(bpy.types.Operator):
    bl_idname = "mmd_kafei_tools.select_ring_bone"
    bl_label = "并排骨骼"
    bl_description = "选择当前选中项的环绕骨骼，例如选择裙子骨骼的一周"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):
        option = "RING_BONE"
        if check_props(self, option) is False:
            return {'FINISHED'}
        select_bone_by_input(option)
        return {'FINISHED'}


def check_props(operator, option):
    if option in ("FLIP_BONE", "PHYSICAL_BONE", "BAKE_BONE", "LINKED_BONE", "RING_BONE", "INVALID_RIGIDBODY_JOINT"):
        active_object = bpy.context.active_object
        if not active_object:
            operator.report(type={'ERROR'}, message=f'请选择MMD模型！')
            return False
        pmx_root = find_pmx_root_with_child(active_object)
        if not pmx_root:
            operator.report(type={'ERROR'}, message=f'请选择MMD模型！')
            return False
        armature = find_pmx_armature(pmx_root)
        if not armature:
            operator.report(type={'ERROR'}, message=f'模型缺少骨架！')
            return False

        if option in ("FLIP_BONE"):
            selected_pbs = []
            pbs = armature.pose.bones
            for pb in pbs:
                if pb.bone.select:
                    selected_pbs.append(pb)
            if not selected_pbs:
                operator.report(type={'ERROR'}, message=f'请至少选择一根骨骼！')
                return False

            lr = ""
            for pb in selected_pbs:
                # 去除.xxx后缀
                basename = re.sub(r'\.\d+$', '', pb.name)
                # 去除LR
                if basename.endswith(('.L', '.R', '.l', '.r', '_L', '_R', '_l', '_r')):
                    curr_lr = basename[-1].lower()
                    print(curr_lr)
                    if not lr:
                        lr = curr_lr
                    else:
                        if curr_lr != lr:
                            operator.report(type={'ERROR'}, message=f'请选择单侧骨骼！')
                            return False
        return True


def traverse_parent(pb, pb_set):
    parent = pb.parent
    if parent:
        # 如果父骨骼只有一个子骨骼，将其添加到列表
        if len(parent.children) == 1:
            pb_set.add(parent)
            traverse_parent(parent, pb_set)  # 继续递归父骨骼
        # 否则结束递归
        else:
            return


def traverse_children(pb, pb_set):
    if len(pb.children) != 1:
        return
    do_traverse_children(pb, pb_set)


def do_traverse_children(pb, pb_set):
    # 如果子骨骼只有一个子骨骼，将其添加到列表
    child = pb.children[0]
    if len(child.children) == 1:
        pb_set.add(child)
        traverse_children(child, pb_set)  # 继续递归子骨骼
    else:
        pb_set.add(child)
        return


def get_ring_bone(selected_pbs, pbs, pb_set):
    prefix_set = set()
    for pb in selected_pbs:
        prefix = get_prefix(pb.name)
        if prefix:
            prefix_set.add(prefix)

    for pb in pbs:
        prefix = get_prefix(pb.name)
        if prefix in prefix_set:
            pb_set.add(pb)


def get_prefix(bl_name):
    # 去除.xxx后缀
    basename = re.sub(r'\.\d+$', '', bl_name)
    # 去除LR
    if basename.endswith(('.L', '.R', '.l', '.r', '_L', '_R', '_l', '_r')):
        basename = basename[:-2]
    # 提取数字
    match = re.search(r'_(\d+)_(\d+)$', basename)
    if match:
        number1 = match.group(1)
        number2 = match.group(2)
        suffix = "_" + number1 + "_" + number2
        part_name = basename.replace(suffix, "")
        prefix = part_name + "_" + number1 + "_"
        return prefix
    return None


matmul = (lambda a, b: a * b) if bpy.app.version < (2, 80, 0) else (lambda a, b: a.__matmul__(b))


class BoneConverter:
    def __init__(self, pose_bone, scale, invert=False):
        mat = pose_bone.bone.matrix_local.to_3x3()
        mat[1], mat[2] = mat[2].copy(), mat[1].copy()
        self.__mat = mat.transposed()
        self.__scale = scale
        if invert:
            self.__mat.invert()
        self.convert_interpolation = _InterpolationHelper(self.__mat).convert

    def convert_location(self, location):
        return matmul(self.__mat, Vector(location)) * self.__scale

    def convert_rotation(self, rotation_xyzw):
        rot = Quaternion()
        rot.x, rot.y, rot.z, rot.w = rotation_xyzw
        return Quaternion(matmul(self.__mat, rot.axis) * -1, rot.angle).normalized()


class _InterpolationHelper:
    def __init__(self, mat):
        self.__indices = indices = [0, 1, 2]
        l = sorted((-abs(mat[i][j]), i, j) for i in range(3) for j in range(3))
        _, i, j = l[0]
        if i != j:
            indices[i], indices[j] = indices[j], indices[i]
        _, i, j = next(k for k in l if k[1] != i and k[2] != j)
        if indices[i] != j:
            idx = indices.index(j)
            indices[i], indices[idx] = indices[idx], indices[i]

    def convert(self, interpolation_xyz):
        return (interpolation_xyz[i] for i in self.__indices)


def xyzw_from_rotation_mode(mode):
    # 如果旋转模式是四元数，直接返回
    if mode == 'QUATERNION':
        return lambda xyzw: xyzw

    # 如果旋转模式是坐标轴角度，将其转为四元数
    if mode == 'AXIS_ANGLE':
        def __xyzw_from_axis_angle(xyzw):
            q = Quaternion(xyzw[:3], xyzw[3])
            return [q.x, q.y, q.z, q.w]

        return __xyzw_from_axis_angle

    # 如果旋转模式是轴角（绕xyzw[:3]旋转了xyzw[3]度），将其转为四元数
    def __xyzw_from_euler(xyzw):
        q = Euler(xyzw[:3], xyzw[3]).to_quaternion()
        return [q.x, q.y, q.z, q.w]

    return __xyzw_from_euler


class _MirrorMapper:
    def __init__(self, data_map=None):
        self.__data_map = data_map

    @staticmethod
    def get_location(location):
        return (-location[0], location[1], location[2])

    @staticmethod
    def get_rotation(rotation_xyzw):
        return (rotation_xyzw[0], -rotation_xyzw[1], -rotation_xyzw[2], rotation_xyzw[3])

    @staticmethod
    def get_rotation3(rotation_xyz):
        return (rotation_xyz[0], -rotation_xyz[1], -rotation_xyz[2])


def minRotationDiff(prev_q, curr_q):
    t1 = (prev_q.w - curr_q.w) ** 2 + (prev_q.x - curr_q.x) ** 2 + (prev_q.y - curr_q.y) ** 2 + (
            prev_q.z - curr_q.z) ** 2
    t2 = (prev_q.w + curr_q.w) ** 2 + (prev_q.x + curr_q.x) ** 2 + (prev_q.y + curr_q.y) ** 2 + (
            prev_q.z + curr_q.z) ** 2
    # t1 = prev_q.rotation_difference(curr_q).angle
    # t2 = prev_q.rotation_difference(-curr_q).angle
    return -curr_q if t2 < t1 else curr_q


def getBoneConverter(bone):
    converter = BoneConverter(bone, 0.08)
    mode = bone.rotation_mode
    compatible_quaternion = minRotationDiff

    class _ConverterWrap:
        convert_location = converter.convert_location
        convert_interpolation = converter.convert_interpolation
        if mode == 'QUATERNION':
            convert_rotation = converter.convert_rotation
            compatible_rotation = compatible_quaternion
        elif mode == 'AXIS_ANGLE':
            @staticmethod
            def convert_rotation(rot):
                (x, y, z), angle = converter.convert_rotation(rot).to_axis_angle()
                return (angle, x, y, z)

            @staticmethod
            def compatible_rotation(prev, curr):
                angle, x, y, z = curr
                if prev[1] * x + prev[2] * y + prev[3] * z < 0:
                    angle, x, y, z = -angle, -x, -y, -z
                angle_diff = prev[0] - angle
                if abs(angle_diff) > math.pi:
                    pi_2 = math.pi * 2
                    bias = -0.5 if angle_diff < 0 else 0.5
                    angle += int(bias + angle_diff / pi_2) * pi_2
                return (angle, x, y, z)
        else:
            convert_rotation = lambda rot: converter.convert_rotation(rot).to_euler(mode)
            compatible_rotation = lambda prev, curr: curr.make_compatible(prev) or curr

    return _ConverterWrap


def do_mirror_pose(bone_a, bone_b):
    x, y, z = bone_a.location
    rw, rx, ry, rz = bone_a.rotation_quaternion

    converter = BoneConverter(bone_a, 12.5, invert=True)
    # 将blender位置值转为vmd位置值
    location = converter.convert_location([x, y, z])
    # 将blender旋转值转为vmd旋转值
    get_xyzw = xyzw_from_rotation_mode(bone_a.rotation_mode)
    curr_rot = converter.convert_rotation(get_xyzw([rx, ry, rz, rw]))
    rotation_xyzw = curr_rot[1:] + curr_rot[0:1]
    rotation_xyzw = Quaternion(rotation_xyzw)

    _loc, _rot = _MirrorMapper.get_location, _MirrorMapper.get_rotation
    converter = getBoneConverter(bone_b)
    # 将vmd位置值转为blender位置值
    loc = converter.convert_location(_loc(location))
    # 将vmd旋转值转为blender旋转值
    curr_rot = converter.convert_rotation(_rot(rotation_xyzw))
    bone_b.location = loc
    bone_b.rotation_quaternion = curr_rot

    bone_b.scale = bone_a.scale


def get_mirror_name(bl_name):
    # 获取去除数字拓展后的basename
    basename = re.sub(r'\.\d+$', '', bl_name)
    # 提取数字扩展部分（如果有）
    res = re.search(r'(\.\d+)$', bl_name)
    suffix = res.group(0) if res else ''

    mirror_basename = ''
    if basename[-2:] == ".L":
        mirror_basename = basename[:-2] + ".R"
    elif basename[-2:] == ".l":
        mirror_basename = basename[:-2] + ".r"
    elif basename[-2:] == ".R":
        mirror_basename = basename[:-2] + ".L"
    elif basename[-2:] == ".r":
        mirror_basename = basename[:-2] + ".l"

    mirror_bl_name = mirror_basename + suffix
    return mirror_bl_name


def mirror_pose():
    obj = bpy.context.active_object
    pmx_root = find_pmx_root_with_child(obj)
    armature = find_pmx_armature(pmx_root)

    pbs = armature.pose.bones
    selected_pbs = []
    for pb in pbs:
        if pb.bone.select:
            selected_pbs.append(pb)

    # 没有骨骼被选择则直接返回
    if not selected_pbs:
        return

    for pb in selected_pbs:
        mirror_pb_name = get_mirror_name(pb.name)
        mirror_bone = pbs.get(mirror_pb_name)
        if mirror_bone:
            do_mirror_pose(pb, mirror_bone)


def remove_invalid_rigidbody_joint():
    """清理无效刚体Joint"""
    obj = bpy.context.active_object
    root = find_pmx_root_with_child(obj)
    armature = find_pmx_armature(root)
    rigidbody_parent = find_rigid_body_parent(root)
    joint_parent = find_joint_parent(root)

    # （预先）删除无效关节
    for joint in reversed(joint_parent.children):
        rigidbody1 = joint.rigid_body_constraint.object1
        rigidbody2 = joint.rigid_body_constraint.object2
        if any(r not in rigidbody_parent.children for r in [rigidbody1, rigidbody2]):
            bpy.data.objects.remove(joint, do_unlink=True)

    # 处理刚体
    for rigidbody in reversed(rigidbody_parent.children):
        bl_name = rigidbody.mmd_rigid.bone
        # 当刚体没有关联的骨骼时，可能是本身设置错误，也可能是本来就没有关联的骨骼，这里不处理
        if not bl_name:
            continue
        # 关联骨骼不存在则删除这个刚体
        if bl_name not in armature.pose.bones:
            bpy.data.objects.remove(rigidbody, do_unlink=True)

    for joint in reversed(joint_parent.children):
        rigidbody1 = joint.rigid_body_constraint.object1
        rigidbody2 = joint.rigid_body_constraint.object2
        if not rigidbody1 or not rigidbody2:
            bpy.data.objects.remove(joint, do_unlink=True)


def select_physical_bone():
    """选择物理骨骼"""
    obj = bpy.context.active_object
    root = find_pmx_root_with_child(obj)
    armature = find_pmx_armature(root)
    bl_names = get_physical_bone(root)
    # 选中骨架并进入姿态模式
    deselect_all_objects()
    show_object(armature)
    select_and_activate(armature)
    bpy.ops.object.mode_set(mode='POSE')
    for bone in armature.pose.bones:
        if bone.name in bl_names:
            bone.bone.select = True
        else:
            bone.bone.select = False


def select_bake_bone():
    """选择用于烘焙VMD的骨骼"""
    obj = bpy.context.active_object
    pmx_root = find_pmx_root_with_child(obj)
    armature = find_pmx_armature(pmx_root)
    # 选中骨架并进入姿态模式
    deselect_all_objects()
    show_object(armature)
    select_and_activate(armature)
    bpy.ops.object.mode_set(mode='POSE')
    for bone in armature.pose.bones:
        if bone.mmd_bone.name_j in PMX_BAKE_BONES:
            bone.bone.select = True
        else:
            bone.bone.select = False


def select_bone_by_input(option):
    """根据用户所选择的骨骼，来选择option相关骨骼"""
    obj = bpy.context.active_object
    pmx_root = find_pmx_root_with_child(obj)
    armature = find_pmx_armature(pmx_root)
    # 选中骨架并进入姿态模式
    deselect_all_objects()
    show_object(armature)
    select_and_activate(armature)
    bpy.ops.object.mode_set(mode='POSE')

    pbs = armature.pose.bones
    selected_pbs = []
    for pb in pbs:
        if pb.bone.select:
            selected_pbs.append(pb)

    # 没有骨骼被选择则直接返回
    if not selected_pbs:
        return

    if option == "MIRROR_BONE":
        bpy.ops.pose.select_mirror(only_active=False, extend=True)
        return

    active_pb = None
    if armature.data.bones.active:
        active_pb = pbs.get(armature.data.bones.active.name)

    pb_set = set()
    if option == "LINKED_BONE":
        for selected_pb in selected_pbs:
            traverse_parent(selected_pb, pb_set)
            traverse_children(selected_pb, pb_set)
    elif option == "RING_BONE":
        get_ring_bone(selected_pbs, pbs, pb_set)

    for pb in pb_set:
        pb.bone.select = True
    active_pb.bone.select = True
