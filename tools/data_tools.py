import json
import os
import subprocess
import sys
from typing import Dict, Any, Optional

def analyze_csv(file_path: str, operations: list = None) -> Dict[str, Any]:
    """Analyze CSV/Excel file and return statistics."""
    from core.validation import validate_file_exists_or_error
    err = validate_file_exists_or_error(file_path, "file_path")
    if err:
        return {"error": err}
    try:
        import pandas as pd
        
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            return {"error": f"Unsupported format: {file_path}"}
        
        operations = operations or ["describe"]
        results = {
            "shape": df.shape,
            "columns": list(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
        }
        
        if "describe" in operations:
            results["describe"] = df.describe().to_dict()
        if "corr" in operations and len(df.select_dtypes(include=['number']).columns) > 1:
            results["correlation"] = df.corr().to_dict()
        
        return results
    except Exception as e:
        return {"error": str(e)}

def create_chart(data: dict, chart_type: str = "bar", title: str = "Chart", 
                 output_path: str = None) -> str:
    """Create chart from data dictionary."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import pandas as pd
        
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        df = pd.DataFrame({"x": labels, "y": values})
        
        plt.figure(figsize=(10, 6))
        if chart_type == "bar":
            df.plot(kind='bar', x='x', y='y', legend=False)
        elif chart_type == "line":
            df.plot(kind='line', x='x', y='y', legend=False, marker='o')
        elif chart_type == "pie":
            df.set_index('x')['y'].plot(kind='pie', autopct='%1.1f%%')
        else:
            df.plot(kind='bar', x='x', y='y', legend=False)
        
        plt.title(title)
        plt.tight_layout()
        
        if not output_path:
            output_path = f"output/chart_{chart_type}.png"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    except Exception as e:
        return f"Error: {str(e)}"

def run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute Python code in Docker sandbox only."""
    from core.docker_sandbox import docker_sandbox

    docker_result = docker_sandbox.run_python(code)
    if docker_result.get("success"):
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "returncode": 0,
            "success": True,
        }
    if "error" in docker_result:
        return {
            "stdout": docker_result.get("stdout", ""),
            "stderr": docker_result.get("stderr", ""),
            "error": docker_result["error"],
            "returncode": 1,
            "success": False,
        }
    return {
        "stdout": "",
        "stderr": "",
        "error": "Docker sandbox unavailable. Code execution disabled.",
        "success": False,
    }


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="analyze_csv",
        description="Analyze a CSV or Excel file and return statistics (shape, columns, nulls, describe, correlations)",
        parameters={"type": "object", "properties": {
            "file_path": {"type": "string"},
            "operations": {"type": "array", "items": {"type": "string"}},
        }},
        execute_fn=analyze_csv,
    )
    registry.register(
        name="create_chart",
        description="Create a chart (bar, line, pie) from data and save as PNG image",
        parameters={"type": "object", "properties": {
            "data": {"type": "object", "properties": {
                "labels": {"type": "array", "items": {"type": "string"}},
                "values": {"type": "array", "items": {"type": "number"}},
            }},
            "chart_type": {"type": "string"},
            "title": {"type": "string"},
            "output_path": {"type": "string"},
        }},
        execute_fn=create_chart,
    )
    registry.register(
        name="run_python",
        description="Execute Python code in subprocess sandbox and return stdout/stderr/result",
        parameters={"type": "object", "properties": {
            "code": {"type": "string"},
            "timeout": {"type": "integer"},
        }},
        execute_fn=run_python,
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["analyze_csv", "create_chart", "run_python"]:
        registry.unregister(name)
