import hou
from burnin.api import APIClient

def get_api_client():
    if not hasattr(hou.session, "burnin_api_client"):
        hou.session.burnin_api_client = APIClient(port=4646)
        hou.session.burnin_roots = hou.session.burnin_api_client.get_local_roots()
    return hou.session.burnin_api_client
