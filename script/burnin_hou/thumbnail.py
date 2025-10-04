from husd import assetutils
from pathlib import Path
import hou, os
import toolutils
from datetime import datetime

def get_viewer():
    viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    pane = viewer.pane()
    return viewer, pane

# Does not work
def snap(node_path: str):
    viewer, pane = get_viewer()

    output = Path(node_path) / "thumbnail.png"

    viewport = viewer.curViewport()
    res_x =viewport.size()[2]
    res_y =viewport.size()[3]

    print(res_x, res_y)
    print(output)

    # assetutils.saveThumbnailFromViewer(
    #     sceneviewer = viewer,
    #     frame=hou.frame(),
    #     res=(res_x,res_y),
    #     output=output
    # )

    msg = 'Snapshot saved: "{}"'.format(output)
    hou.ui.setStatusMessage(msg, severity=hou.severityType.Message)


# Does not work
def saveViewportToThumbnail(node_path: str):
    if hou.isUIAvailable():
        viewer, pane = get_viewer()
        output = Path(node_path) / "thumbnail.png"
        viewport = viewer.curViewport()
        res_x =viewport.size()[2]
        res_y =viewport.size()[3]
        res = (res_x, res_y)
        output = Path(node_path) / "thumbnail.png"
        assetutils.saveThumbnailFromViewer(output=output,res=res)


def ExportScreenshot(node_path: str):

    #Get the current Desktop
    desktop = hou.ui.curDesktop()

    # Get the scene viewer
    scene_view = toolutils.sceneViewer()


    output = Path(node_path) / "thumbnail.png"

    # Copy the viewer's current flipbook settings
    flipbook_options = scene_view.flipbookSettings().stash()

    #Current framne
    cf = int(hou.expandString("$F"))


    flipbook_options.output(output)
    flipbook_options.frameRange( (cf, cf) )
    flipbook_options.beautyPassOnly(False)
    flipbook_options.visibleTypes(hou.flipbookObjectType.GeoOnly)
    flipbook_options.outputToMPlay(False)

    cam = scene_view.curViewport().camera()

    if cam:
        rx = cam.parm("resx").eval()
        ry = cam.parm("resy").eval()

        flipbook_options.useResolution = True
        flipbook_options.resolution( (rx, ry) )


    scene_view.flipbook(viewport=None, settings=flipbook_options, open_dialog=False)

    return output

def thumbnail_path(kwargs):
    node = kwargs['node']
    dir_path = node.parm("dir_path").evalAsString() 
    output = Path(dir_path) / ".node"
    if not output.exists():
        msg = 'Output directory does not exist to store thumbnail: "{}"'.format(output)
        hou.ui.setStatusMessage(msg, severity=hou.severityType.Message)
        return None
    else:
        output = output / "thumbnail.png"
        return output


def snap_shot(kwargs):
    try:
        viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
        pane = viewer.pane()
        output = thumbnail_path(kwargs)
        if not output:
            return

        viewport = viewer.curViewport()
        if viewport is None:
            return
        res_x =viewport.size()[2]
        res_y =viewport.size()[3]
        
        assetutils.saveThumbnailFromViewer(
            sceneviewer = viewer,
            frame=hou.frame(),
            res=(res_x,res_y),
            output=str(output)
        )
        msg = 'Snapshot saved: "{}"'.format(output)
        hou.ui.setStatusMessage(msg, severity=hou.severityType.Message)
        return output
    except Exception as e:
        msg = 'Snapshot failed: "{}"'.format(e)
        print(msg)
        hou.ui.setStatusMessage(msg, severity=hou.severityType.Error)
        return None
