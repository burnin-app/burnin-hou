import hou

from burnin.api import BurninClient
from burnin.entity.node import Node
from burnin.entity.surreal import Thing
from burnin.entity.version import Version, VersionStatus
from burnin.entity.filetype import FileType
from burnin.entity.utils import TypeWrapper

from burnin_hou.ui import buildFilePath



def burninComponentOutput(kwargs):
    '''
    Burnin Component Output
    '''
    node = kwargs['node']
    input_node = node.inputs()[0]

    node.parm("errormsg1").lock(0)
    node.parm("errormsg1").set("")

    component_output = None
    if input_node.type().name() == "componentoutput":
        component_output = input_node
    else:
        message = f"Input node must be of type 'Component Output'"
        node.parm("errormsg1").set(message)
        return None
    
    root_id = node.parm("root_id").evalAsString()
    component_path = node.parm("component_path").evalAsString()
    asset_name = node.parm("asset_name").evalAsString()
    if len(asset_name) < 1:
        hou.ui.displayMessage(f"Error: Asset name must be specified", severity=hou.severityType.Error)
    
    component_id = Thing.from_ids(root_id, component_path + "/v000")
    version_node = Node.new_version(component_id, FileType.Geometry)
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
            node.parm("dir_path").lock(0)
            node.parm("dir_path").set(str(file_path))
            node.parm("dir_path").lock(1)

            # version status
            node.parm("status").set(VersionStatus.Incomplete.value)

            ## change component_output values
            component_output.parm("name").set(asset_name)
            file_name_with_ext = str(asset_name + ".usd")
            component_output.parm("filename").set(file_name_with_ext)
            output_path = file_path / file_name_with_ext
            component_output.parm("lopoutput").set(str(output_path))

            component_output.parm("execute").pressButton()

            ## update node type data: Version
            version_type: Version = version_node.node_type.data
            version_type.comment = node.parm("comment").evalAsString()
            version_type.software = "houdini"
            version_type.head_file = file_name_with_ext
            version_type.status = VersionStatus.Published

            ## update node type data: FileType
            file_type: FileType = version_type.file_type.data
            file_type.file_name = asset_name
            file_type.file_format = ".usd"

            version_type.file_type = TypeWrapper(file_type)
            version_node.node_type = TypeWrapper(version_type)
            version_node.created_at = None

            version_node = burnin_client.commit_component_version(version_node)
            print(version_node)

            # update version status
            version_node_type: Version = version_node.node_type.data
            node.parm("status").set(version_node_type.status)

            if node.parm("thumbnail").eval() == 1:
                component_output.parm("executeviewport").pressButton()
    
    except Exception as e:
        hou.ui.displayMessage(f"An error occurred:\n{str(e)}", severity=hou.severityType.Error)