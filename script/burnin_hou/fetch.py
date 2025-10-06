import hou

from burnin.api import BurninClient
from burnin.entity.surreal import Thing
from burnin.entity.node import Version, Node
from burnin.entity.filetype import Geometry

from burnin_hou.ui import buildDirPathFromVersionNode
from burnin_hou.ui import _buildMenuStringList

def fetch_version_list(kwargs):
    burnin_client = BurninClient()
    node = kwargs['node']
    root_id = node.parm("root_id").evalAsString()
    component_path = node.parm("component_path").evalAsString()
    component_id = Thing.from_ids(root_id, component_path)
    menu_list = []
    try:
        component_node = burnin_client.get_component_version_node(component_id)
        version_list = component_node.get_segment_names()
        menu_list.extend(version_list)
    except Exception as e:
        print(e)

    menu_list.reverse()
    return _buildMenuStringList(menu_list, add_prefix=False)

def fetch_version_node(kwargs, context="SOP"):
    node = kwargs['node']
    root_id = node.parm("root_id").evalAsString()
    component_path = node.parm("component_path").evalAsString()
    if component_path.endswith("/"):
        component_path = component_path[:-1]
    version_type = node.parm("version_type").evalAsString()
    if version_type == "Version":
        version_number = node.parm("version").evalAsString()
    else:
        version_number = version_type

    component_id = Thing.from_ids(root_id, component_path + "/" + version_number)

    # rest error nodes
    node.parm("error_switch").lock(0)
    node.parm("error_switch").set(0)
    node.parm("errormsg1").lock(0)
    node.parm("errormsg1").set("")


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
        if not node_type.file_type.variant_name == "Geometry":
            node.parm("error_switch").set(1)
            node.parm("error_switch").lock(1)
            node.parm("errormsg1").set(f"Invalid file type: {node_type.file_type.variant_name}")
            node.parm("errormsg1").lock(1)
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

        if context == "SOP":
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
                node.parm("error_switch").set(1)
                node.parm("error_switch").lock(1)
                node.parm("errormsg1").set(f"Invalid File Type: Cannot read {file_type_str} file")
                node.parm("errormsg1").lock(1)
                raise Exception(f"Invalid file type: {file_type_str}")

            # set time dependedn
            time_dependent = file_type.time_dependent
            node.parm("timedependent").lock(0)
            node.parm("timedependent").set(time_dependent)
            node.parm("timedependent").lock(1)

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
        
        if context == "LOP":
            file_type_str = file_type.file_format
            if file_type_str not in [".usd", ".usdc", ".usda", ".usdz"]:
                node.parm("error_switch").set(1)
                node.parm("error_switch").lock(1)
                node.parm("errormsg1").set(f"Invalid File Type: Cannot read {file_type_str} file")
                node.parm("errormsg1").lock(1)
                raise Exception(f"Invalid file type: {file_type_str}")

            file_name = file_type.file_name + file_type_str
            node.parm("file_name").lock(0)
            node.parm("file_name").set(file_name)
            node.parm("file_name").lock(1)



    except Exception as e:
        print(e)
        return None
    return version_node
