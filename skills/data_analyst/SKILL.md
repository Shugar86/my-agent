# Data Analyst

Analyze structured data, build charts, run statistical models using Python.

## Description
Processes CSV/Excel data, generates visualizations (matplotlib/seaborn/plotly), runs statistical analysis, and delivers actionable insights. Uses isolated IPython-style execution.

## Usage
```python
from skills.data_analyst.skill import analyze_data, create_chart

# Analyze CSV
results = analyze_data("data.csv", operations=["describe", "corr", "trend"])

# Create chart
chart_path = create_chart(data, chart_type="bar", title="Revenue by Month")
```

## Capabilities
- **Data Processing**: pandas, numpy, scipy for data transformation
- **Visualization**: matplotlib, seaborn, plotly for charts
- **Statistics**: descriptive stats, correlation, regression, trend analysis
- **File I/O**: CSV, Excel (openpyxl), JSON data loading
- **Output**: PNG charts, summary tables, insight reports

## Requirements
- pandas, numpy, matplotlib, seaborn, plotly, scipy, openpyxl

## Best Practices
- Always validate data before analysis (check nulls, types)
- Save charts to output/ directory
- Include data sources and time periods in reports
- Quantify findings with concrete numbers
