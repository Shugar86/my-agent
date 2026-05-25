from tools import code_tools, file_tools


def register_tools():
    code_tools.register_tools()
    file_tools.register_tools()


def unregister_tools():
    code_tools.unregister_tools()
    file_tools.unregister_tools()
