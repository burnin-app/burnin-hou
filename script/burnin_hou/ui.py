import hou
from builtins import zip
from burnin.api import BurninClient
from pathlib import Path
from burnin.entity.utils import parse_node_path
from burnin.entity.surreal import Thing
from burnin.entity.node import Node

def _buildMenuStringList(names: list[str], add_prefix: bool = False) -> str:
    """ Duplicates each element in a list of strings.
        For example, ["walk", "run"] becomes ["walk", "walk", "run", "run"]
    """
    if add_prefix:
        values = ["@name="+name for name in names]
    else:
        values = names
    return [name for pair in zip(values, names) for name in pair]


def buildRootListMenu():
    """Build a menu containing all the root names"""
    burnin_client = BurninClient()
    temp_names = burnin_client.get_names()
    menu = _buildMenuStringList(temp_names, add_prefix=False)
    return menu

def buildComponentMenuList(kwargs):
    burnin_client = BurninClient()
    node = kwargs['node']
    root_id = node.parm("root_id").evalAsString()
    component_path = node.parm("component_path").evalAsString()
    component_id = Thing.from_ids(root_id, component_path)
    menu_list = ["Latest",  "Atop"]
    try:
        component_node = burnin_client.get_component_version_node(component_id)
        version_list = component_node.get_segment_names()
        menu_list.extend(version_list)
    except Exception as e:
        print(e)
    return _buildMenuStringList(menu_list, add_prefix=False)

def buildFilePath(kwargs, include_file_name: bool = False, component_path: str = None) -> Path:
    node = kwargs['node']
    root_path = node.parm("root_path").evalAsString()
    root_name = node.parm("root_name").evalAsString()

    if component_path is None:
        component_path = node.parm("component_path").evalAsString()

    component_path = parse_node_path(component_path)

    if component_path.startswith('/'):
        component_path = component_path[1:]
    version_number = node.parm("version_number").evalAsString()

    if include_file_name:
        file_type = node.parm("file_type").evalAsString()

        frame_expression = "" 
        # check if its time dependent
        if node.parm("timedependent").evalAsInt() == 1:
            frame_expression = ".$F4"

        file_name = component_path.split("/")[-1] + "_" + version_number + frame_expression + file_type

    file_path = Path(root_path) / root_name / component_path / version_number
    if include_file_name:
        return file_path / file_name
    else:
        return file_path
    

def buildDirPathFromVersionNode(kwargs, version_node: Node):
    node = kwargs['node']
    root_path = node.parm("root_path").evalAsString()
    root_name = node.parm("root_name").evalAsString()
    root_path = Path(root_path) / root_name

    version_node_path = version_node.get_node_id_str()
    version_node_path = parse_node_path(version_node_path)
    if version_node_path.startswith('/'):
        version_node_path = version_node_path[1:]
    
    return root_path / version_node_path
    
