"""
NHS Data Lineage Tracking

This module implements data lineage tracking for healthcare data,
capturing data origin, transformations, and flow through systems.
"""

import os
import pandas as pd
import numpy as np
import json
import networkx as nx
from datetime import datetime
import uuid

class DataLineageTracker:
    """
    Tracks data lineage for healthcare datasets.
    
    This class provides tools for mapping data relationships, tracking data flow,
    and visualizing data lineage.
    """
    
    def __init__(self, data_dir='data', output_dir='data/lineage'):
        """
        Initialize the Data Lineage Tracker.
        
        Args:
            data_dir (str): Directory containing the data files
            output_dir (str): Directory to save lineage artifacts
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define standard dataset relationships based on expected file structure
        self.standard_relationships = [
            {
                "source_dataset": "patient_demographics",
                "relationship_type": "primary",
                "target_dataset": "patient_medical_records",
                "joining_fields": ["patient_id", "nhs_number"],
                "description": "Patient demographics are the primary reference for medical records"
            },
            {
                "source_dataset": "patient_demographics",
                "relationship_type": "primary",
                "target_dataset": "patient_lab_results",
                "joining_fields": ["patient_id", "nhs_number"],
                "description": "Patient demographics are the primary reference for lab results"
            },
            {
                "source_dataset": "patient_demographics",
                "relationship_type": "primary",
                "target_dataset": "patient_consent_records",
                "joining_fields": ["patient_id", "nhs_number"],
                "description": "Patient demographics are the primary reference for consent records"
            },
            {
                "source_dataset": "patient_medical_records",
                "relationship_type": "primary",
                "target_dataset": "patient_lab_results",
                "joining_fields": ["record_id"],
                "description": "Medical records are the primary reference for associated lab results"
            },
            {
                "source_dataset": "nhs_staff_records",
                "relationship_type": "referenced_by",
                "target_dataset": "data_access_audit_logs",
                "joining_fields": ["staff_id"],
                "description": "Staff records are referenced by audit logs for access tracking"
            }
        ]
    
    def detect_dataset_relationships(self):
        """
        Detect relationships between datasets based on common fields.
        
        Returns:
            list: Detected relationships between datasets
        """
        # Get all CSV files in the data directory
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"No CSV files found in {self.data_dir}")
            return []
        
        # Load all datasets
        datasets = {}
        for file_name in csv_files:
            base_name = os.path.splitext(file_name)[0]
            try:
                datasets[base_name] = pd.read_csv(os.path.join(self.data_dir, file_name))
                print(f"Loaded {file_name}")
            except Exception as e:
                print(f"Error loading {file_name}: {str(e)}")
        
        # Detect relationships
        detected_relationships = []
        
        # First pass: Detect based on exact field name matches
        for source_name, source_df in datasets.items():
            source_columns = set(source_df.columns)
            
            for target_name, target_df in datasets.items():
                if source_name == target_name:
                    continue
                
                target_columns = set(target_df.columns)
                
                # Find common columns
                common_columns = source_columns.intersection(target_columns)
                
                # Remove common utility columns that don't indicate relationships
                utility_columns = {'created_at', 'updated_at'}
                relationship_columns = [col for col in common_columns if col not in utility_columns]
                
                if relationship_columns:
                    # Check if these columns could be keys
                    potential_keys = []
                    for col in relationship_columns:
                        # A column is a potential key if it has high cardinality
                        source_unique = source_df[col].nunique() / len(source_df) if len(source_df) > 0 else 0
                        target_unique = target_df[col].nunique() / len(target_df) if len(target_df) > 0 else 0
                        
                        # If either has high uniqueness, it's a potential key
                        if source_unique > 0.5 or target_unique > 0.5:
                            potential_keys.append(col)
                    
                    if potential_keys:
                        # Determine relationship type
                        # If source has more unique values than target, it's likely a primary-foreign relationship
                        rel_type = "unknown"
                        for key in potential_keys:
                            source_unique = source_df[key].nunique()
                            target_unique = target_df[key].nunique()
                            
                            if source_unique >= target_unique:
                                rel_type = "primary"
                                break
                            else:
                                rel_type = "referenced_by"
                                break
                        
                        detected_relationships.append({
                            "source_dataset": source_name,
                            "relationship_type": rel_type,
                            "target_dataset": target_name,
                            "joining_fields": potential_keys,
                            "description": f"Detected relationship based on common fields: {', '.join(potential_keys)}",
                            "detection_method": "automatic"
                        })
        
        # Combine with standard relationships
        final_relationships = []
        
        # Add standard relationships first
        for std_rel in self.standard_relationships:
            # Check if both datasets exist
            source_exists = std_rel["source_dataset"] in datasets
            target_exists = std_rel["target_dataset"] in datasets
            
            if source_exists and target_exists:
                # Add with detection method
                rel_copy = std_rel.copy()
                rel_copy["detection_method"] = "standard"
                final_relationships.append(rel_copy)
        
        # Add detected relationships that aren't already covered
        for det_rel in detected_relationships:
            is_new = True
            
            for std_rel in final_relationships:
                if (det_rel["source_dataset"] == std_rel["source_dataset"] and
                    det_rel["target_dataset"] == std_rel["target_dataset"]):
                    is_new = False
                    break
            
            if is_new:
                final_relationships.append(det_rel)
        
        # Save relationships
        output_file = os.path.join(self.output_dir, "dataset_relationships.json")
        with open(output_file, 'w') as f:
            json.dump(final_relationships, f, indent=2)
        
        print(f"Detected {len(final_relationships)} dataset relationships. Results saved to {output_file}")
        
        return final_relationships
    
    def create_lineage_graph(self, relationships=None):
        """
        Create a lineage graph from dataset relationships.
        
        Args:
            relationships (list): Dataset relationships to use
            
        Returns:
            nx.DiGraph: Directed graph representing data lineage
        """
        if relationships is None:
            # Try to load relationships from file
            relationships_file = os.path.join(self.output_dir, "dataset_relationships.json")
            if os.path.exists(relationships_file):
                with open(relationships_file, 'r') as f:
                    relationships = json.load(f)
            else:
                # Detect relationships
                relationships = self.detect_dataset_relationships()
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for rel in relationships:
            source = rel["source_dataset"]
            target = rel["target_dataset"]
            rel_type = rel["relationship_type"]
            
            # Add nodes if they don't exist
            if not G.has_node(source):
                G.add_node(source, type="dataset")
            
            if not G.has_node(target):
                G.add_node(target, type="dataset")
            
            # Add edge with attributes
            G.add_edge(
                source, 
                target, 
                relationship=rel_type,
                joining_fields=rel["joining_fields"],
                description=rel["description"]
            )
        
        return G
    
    def generate_mermaid_diagram(self, graph=None):
        """
        Generate a Mermaid.js diagram from the lineage graph.
        
        Args:
            graph (nx.DiGraph): Lineage graph to visualize
            
        Returns:
            str: Mermaid.js diagram code
        """
        if graph is None:
            graph = self.create_lineage_graph()
        
        # Create Mermaid diagram
        mermaid_code = "graph TD\n"
        
        # Add nodes
        node_ids = {}
        for i, node in enumerate(graph.nodes()):
            node_id = f"N{i}"
            node_ids[node] = node_id
            mermaid_code += f"    {node_id}[{node}]\n"
        
        # Add edges
        for source, target, data in graph.edges(data=True):
            source_id = node_ids[source]
            target_id = node_ids[target]
            
            # Define arrow style based on relationship type
            arrow_style = "-->"
            if data["relationship"] == "primary":
                arrow_style = "==>"
            elif data["relationship"] == "referenced_by":
                arrow_style = "-.->-"
            
            # Create label from joining fields
            if "joining_fields" in data and data["joining_fields"]:
                label = ", ".join(data["joining_fields"])
                mermaid_code += f"    {source_id} {arrow_style}|{label}| {target_id}\n"
            else:
                mermaid_code += f"    {source_id} {arrow_style} {target_id}\n"
        
        # Save Mermaid diagram
        output_file = os.path.join(self.output_dir, "lineage_diagram.mmd")
        with open(output_file, 'w') as f:
            f.write(mermaid_code)
        
        print(f"Generated Mermaid diagram. Saved to {output_file}")
        
        return mermaid_code
    
    def analyze_data_flow(self, audit_file='data_access_audit_logs.csv'):
        """
        Analyze data flow based on audit logs.
        
        Args:
            audit_file (str): Name of the audit logs file
            
        Returns:
            dict: Data flow analysis results
        """
        audit_path = os.path.join(self.data_dir, audit_file)
        if not os.path.exists(audit_path):
            print(f"Audit file not found: {audit_path}")
            return {}
        
        try:
            # Load audit logs
            df_audit = pd.read_csv(audit_path)
            
            # Convert timestamp to datetime
            df_audit['timestamp'] = pd.to_datetime(df_audit['timestamp'])
            
            # Analyze data flow
            flow_analysis = {
                "analysis_id": str(uuid.uuid4()),
                "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "file_analyzed": audit_file,
                "total_access_events": len(df_audit),
                "resource_types": {},
                "staff_access": {},
                "temporal_patterns": {},
                "access_paths": []
            }
            
            # Analyze access by resource type
            resource_counts = df_audit['resource_type'].value_counts().to_dict()
            for resource, count in resource_counts.items():
                flow_analysis["resource_types"][resource] = {
                    "access_count": int(count),
                    "percentage": float(count / len(df_audit) * 100) if len(df_audit) > 0 else 0
                }
            
            # Analyze access by staff
            staff_counts = df_audit.groupby(['staff_id', 'staff_name']).size().reset_index(name='count')
            staff_counts = staff_counts.sort_values('count', ascending=False)
            
            for _, row in staff_counts.head(10).iterrows():
                flow_analysis["staff_access"][row['staff_id']] = {
                    "staff_name": row['staff_name'],
                    "access_count": int(row['count']),
                    "percentage": float(row['count'] / len(df_audit) * 100) if len(df_audit) > 0 else 0
                }
            
            # Analyze temporal patterns (by hour of day)
            df_audit['hour'] = df_audit['timestamp'].dt.hour
            hour_counts = df_audit.groupby('hour').size().to_dict()
            
            for hour, count in hour_counts.items():
                flow_analysis["temporal_patterns"][int(hour)] = {
                    "access_count": int(count),
                    "percentage": float(count / len(df_audit) * 100) if len(df_audit) > 0 else 0
                }
            
            # Analyze common access paths (sequences of actions)
            # Group by staff and sort by timestamp to get sequences
            df_audit = df_audit.sort_values(['staff_id', 'timestamp'])
            
            # Create sequence of actions for each staff member
            staff_sequences = {}
            
            for staff_id, group in df_audit.groupby('staff_id'):
                actions = group['action'].tolist()
                resources = group['resource_type'].tolist()
                
                # Create action-resource pairs
                sequence = [f"{actions[i]}:{resources[i]}" for i in range(len(actions))]
                
                staff_sequences[staff_id] = sequence
            
            # Find common subsequences
            common_paths = {}
            for staff_id, sequence in staff_sequences.items():
                # Look for subsequences of length 2, 3, and 4
                for length in [2, 3, 4]:
                    if len(sequence) >= length:
                        for i in range(len(sequence) - length + 1):
                            subseq = tuple(sequence[i:i+length])
                            if subseq in common_paths:
                                common_paths[subseq] += 1
                            else:
                                common_paths[subseq] = 1
            
            # Sort by frequency
            common_paths = {k: v for k, v in sorted(common_paths.items(), key=lambda item: item[1], reverse=True)}
            
            # Add top 10 common paths
            for path, count in list(common_paths.items())[:10]:
                flow_analysis["access_paths"].append({
                    "path": list(path),
                    "frequency": int(count)
                })
            
            # Save flow analysis
            output_file = os.path.join(self.output_dir, "data_flow_analysis.json")
            with open(output_file, 'w') as f:
                json.dump(flow_analysis, f, indent=2)
            
            print(f"Data flow analysis complete. Results saved to {output_file}")
            
            return flow_analysis
        
        except Exception as e:
            print(f"Error analyzing data flow: {str(e)}")
            return {"error": str(e)}
    
    def generate_impact_analysis(self, dataset_name):
        """
        Generate an impact analysis for a specified dataset.
        
        Args:
            dataset_name (str): Name of the dataset to analyze
            
        Returns:
            dict: Impact analysis results
        """
        # Create lineage graph
        graph = self.create_lineage_graph()
        
        # Check if dataset exists in the graph
        if dataset_name not in graph.nodes:
            return {
                "error": f"Dataset '{dataset_name}' not found in lineage graph",
                "status": "failed"
            }
        
        # Find all datasets that depend on this dataset (downstream)
        downstream = []
        for target in nx.descendants(graph, dataset_name):
            # Get the path from dataset_name to target
            paths = list(nx.all_simple_paths(graph, dataset_name, target))
            
            if paths:
                # Use the shortest path
                path = paths[0]
                
                # Get edges along the path
                edges = []
                for i in range(len(path) - 1):
                    source = path[i]
                    dest = path[i + 1]
                    edge_data = graph.get_edge_data(source, dest)
                    edges.append({
                        "source": source,
                        "target": dest,
                        "relationship": edge_data["relationship"],
                        "joining_fields": edge_data.get("joining_fields", [])
                    })
                
                downstream.append({
                    "dataset": target,
                    "path": path,
                    "edges": edges,
                    "distance": len(path) - 1,
                    "impact_level": "High" if len(path) == 2 else "Medium" if len(path) == 3 else "Low"
                })
        
        # Find all datasets that this dataset depends on (upstream)
        upstream = []
        for source in nx.ancestors(graph, dataset_name):
            # Get the path from source to dataset_name
            paths = list(nx.all_simple_paths(graph, source, dataset_name))
            
            if paths:
                # Use the shortest path
                path = paths[0]
                
                # Get edges along the path
                edges = []
                for i in range(len(path) - 1):
                    src = path[i]
                    dest = path[i + 1]
                    edge_data = graph.get_edge_data(src, dest)
                    edges.append({
                        "source": src,
                        "target": dest,
                        "relationship": edge_data["relationship"],
                        "joining_fields": edge_data.get("joining_fields", [])
                    })
                
                upstream.append({
                    "dataset": source,
                    "path": path,
                    "edges": edges,
                    "distance": len(path) - 1,
                    "dependency_level": "High" if len(path) == 2 else "Medium" if len(path) == 3 else "Low"
                })
        
        # Create impact analysis
        impact_analysis = {
            "analysis_id": str(uuid.uuid4()),
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "dataset": dataset_name,
            "downstream_dependencies": len(downstream),
            "upstream_dependencies": len(upstream),
            "downstream_datasets": downstream,
            "upstream_datasets": upstream,
            "impact_summary": {
                "high_impact": sum(1 for d in downstream if d["impact_level"] == "High"),
                "medium_impact": sum(1 for d in downstream if d["impact_level"] == "Medium"),
                "low_impact": sum(1 for d in downstream if d["impact_level"] == "Low")
            },
            "critical_path": self._find_critical_path(dataset_name, downstream)
        }
        
        # Save impact analysis
        output_file = os.path.join(self.output_dir, f"{dataset_name}_impact_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(impact_analysis, f, indent=2)
        
        print(f"Impact analysis for {dataset_name} complete. Results saved to {output_file}")
        
        return impact_analysis
    
    def _find_critical_path(self, dataset_name, downstream_datasets):
        """
        Find the critical path (most important dependencies) for a dataset.
        
        Args:
            dataset_name (str): The dataset to analyze
            downstream_datasets (list): Downstream dependencies
            
        Returns:
            list: Critical path of datasets
        """
        if not downstream_datasets:
            return []
        
        # Sort by impact level and then by the number of direct dependencies
        high_impact = [d for d in downstream_datasets if d["impact_level"] == "High"]
        
        if not high_impact:
            return []
        
        # Count how many other datasets depend on each high impact dataset
        dependency_counts = {}
        for impact_dataset in high_impact:
            dataset = impact_dataset["dataset"]
            dependency_counts[dataset] = len([d for d in downstream_datasets if dataset in d["path"]])
        
        # Sort high impact datasets by dependency count
        sorted_datasets = sorted(high_impact, key=lambda d: dependency_counts.get(d["dataset"], 0), reverse=True)
        
        # Take top 3 or fewer
        critical_datasets = sorted_datasets[:min(3, len(sorted_datasets))]
        
        return [
            {
                "dataset": d["dataset"],
                "impact_level": d["impact_level"],
                "dependencies": dependency_counts.get(d["dataset"], 0)
            }
            for d in critical_datasets
        ]
    
    def generate_lineage_documentation(self):
        """
        Generate comprehensive data lineage documentation.
        
        Returns:
            dict: Lineage documentation
        """
        # Detect relationships
        relationships = self.detect_dataset_relationships()
        
        # Create lineage graph
        graph = self.create_lineage_graph(relationships)
        
        # Generate Mermaid diagram
        mermaid_code = self.generate_mermaid_diagram(graph)
        
        # Analyze data flow if audit logs exist
        audit_file = 'data_access_audit_logs.csv'
        audit_path = os.path.join(self.data_dir, audit_file)
        
        flow_analysis = {}
        if os.path.exists(audit_path):
            flow_analysis = self.analyze_data_flow(audit_file)
        
        # Create documentation
        documentation = {
            "documentation_id": str(uuid.uuid4()),
            "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "title": "NHS Data Governance - Data Lineage Documentation",
            "version": "1.0",
            "datasets": list(graph.nodes()),
            "relationships": relationships,
            "mermaid_diagram": mermaid_code,
            "flow_analysis": flow_analysis,
            "impact_analyses": {}
        }
        
        # Generate impact analysis for each dataset
        for dataset in graph.nodes():
            impact_analysis = self.generate_impact_analysis(dataset)
            if "error" not in impact_analysis:
                documentation["impact_analyses"][dataset] = impact_analysis
        
        # Save comprehensive documentation
        output_file = os.path.join(self.output_dir, "comprehensive_lineage_documentation.json")
        with open(output_file, 'w') as f:
            json.dump(documentation, f, indent=2)
        
        # Create a more readable markdown version
        markdown = f"# {documentation['title']}\n\n"
        markdown += f"Version: {documentation['version']} | Created: {documentation['created_date']}\n\n"
        
        markdown += "## Datasets\n\n"
        for dataset in documentation["datasets"]:
            markdown += f"- {dataset}\n"
        
        markdown += "\n## Dataset Relationships\n\n"
        markdown += "| Source Dataset | Relationship | Target Dataset | Joining Fields |\n"
        markdown += "|---------------|-------------|---------------|---------------|\n"
        
        for rel in documentation["relationships"]:
            markdown += f"| {rel['source_dataset']} | {rel['relationship_type']} | {rel['target_dataset']} | {', '.join(rel['joining_fields'])} |\n"
        
        markdown += "\n## Data Lineage Diagram\n\n"
        markdown += f"```mermaid\n{documentation['mermaid_diagram']}\n```\n\n"
        
        if "total_access_events" in flow_analysis:
            markdown += "## Data Flow Summary\n\n"
            markdown += f"Total access events: {flow_analysis['total_access_events']}\n\n"
            
            markdown += "### Resource Access Distribution\n\n"
            markdown += "| Resource Type | Access Count | Percentage |\n"
            markdown += "|--------------|-------------|------------|\n"
            
            for resource, details in flow_analysis["resource_types"].items():
                markdown += f"| {resource} | {details['access_count']} | {details['percentage']:.1f}% |\n"
        
        markdown += "\n## Impact Summary\n\n"
        for dataset, analysis in documentation["impact_analyses"].items():
            markdown += f"### {dataset}\n\n"
            markdown += f"- Downstream dependencies: {analysis['downstream_dependencies']}\n"
            markdown += f"- Upstream dependencies: {analysis['upstream_dependencies']}\n"
            markdown += f"- High impact dependencies: {analysis['impact_summary']['high_impact']}\n"
            markdown += f"- Medium impact dependencies: {analysis['impact_summary']['medium_impact']}\n"
            markdown += f"- Low impact dependencies: {analysis['impact_summary']['low_impact']}\n\n"
        
        # Save markdown documentation
        markdown_file = os.path.join(self.output_dir, "data_lineage_documentation.md")
        with open(markdown_file, 'w') as f:
            f.write(markdown)
        
        print(f"Comprehensive lineage documentation complete. Results saved to {output_file} and {markdown_file}")
        
        return documentation

if __name__ == "__main__":
    # Generate lineage documentation
    lineage_tracker = DataLineageTracker()
    documentation = lineage_tracker.generate_lineage_documentation()
