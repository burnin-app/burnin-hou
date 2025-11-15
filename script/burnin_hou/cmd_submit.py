from burnin.api import BurninClient
from burnin.entity.node import Node
from burnin.entity.surreal import Thing
from burnin.entity.version import Version, VersionStatus
from burnin.entity.filetype import FileType
from burnin.entity.utils import TypeWrapper
from burnin.entity.media import FfmpegCMD
from burnin_hou.ui import buildFilePath
from burnin.entity.queue import CmdSubmit
import hou
import os
import shutil




def burninSubmitRenderCmd(kwargs):
    '''
    On Burnin USD Render ROP
    '''

    node = kwargs['node']
    root_id = node.parm("root_id").evalAsString()
    component_path = node.parm("component_path").evalAsString()
    component_id: Thing = Thing.from_ids(root_id, component_path + "/v000")
    version_node: Node = Node.new_version(component_id, FileType.Image)

    burnin_client = BurninClient()

    try:
        version_node: Node = burnin_client.create_or_update_component_version(version_node)
        if version_node:
            version_node_id = version_node.get_node_id_str()
            version_number = version_node_id.split("/")[-1]
            node.parm("version_number").lock(0)
            node.parm("version_number").set(version_number)
            node.parm("version_number").lock(1)

            file_path = buildFilePath(kwargs, include_file_name=False)

            # version status
            node.parm("status").set(VersionStatus.Incomplete.value)

            trange = node.parm("trange").evalAsString()
            file_name = component_path.split("/")[-1] + "_" + version_number
            frame_range = []
            if trange == "off":
                file_name_with_ext = file_name + ".exr"
                thumb_image_file_name_with_ext = file_name_with_ext
                frame_range = [int(hou.frame()), int(hou.frame()), 1]
            else:
                file_name_with_ext = file_name + ".$F4.exr"
                thumb_image_file_name_with_ext = file_name + "." + str(int(node.parm("f1").eval())).zfill(4) + ".exr"
                start_frame = node.pram("f1").eval()
                end_frame = node.pram("f2").eval()
                frame_range = [int(start_frame), int(end_frame)]


            full_path = file_path / file_name_with_ext

            image_file_path = file_path / thumb_image_file_name_with_ext
            output_thumbnail_path = file_path / "thumbnail.png"

            node.parm("outputimage").set(str(full_path))

            hou.hipFile.save()
            current_path = hou.hipFile.path()
            hip_file_ext = current_path.split(".")[-1]
            setup_file_name = file_name + "_render_setup." + hip_file_ext
            setup_path = file_path / setup_file_name
            render_script_name = file_name + "_render_script.py" 
            render_script_path = file_path / render_script_name

            # hou.hipFile.save(file_name=str(setup_path), save_to_recent_files=False)

            rop_node_path = node.path() + "/usdrender_rop"

            # thumbnail render script
            create_render_script(str(render_script_path), str(current_path), str(setup_path), component_id, node.path(), rop_node_path, [image_file_path, output_thumbnail_path])

            # create cmd
            node_names = str(version_node.id.id.String).split("/")
            job_names = []
            for n in node_names:
                if (":" in n):
                    name = n.split(":")[-1]
                    job_names.append(name)
                
            job_name = "_".join(job_names) 

            if trange != "off":
                output_file_path = file_name_with_ext.replace("$F4", "####")
            else:
                output_file_path = file_name_with_ext
            

            cmd = CmdSubmit.new(
                name=job_name,
                shell="hython",
                component_id=version_node.id,
                cwd=None,
                env={},
                args=[
                    str(render_script_path)
                ],
                stack=os.getenv("BU_STACK"),
                frame_range=frame_range,
                user_id = None,
                output_path=str(output_file_path)
            )

            burnin_client.cmd_submit(cmd)

            # update node type data : Version
            version_type: Version = version_node.node_type.data
            version_type.comment = node.parm("comment").evalAsString()
            version_type.software = "houdini"
            version_type.status = VersionStatus.Published

            ## update node type data : FileTYpe
            file_type: FileType = version_type.file_type.data
            file_type.file_name = file_name
            file_type.file_format = ".exr"

            if trange != "off":
                file_type.time_dependent = True
                frame_range =  [hou.parm("f1").eval(), hou.parm("f2").eval(), hou.parm("f3").eval()]
                file_type.frame_range = frame_range
            
            version_type.file_type = TypeWrapper(file_type)
            version_node.node_type = TypeWrapper(version_type)
            version_node.created_at = None

            version_node = burnin_client.commit_component_version(version_node)
            print(version_node)


    except Exception as e:
            hou.ui.displayMessage(f"An error occurred:\n{str(e)}", severity=hou.severityType.Error)#


def create_render_script(render_script_path: str, src_hip_file: str, dst_hip_file: str, version_id: Thing, node_path: str, rop_path: str, thumbnail_paths: list):
    """
    Creates a Python script at `output_path` that will load a given .hip file
    and render the specified ROP inside Houdini.
    """

    thumbnail_content = f'''
    # no thumbnail
'''

    print(thumbnail_paths)
    if len(thumbnail_paths) == 2:
        thumbnail_content = f'''
from burnin.entity.media import FfmpegCMD
from burnin.api import BurninClient

ffmpeg_cmd = FfmpegCMD(r"{str(thumbnail_paths[0])}", r"{str(thumbnail_paths[1])}")
burnin_client = BurninClient()
burnin_client.generate_thumbnail_from_image(ffmpeg_cmd)

'''

    script_content = f'''import hou
hou.hipFile.load(r"{dst_hip_file}")

# ROP path (adjust if needed)
rop = hou.node(r"{rop_path}")

# Get frame range
f1, f2 = rop.evalParm("f1"), rop.evalParm("f2")
print(f"Rendering from frame {{f1}} to {{f2}}...")

# Render (prints progress in hython)
rop.render(verbose=True)

# thumbnail script
{thumbnail_content}
'''

    # Ensure folder exists
    os.makedirs(os.path.dirname(render_script_path), exist_ok=True)

    # copy the file
    shutil.copy2(src_hip_file, dst_hip_file)

    # Write the file
    with open(render_script_path, "w") as f:
        f.write(script_content)

    print(f"Render script created at: {render_script_path}")