"""
HTML report generator using Jinja2.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def generate_html_report(
    project_name: str,
    selected: Dict[str, Any],
    pareto: List[Dict[str, Any]],
    strategy_label: str = "",
) -> str:
    """Render and return an HTML report string."""
    template = env.get_template("report.html")
    return template.render(
        project_name=project_name,
        selected=selected,
        pareto=pareto,
        strategy_label=strategy_label,
    )
