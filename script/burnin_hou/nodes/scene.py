import hou
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
                if node:
                    menu_list = node.get_segment_names()
            except Exception as e:
                raise Exception(f"{e}")
    
    menu_list.sort()
    return _buildMenuStringList(menu_list, add_prefix=False)

def build_shot(kwargs):
    node = kwargs['node']
    root_id = node.parm("root_id").evalAsString()
    shot_component_path = node.parm("shot_component_path").evalAsString()
    node_id: Thing = Thing.from_ids(root_id, shot_component_path) 

    if shot_component_path.startswith("@/"):
        try:
            burnin_cleint = BurninClient()
            shot_node : Node = burnin_cleint.get_node_by_id(node_id)
            if shot_node:
                # set attributes
                frame_range = shot_node.get_attribute_value("Frame Range")
                if frame_range:
                    node.parm("frx").set(int(frame_range[0]))
                    node.parm("fry").set(int(frame_range[1]))
                    node.parm("frz").set(int(frame_range[2]))

                    start_cache_frame = node.parm("crx").eval()
                    end_cache_frame = node.parm("cry").eval()

                    hou.playbar.setFrameRange(start_cache_frame, end_cache_frame)  
                    hou.setFrame(start_cache_frame)

        except Exception as e:
            raise Exception(f"{e}")

    else:
        hou.ui.setStatusMessage(f"Invalid Shot Path: {shot_component_path}", severity=hou.severityType.Message)
