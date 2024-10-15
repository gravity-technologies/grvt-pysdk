# ruff: noqa: D200
# ruff: noqa: D204
# ruff: noqa: D205
# ruff: noqa: D404
# ruff: noqa: W291
# ruff: noqa: D400
# ruff: noqa: E501



class ConnectionInProgress(Exception):
    """The SDK is attempting to connect to the web socket, we cannot try to subscribe at this time"""
    pass
