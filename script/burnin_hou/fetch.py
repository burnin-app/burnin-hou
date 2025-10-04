import hou
from burnin.api import BurninClient
from burnin.entity.surreal import Thing
from burnin_hou.ui import buildDirPathFromVersionNode
from burnin.entity.node import Version, Node
from burnin.entity.filetype import Geometry

def fetch_version_node(kwargs):
    node = kwargs['node']
    root_id = node.parm("root_id").evalAsString()
    component_path = node.parm("component_path").evalAsString()
    if component_path.endswith("/"):
        component_path = component_path[:-1]
    version_type = node.parm("version_type").evalAsString()
    component_id = Thing.from_ids(root_id, component_path + "/" + version_type)

    try:
        burnin_client = BurninClient()
        version_node: Node 
        try:
            version_node = burnin_client.get_version_node(component_id)
        except Exception as e:
            print(e)
            ## reset paraemter data
            node.parm("comment").lock(0)
            node.parm("comment").set("")
            node.parm("status").lock(0)
            node.parm("status").set("None")
            node.parm("file_name").lock(0)
            node.parm("file_name").set("")
            node.parm("file_type").lock(0)
            node.parm("file_type").set(0)
            node.parm("timedependent").lock(0)
            node.parm("timedependent").set(0)
            node.parm("f1").lock(0)
            node.parm("f1").set(0)
            node.parm("f2").lock(0)
            node.parm("f2").set(0)
            node.parm("f3").lock(0)
            node.parm("f3").set(0)
            node.parm("substeps").lock(0)
            node.parm("substeps").set(0)
            node.parm("dir_path").lock(0)
            node.parm("dir_path").set("")
            return None

        if not version_node.node_type.variant_name == "Version":
            raise Exception(f"Invalid node type: {version_node.node_type.variant_name}")

        node_file_path = buildDirPathFromVersionNode(kwargs, version_node)
        node.parm("dir_path").lock(0)
        node.parm("dir_path").set(str(node_file_path))
        node.parm("dir_path").lock(1)

        node_type: Version = version_node.node_type.data
        print(node_type)
        if not node_type.file_type.variant_name == "Geometry":
            raise Exception(f"Invalid file type: {node_type.file_type.variant_name}")
        
        ## set comment and status
        if node_type.comment:
            node.parm("comment").lock(0)
            node.parm("comment").set(node_type.comment)
            node.parm("comment").lock(1)

        node.parm("status").lock(0)
        node.parm("status").set(node_type.status)
        node.parm("status").lock(1)

        file_type: Geometry = node_type.file_type.data

        # set file name
        file_name = file_type.file_name
        node.parm("file_name").lock(0)
        node.parm("file_name").set(file_name)
        node.parm("file_name").lock(1)

        # set file type
        file_type_str = file_type.file_format
        file_type_parm = hou.parm("file_type")
        file_type_items = file_type_parm.menuItems()
        if file_type_str in file_type_items:
            index = file_type_items.index(file_type_str)
            file_type_parm.lock(0)
            file_type_parm.set(index)
            file_type_parm.lock(1)
        else:
            raise Exception(f"Invalid file type: {file_type_str}")

        # set time dependedn
        time_dependent = file_type.time_dependent
        node.parm("timedependent").lock(0)
        node.parm("timedependent").set(time_dependent)
        node.parm("timedependent").lock(1)
        print(file_type)

        if time_dependent:
            frame_range = file_type.frame_range
            node.parm("f1").lock(0)
            node.parm("f1").set(frame_range[0])
            node.parm("f1").lock(1)
            node.parm("f2").lock(0)
            node.parm("f2").set(frame_range[1])
            node.parm("f2").lock(1)
            node.parm('f3').lock(0)
            node.parm('f3').set(frame_range[2])
            node.parm('f3').lock(1)

            # substeps
            node.parm("substeps").lock(0)
            node.parm("substeps").set(file_type.substeps)
            node.parm("substeps").lock(1)



        print(version_node)
    except Exception as e:
        print(e)
        return None
    return version_node
