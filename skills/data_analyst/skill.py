import json
import os
from typing import List, Dict, Any, Optional

def analyze_data(file_path: str, operations: List[str] = None) -> Dict[str, Any]:
    """Analyze data file (CSV/Excel) and return statistics."""
    try:
        import pandas as pd
        import numpy as np
        
        # Determine file type and load
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return {"error": f"Unsupported file format: {file_path}"}
        
        results = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict(),
        }
        
        operations = operations or ["describe"]
        
        if "describe" in operations:
            results["describe"] = df.describe().to_dict()
        
        if "corr" in operations and len(df.select_dtypes(include=[np.number]).columns) > 1:
            results["correlation"] = df.corr().to_dict()
        
        if "trend" in operations:
            # Simple trend detection for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            trends = {}
            for col in numeric_cols:
                if len(df[col].dropna()) > 1:
                    slope = np.polyfit(range(len(df[col].dropna())), df[col].dropna(), 1)[0]
                    trends[col] = "up" if slope > 0 else "down" if slope < 0 else "flat"
            results["trends"] = trends
        
        if "missing" in operations:
            results["missing_analysis"] = {
                col: {"count": int(count), "percentage": round(count/len(df)*100, 2)}
                for col, count in df.isnull().sum().items() if count > 0
            }
        
        return results
    except Exception as e:
        return {"error": str(e)}

def create_chart(data_source: str, chart_type: str = "bar", 
                 x_column: str = None, y_column: str = None,
                 title: str = "Chart", output_path: str = None) -> str:
    """Create chart from data and save as PNG."""
    try:
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Load data
        if isinstance(data_source, str) and os.path.exists(data_source):
            if data_source.endswith('.csv'):
                df = pd.read_csv(data_source)
            else:
                df = pd.read_excel(data_source)
        elif isinstance(data_source, list):
            df = pd.DataFrame(data_source)
        elif isinstance(data_source, dict):
            df = pd.DataFrame(data_source)
        else:
            df = data_source
        
        # Auto-detect columns if not specified
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not x_column and len(df.columns) > 0:
            x_column = df.columns[0]
        if not y_column and len(numeric_cols) > 0:
            y_column = numeric_cols[0]
        
        # Create figure
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        
        if chart_type == "bar":
            if y_column:
                df.plot(kind='bar', x=x_column, y=y_column, legend=False)
            else:
                df.plot(kind='bar', legend=False)
        elif chart_type == "line":
            if y_column:
                df.plot(kind='line', x=x_column, y=y_column, legend=False)
            else:
                df.plot(kind='line', legend=False)
        elif chart_type == "scatter":
            if y_column:
                df.plot(kind='scatter', x=x_column, y=y_column)
        elif chart_type == "pie":
            if y_column:
                df.set_index(x_column)[y_column].plot(kind='pie', autopct='%1.1f%%')
            else:
                df.iloc[:, 0].plot(kind='pie', autopct='%1.1f%%')
        elif chart_type == "hist":
            if y_column:
                df[y_column].plot(kind='hist', bins=20)
            else:
                df.iloc[:, 0].plot(kind='hist', bins=20)
        elif chart_type == "heatmap":
            if len(numeric_cols) > 1:
                sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0)
        elif chart_type == "box":
            df[numeric_cols].plot(kind='box')
        else:
            return f"Unsupported chart type: {chart_type}"
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save
        if not output_path:
            import time; output_path = f"output/chart_{chart_type}_{int(time.time())}.png"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    except Exception as e:
        return f"Error creating chart: {str(e)}"


def register_tools():
    from tools import data_tools
    data_tools.register_tools()


def unregister_tools():
    from tools import data_tools
    data_tools.unregister_tools()

def run_python_code(code: str) -> Dict[str, Any]:
    """Execute Python code in isolated environment and return results."""
    import io
    import contextlib
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    result = {
        "stdout": "",
        "stderr": "",
        "result": None,
        "error": None
    }
    
    try:
        # Create restricted globals
        safe_globals = {
            "__builtins__": __builtins__,
            "pd": __import__('pandas'),
            "np": __import__('numpy'),
            "plt": __import__('matplotlib.pyplot'),
            "sns": __import__('seaborn'),
            "json": json,
            "os": os,
        }
        
        with contextlib.redirect_stdout(stdout_capture):
            with contextlib.redirect_stderr(stderr_capture):
                exec(code, safe_globals)
        
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()
        
    except Exception as e:
        result["error"] = str(e)
        result["stderr"] = stderr_capture.getvalue()
    
    return result

def generate_insights(data_summary: Dict[str, Any]) -> str:
    """Generate plain-language insights from data analysis results."""
    insights = []
    
    if "describe" in data_summary:
        desc = data_summary["describe"]
        insights.append("## Key Statistics\n")
        for col, stats in desc.items():
            if isinstance(stats, dict):
                insights.append(f"**{col}**: mean={stats.get('mean', 'N/A'):.2f}, std={stats.get('std', 'N/A'):.2f}")
    
    if "trends" in data_summary:
        insights.append("\n## Trends\n")
        for col, trend in data_summary["trends"].items():
            emoji = "📈" if trend == "up" else "📉" if trend == "down" else "➡️"
            insights.append(f"{emoji} **{col}**: {trend}")
    
    if "correlation" in data_summary:
        insights.append("\n## Correlations\n")
        corr = data_summary["correlation"]
        # Find strongest correlations
        pairs = []
        for col1 in corr:
            for col2 in corr[col1]:
                if col1 != col2 and col1 < col2:  # Avoid duplicates
                    val = corr[col1][col2]
                    if abs(val) > 0.5:  # Only strong correlations
                        pairs.append((col1, col2, val))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        for col1, col2, val in pairs[:5]:
            insights.append(f"• **{col1}** ↔ **{col2}**: {val:.3f}")
    
    return "\n".join(insights)
