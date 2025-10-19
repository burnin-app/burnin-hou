from burnin.api import BurninClient
from burnin.entity.surreal import Thing
from burnin.entity.node import Node

from burnin_hou.ui import _buildMenuStringList

def build_segments_menu(kwargs):
    idx = kwargs.get('script_multiparm_index')
    node = kwargs['node']
    root_id = "nodes-" + node.parm("root_id").evalAsString()
    node_id_str: str = node.parm("node_id_" + str(idx)).evalAsString()
    menu_list = []
    if len(node_id_str) > 0:
        if node_id_str.startswith("@/"):
            node_id: Thing = Thing.from_str(root_id, node_id_str) 
            try:
                burnin_client = BurninClient()
                node: Node = burnin_client.get_node_by_id(node_id)
                menu_list = node.get_segment_names()
            except Exception as e:
                raise Exception(f"{e}")
    
    menu_list.sort()
    return _buildMenuStringList(menu_list, add_prefix=False)
