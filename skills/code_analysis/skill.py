from tools import file_tools, code_tools


def register_tools():
    file_tools.register_tools()
    code_tools.register_tools()


def unregister_tools():
    file_tools.unregister_tools()
    code_tools.unregister_tools()
