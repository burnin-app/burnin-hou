# node = hou.node("/obj/lightning_FX/lightning_parameter_switch")
# folder_name = "main_parameters"

# parm_group = node.parmTemplateGroup()

def get_parms_in_folder(ptg_or_folder, folder_name):
    """
    ptg_or_folder: can be ParmTemplateGroup or FolderParmTemplate
    returns list of parm names under folder_name
    """
    import hou
    for pt in ptg_or_folder.entries() if isinstance(ptg_or_folder, hou.ParmTemplateGroup) else ptg_or_folder.parmTemplates():
        # check if this is a folder
        if pt.type() == hou.parmTemplateType.Folder:
            if pt.name() == folder_name:
                # folder found, return its children names
                return [child.name() for child in pt.parmTemplates()]
            else:
                # recursively search nested folders
                result = get_parms_in_folder(pt, folder_name)
                if result:
                    return result
    return []

# parm_names = get_parms_in_folder(parm_group, folder_name)

# print("Parameters under folder:", parm_names)


def update_expression(kwargs):
    node = kwargs['node']
    folder_name = "main_parameters"
    parm_group = node.parmTemplateGroup()

    parm_names = get_parms_in_folder(parm_group, folder_name)

    for parm_name in parm_names:
        if parm_name != "switch_index":

            pt = parm_group.find(parm_name)
            print(pt)

            parm = node.parm(parm_name)

            if parm:
                py_expr = 'idx = int(hou.pwd().parm("switch_index").eval())\nreturn hou.pwd().parm(f"' + parm_name + '{idx}").eval()'
                # py_expr = (
                #     'idx = int(hou.pwd().parm("switch_index").eval())\n'
                #     f'p = hou.pwd().parm("{parm_name}" + str(idx))\n'
                #     'return p.eval() if p.parmTemplate().type() != hou.parmTemplateType.Float3 else p.evalAsTuple()'
                # )
                import hou
                parm.setExpression(py_expr, hou.exprLanguage.Python)

