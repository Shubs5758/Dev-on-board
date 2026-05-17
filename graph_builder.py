"""
Graph visualization module for DevOnboard.
Builds interactive network graphs using networkx and pyvis.
"""

import networkx as nx
from pyvis.network import Network
from typing import List, Dict, Tuple
from pathlib import Path
import utils


def build_file_graph(parsed_files: List[Dict], role: str) -> str:
    """
    Build an interactive file dependency graph using pyvis.
    
    Args:
        parsed_files: List of parsed file dictionaries
        role: Developer role for highlighting relevant files
        
    Returns:
        HTML string of the rendered graph
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Create file path to info mapping
    file_map = {f['path']: f for f in parsed_files}
    
    # Add nodes
    for file_info in parsed_files:
        filepath = file_info['path']
        filename = file_info['name']
        lines = file_info.get('lines', 0)
        language = file_info.get('language', 'Unknown')
        
        # Determine node color based on file type
        color = _get_node_color(filepath)
        
        # Size based on lines of code (15-45px)
        size = min(15 + (lines / 20), 45)
        
        # Create label
        label = filename
        
        # Add node with properties
        G.add_node(
            filepath,
            label=label,
            title=f"{filename}\n{language}\n{lines} lines",
            color=color,
            size=size,
            language=language,
            lines=lines
        )
    
    # Add edges based on imports
    for file_info in parsed_files:
        source_path = file_info['path']
        imports = file_info.get('imports', [])
        
        for imp in imports:
            # Try to resolve import to actual file
            target_path = _resolve_import(imp, source_path, file_map)
            
            if target_path and target_path in file_map:
                # Add edge
                if G.has_edge(source_path, target_path):
                    # Increase edge weight for multiple imports
                    G[source_path][target_path]['weight'] += 1
                else:
                    G.add_edge(source_path, target_path, weight=1)
    
    # Create pyvis network
    net = Network(
        height="600px",
        width="100%",
        directed=True,
        bgcolor="#fafafa",
        font_color="#2c2c2a"
    )
    
    # Configure physics
    net.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.001,
        damping=0.09
    )
    
    # Add nodes and edges from networkx graph
    for node, attrs in G.nodes(data=True):
        net.add_node(
            node,
            label=attrs.get('label', node),
            title=attrs.get('title', node),
            color=attrs.get('color', '#888780'),
            size=attrs.get('size', 20)
        )
    
    for source, target, attrs in G.edges(data=True):
        weight = attrs.get('weight', 1)
        width = min(1 + weight, 3)
        net.add_edge(source, target, width=width)
    
    # Generate HTML
    html = net.generate_html()
    
    return html


def build_function_graph(parsed_files: List[Dict]) -> str:
    """
    Build an interactive function-level call graph.
    
    Args:
        parsed_files: List of parsed file dictionaries
        
    Returns:
        HTML string of the rendered graph
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Only process Python files for now (have detailed AST info)
    python_files = [f for f in parsed_files if f.get('language') == 'Python']
    
    # Track function call counts
    call_counts = {}
    
    # Add function nodes and edges
    for file_info in python_files:
        filepath = file_info['path']
        functions = file_info.get('functions', [])
        
        for func in functions:
            func_name = func['name']
            node_id = f"{filepath}::{func_name}"
            
            # Add function node
            G.add_node(
                node_id,
                label=func_name,
                title=f"{func_name}\n{filepath}\nLine {func.get('line_number', '?')}",
                filepath=filepath,
                color="#378ADD"
            )
            
            # Track calls
            if node_id not in call_counts:
                call_counts[node_id] = 0
            
            # Add edges for function calls
            calls_made = func.get('calls_made', [])
            for called_func in calls_made:
                # Try to find the called function in the same file first
                target_id = f"{filepath}::{called_func}"
                
                if target_id in G.nodes():
                    G.add_edge(node_id, target_id)
                    call_counts[target_id] = call_counts.get(target_id, 0) + 1
    
    # Highlight top 5 most-called functions
    if call_counts:
        top_functions = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for func_id, count in top_functions:
            if func_id in G.nodes():
                G.nodes[func_id]['color'] = "#EF9F27"  # Amber
                G.nodes[func_id]['size'] = 30
                G.nodes[func_id]['title'] += f"\n⭐ Called {count} times"
    
    # Create pyvis network
    net = Network(
        height="600px",
        width="100%",
        directed=True,
        bgcolor="#fafafa",
        font_color="#2c2c2a"
    )
    
    # Configure physics
    net.barnes_hut(
        gravity=-5000,
        central_gravity=0.3,
        spring_length=150,
        spring_strength=0.001,
        damping=0.09
    )
    
    # Add nodes and edges
    for node, attrs in G.nodes(data=True):
        net.add_node(
            node,
            label=attrs.get('label', node),
            title=attrs.get('title', node),
            color=attrs.get('color', '#378ADD'),
            size=attrs.get('size', 20)
        )
    
    for source, target in G.edges():
        net.add_edge(source, target)
    
    # Generate HTML
    html = net.generate_html()
    
    return html


