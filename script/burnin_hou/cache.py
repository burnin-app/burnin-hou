import hou
from pathlib import Path
import sys

from burnin.api import BurninClient
from burnin.entity.node import Node
from burnin.entity.surreal import Thing
from burnin.entity.version import Version, VersionStatus
from burnin.entity.filetype import FileType
from burnin.entity.utils import TypeWrapper

from burnin_hou.thumbnail import thumbnail_path
from burnin_hou.ui import buildFilePath
import os

def fileCache(kwargs):
    '''
    Component cache node
    '''
    node = kwargs['node']
    node_path = Path(node.path())
    component_path = node.parm('component_path').evalAsString()
    root_id = node.parm("root_id").evalAsString()
    component_id = Thing.from_ids(root_id, component_path + "/v000")
    version_node = Node.new_version(component_id, FileType.Geometry)
    burnin_client = BurninClient()

    delimeter = "/"
    if os.name == 'nt':
        delimeter = "\\"
        # check

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


            ## save data to disk
            file_type = node.parm("file_type").evalAsString()
            cache_node = None
            if file_type in [".bgeo.sc", ".bgeo", ".vdb"]:
                cache_node_path = node_path / "filecache"
                cache_node_path = str(cache_node_path).replace(delimeter, "/")
                cache_node = hou.node(cache_node_path)
            
            if cache_node:
                cache_node.parm("execute").pressButton()

            ## update node type data : Version
            version_type: Version = version_node.node_type.data
            version_type.comment = node.parm("comment").evalAsString()
            version_type.software = "houdini"
            file_name = hou.parm("file_name").evalAsString().split(delimeter)[-1]
            exp = ""
            if hou.parm("timedependent").eval() == 1:
                exp = ".$F4"
            file_name_with_ext = file_name + exp + node.parm("file_type").evalAsString()
            version_type.head_file = file_name_with_ext
            version_type.status = VersionStatus.Published
            node.parm("status").set("Incomplete")

            ## update node type data : FileType
            file_type: FileType = version_type.file_type.data
            file_type.file_name = file_name
            file_type.time_dependent = hou.parm("timedependent").eval() == 1
            if file_type.time_dependent:
                frame_range =  [hou.parm("f1").eval(), hou.parm("f2").eval(), hou.parm("f3").eval()]
                file_type.frame_range = frame_range
                file_type.substeps = hou.parm("substeps").eval()
            file_type.file_format = node.parm("file_type").evalAsString()
            print(file_type)

            version_type.file_type = TypeWrapper(file_type)
            version_node.node_type = TypeWrapper(version_type)
            version_node.created_at = None
            version_node.thumbnail = thumbnail_path(kwargs)
            print(version_node)

            print("\n")
            version_node = burnin_client.commit_component_version(version_node)
            print(version_node)

            # update version status
            version_node_type: Version = version_node.node_type.data
            node.parm("status").set(version_node_type.status)

            if node.parm("thumbnail").eval() == 1:
                hou.parm("update_thumbnail").pressButton()
            
            hou.ui.setStatusMessage(f"File cache completed: {version_node_id}", severity=hou.severityType.Message)

    except Exception as e:
        hou.ui.displayMessage(f"An error occurred:\n{str(e)}", severity=hou.severityType.Error)
