import os
import importlib.util
from pathlib import Path


class PluginManager:
    def __init__(self, plugins_dirs=None):
        self.plugins_dirs = plugins_dirs or ["plugins/"]
        self.plugins = {}
        self.hooks = {
            "on_message": [],
            "on_response": [],
            "on_tool_call": [],
            "on_error": [],
        }

    def discover(self):
        for plugins_dir in self.plugins_dirs:
            dir_path = Path(plugins_dir)
            if not dir_path.exists():
                continue
            for item in dir_path.iterdir():
                if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                    self._load_plugin(item)
                elif item.is_dir() and (item / "__init__.py").exists():
                    self._load_plugin(item / "__init__.py")

    def _load_plugin(self, path):
        module_name = "plugin_" + path.parent.name if path.name == "__init__.py" else "plugin_" + path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "Plugin"):
            plugin_class = getattr(module, "Plugin")
            plugin = plugin_class()
            name = getattr(plugin, "name", module_name)
            self.plugins[name] = plugin

            for hook_name in self.hooks:
                if hasattr(plugin, hook_name):
                    self.hooks[hook_name].append(getattr(plugin, hook_name))

    def unload(self, name):
        if name in self.plugins:
            plugin = self.plugins[name]
            if hasattr(plugin, "unload"):
                plugin.unload()
            for hook_name in self.hooks:
                if hasattr(plugin, hook_name):
                    hook_fn = getattr(plugin, hook_name)
                    if hook_fn in self.hooks[hook_name]:
                        self.hooks[hook_name].remove(hook_fn)
            del self.plugins[name]

    def reload(self, name=None):
        if name:
            self.unload(name)
            self.discover()
        else:
            for n in list(self.plugins.keys()):
                self.unload(n)
            self.discover()

    def emit(self, hook_name, **kwargs):
        results = []
        for hook in self.hooks.get(hook_name, []):
            try:
                result = hook(**kwargs)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results

    def list_plugins(self):
        return list(self.plugins.keys())
