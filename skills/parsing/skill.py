from tools import web_tools, file_tools


def register_tools():
    web_tools.register_tools()
    file_tools.register_tools()


def unregister_tools():
    web_tools.unregister_tools()
    file_tools.unregister_tools()
