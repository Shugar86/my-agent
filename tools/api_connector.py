import requests
from core.tool_registry import registry


def api_get(url, headers=None, params=None):
    try:
        response = requests.get(url, headers=headers or {}, params=params or {}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def api_post(url, json=None, headers=None):
    try:
        response = requests.post(url, json=json or {}, headers=headers or {}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def api_put(url, json=None, headers=None):
    try:
        response = requests.put(url, json=json or {}, headers=headers or {}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def api_delete(url, headers=None):
    try:
        response = requests.delete(url, headers=headers or {}, timeout=30)
        response.raise_for_status()
        return {"status": "deleted", "code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def register_tools():
    registry.register(
        name="api_get",
        description="Make a GET request to an API endpoint",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API endpoint URL"},
                "headers": {"type": "object", "description": "Request headers"},
                "params": {"type": "object", "description": "Query parameters"},
            },
            "required": ["url"],
        },
        execute_fn=api_get,
    )

    registry.register(
        name="api_post",
        description="Make a POST request to an API endpoint",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API endpoint URL"},
                "json": {"type": "object", "description": "JSON body"},
                "headers": {"type": "object", "description": "Request headers"},
            },
            "required": ["url"],
        },
        execute_fn=api_post,
    )

    registry.register(
        name="api_put",
        description="Make a PUT request to an API endpoint",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API endpoint URL"},
                "json": {"type": "object", "description": "JSON body"},
                "headers": {"type": "object", "description": "Request headers"},
            },
            "required": ["url"],
        },
        execute_fn=api_put,
    )

    registry.register(
        name="api_delete",
        description="Make a DELETE request to an API endpoint",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API endpoint URL"},
                "headers": {"type": "object", "description": "Request headers"},
            },
            "required": ["url"],
        },
        execute_fn=api_delete,
    )


def unregister_tools():
    registry.unregister("api_get")
    registry.unregister("api_post")
    registry.unregister("api_put")
    registry.unregister("api_delete")
