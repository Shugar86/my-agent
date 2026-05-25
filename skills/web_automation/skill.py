from tools import web_tools, api_connector


def register_tools():
    web_tools.register_tools()
    api_connector.register_tools()


def unregister_tools():
    web_tools.unregister_tools()
    api_connector.unregister_tools()
