from tools import file_tools


def register_tools():
    file_tools.register_tools()


def unregister_tools():
    file_tools.unregister_tools()


def get_output_path():
    return "output/"
