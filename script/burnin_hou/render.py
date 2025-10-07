import hou
from pathlib import Path

from burnin.api import BurninClient
from burnin.entity.node import Node
from burnin.entity.surreal import Thing
from burnin.entity.version import Version, VersionStatus
from burnin.entity.filetype import FileType
from burnin.entity.utils import TypeWrapper
from burnin_hou.ui import buildFilePath

def burninUSDRenderROP(kwargs):
    '''
    Burnin USD Render ROP
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
            file_name_with_ext = file_name + ".$F4.exr"
            full_path = file_path / file_name_with_ext

            node.parm("outputimage").set(str(full_path))
            node.parm("execute").pressButton()

            ## update node type data : Version
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

            version_node_type: Version = version_node.node_type.data
            node.parm("status").set(version_node_type.status)
    
    except Exception as e:
        hou.ui.displayMessage(f"An error occurred:\n{str(e)}", severity=hou.severityType.Error)