def analyse_graph_metrics(parsed_files: List[Dict]) -> Dict:
    """
    Analyse graph structure and return key metrics.
    
    Args:
        parsed_files: List of parsed file dictionaries
        
    Returns:
        Dictionary with hub_files, isolated_files, circular_deps, total_connections
    """
    # Build networkx graph
    G = nx.DiGraph()
    
    # Create file map
    file_map = {f['path']: f for f in parsed_files}
    
    # Add nodes
    for file_info in parsed_files:
        G.add_node(file_info['path'])
    
    # Add edges
    for file_info in parsed_files:
        source_path = file_info['path']
        imports = file_info.get('imports', [])
        
        for imp in imports:
            target_path = _resolve_import(imp, source_path, file_map)
            if target_path and target_path in file_map:
                G.add_edge(source_path, target_path)
    
    # Calculate metrics
    metrics = {
        'hub_files': [],
        'isolated_files': [],
        'circular_deps': [],
        'total_connections': G.number_of_edges()
    }
    
    # Find hub files (most imported)
    in_degrees = dict(G.in_degree())
    sorted_by_imports = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
    
    for filepath, degree in sorted_by_imports[:3]:
        if degree > 0:
            file_info = file_map.get(filepath, {})
            metrics['hub_files'].append({
                'path': filepath,
                'name': file_info.get('name', Path(filepath).name),
                'import_count': degree,
                'reason': _explain_hub_importance(filepath, degree)
            })
    
    # Find isolated files (no connections)
    for node in G.nodes():
        if G.in_degree(node) == 0 and G.out_degree(node) == 0:
            file_info = file_map.get(node, {})
            metrics['isolated_files'].append({
                'path': node,
                'name': file_info.get('name', Path(node).name)
            })
    
    # Detect circular dependencies
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles[:5]:  # Limit to first 5
            cycle_names = [file_map.get(f, {}).get('name', Path(f).name) for f in cycle]
            metrics['circular_deps'].append({
                'files': cycle,
                'names': cycle_names,
                'description': ' → '.join(cycle_names) + ' → ' + cycle_names[0]
            })
    except:
        pass
    
    return metrics


def _get_node_color(filepath: str) -> str:
    """Determine node color based on file type."""
    if utils.is_entry_point(filepath):
        return "#1D9E75"  # Green - entry points
    elif utils.is_config_file(filepath):
        return "#E24B4A"  # Red - config files
    elif utils.is_test_file(filepath):
        return "#888780"  # Gray - tests
    elif any(keyword in filepath.lower() for keyword in ['util', 'helper', 'common', 'shared']):
        return "#EF9F27"  # Orange - utilities
    else:
        return "#378ADD"  # Blue - core modules


def _resolve_import(import_info: str, source_path: str, file_map: Dict) -> str:
    """
    Try to resolve an import statement to an actual file path.
    
    Args:
        import_info: Import string or dict
        source_path: Path of the file doing the importing
        file_map: Dictionary mapping file paths to file info
        
    Returns:
        Resolved file path or None
    """
    # Handle dict format from Python AST
    if isinstance(import_info, dict):
        module = import_info.get('module', '')
    else:
        module = str(import_info)
    
    if not module:
        return None
    
    # Remove quotes and clean up
    module = module.strip('\'"')
    
    # Try different resolution strategies
    source_dir = str(Path(source_path).parent)
    
    # Strategy 1: Relative import (./module or ../module)
    if module.startswith('.'):
        # Convert relative to absolute
        parts = module.split('/')
        current_dir = Path(source_dir)
        
        for part in parts:
            if part == '..':
                current_dir = current_dir.parent
            elif part and part != '.':
                current_dir = current_dir / part
        
        # Try with different extensions
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '']:
            candidate = str(current_dir) + ext
            if candidate in file_map:
                return candidate
    
    # Strategy 2: Look for matching filename
    module_name = module.split('.')[-1].split('/')[-1]
    for filepath in file_map.keys():
        filename = Path(filepath).stem
        if filename == module_name:
            return filepath
    
    # Strategy 3: Partial path match
    for filepath in file_map.keys():
        if module in filepath or module.replace('.', '/') in filepath:
            return filepath
    
    return None


def _explain_hub_importance(filepath: str, import_count: int) -> str:
    """Generate explanation for why a hub file is important."""
    filename = Path(filepath).name
    
    if utils.is_entry_point(filepath):
        return f"Entry point imported by {import_count} files - critical for app initialization"
    elif 'util' in filepath.lower() or 'helper' in filepath.lower():
        return f"Utility module used across {import_count} files - contains shared functionality"
    elif 'model' in filepath.lower() or 'schema' in filepath.lower():
        return f"Data model used by {import_count} files - defines core data structures"
    elif 'config' in filepath.lower():
        return f"Configuration imported by {import_count} files - centralizes settings"
    else:
        return f"Core module imported by {import_count} files - central to the architecture"

# Made with Bob
