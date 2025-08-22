#!/usr/bin/env python3
"""
CSV Dependency Graph Comparator

This script parses CSV data with dependency graph information and buckets them 
based on whether the graphs are identical. It includes locator and createdAt
information for each analysis.

Expected CSV format:
locator,createdAt,data

Where:
- locator: Project locator string
- createdAt: Timestamp when analysis was created
- data: JSON string containing the full dependency graph data (in quotes)
"""

import json
import sys
import csv
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
import hashlib
from io import StringIO
from datetime import datetime


class DependencyGraph:
    """Represents a normalized dependency graph for comparison."""
    
    def __init__(self, source_unit: Dict[str, Any]):
        self.type = source_unit.get("Type", "")
        self.graph_breadth = source_unit.get("GraphBreadth", "")
        self.build = source_unit.get("Build", {})
        self.origin_paths = source_unit.get("OriginPaths", [])
        
        # Extract normalized data
        self.direct_imports = self._normalize_locators(self.build.get("Imports", []))
        self.dependencies = self._normalize_dependencies(self.build.get("Dependencies", []))
        self.build_succeeded = self.build.get("Succeeded", False)
        
    def _normalize_locators(self, locators: List[str]) -> Set[str]:
        """Normalize locators by removing version info if needed for comparison."""
        return set(sorted(locators))
    
    def _normalize_dependencies(self, deps: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """Normalize dependencies to locator -> set of imports mapping."""
        normalized = {}
        for dep in deps:
            locator = dep.get("locator", "")
            imports = set(dep.get("imports", []))
            normalized[locator] = imports
        return normalized
    
    def get_signature(self) -> str:
        """Generate a signature for this dependency graph."""
        # Create a deterministic representation of the graph
        data = {
            "type": self.type,
            "graph_breadth": self.graph_breadth,
            "build_succeeded": self.build_succeeded,
            "direct_imports": sorted(list(self.direct_imports)),
            "dependencies": {
                locator: sorted(list(imports)) 
                for locator, imports in sorted(self.dependencies.items())
            }
        }
        
        # Convert to JSON string and hash it
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def is_equivalent_to(self, other: 'DependencyGraph') -> bool:
        """Check if this graph is equivalent to another graph."""
        return (
            self.type == other.type and
            self.graph_breadth == other.graph_breadth and
            self.build_succeeded == other.build_succeeded and
            self.direct_imports == other.direct_imports and
            self.dependencies == other.dependencies
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get basic statistics about this graph."""
        return {
            "direct_dependencies": len(self.direct_imports),
            "total_dependencies": len(self.dependencies),
            "dependencies_with_imports": len([d for d in self.dependencies.values() if d])
        }


class ProjectAnalysis:
    """Represents a complete project analysis with metadata from CSV."""
    
    def __init__(self, locator: str, created_at: str, project_data: Dict[str, Any]):
        self.locator = locator
        self.created_at = created_at
        self.name = project_data.get("Name", "")
        self.source_units = []
        
        for su_data in project_data.get("SourceUnits", []):
            self.source_units.append(DependencyGraph(su_data))
    
    def get_signature(self) -> str:
        """Generate a signature for this entire project analysis."""
        # Sort source units by type and signature for consistent comparison
        su_signatures = []
        for su in sorted(self.source_units, key=lambda x: x.type):
            su_signatures.append(f"{su.type}:{su.get_signature()}")
        
        combined = "|".join(su_signatures)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def is_equivalent_to(self, other: 'ProjectAnalysis') -> bool:
        """Check if this project analysis is equivalent to another."""
        if len(self.source_units) != len(other.source_units):
            return False
        
        # Sort both lists by type for comparison
        self_sorted = sorted(self.source_units, key=lambda x: x.type)
        other_sorted = sorted(other.source_units, key=lambda x: x.type)
        
        return all(
            su1.is_equivalent_to(su2) 
            for su1, su2 in zip(self_sorted, other_sorted)
        )


def parse_csv_data(csv_data: str) -> List[ProjectAnalysis]:
    """Parse CSV data containing dependency graph information."""
    projects = []
    
    # Create a StringIO object from the CSV data
    csv_file = StringIO(csv_data)
    reader = csv.reader(csv_file)
    
    # Read header row
    header = next(reader)
    expected_columns = ["locator", "createdAt", "data"]
    
    # Validate header
    if header != expected_columns:
        print(f"Warning: Expected columns {expected_columns}, got {header}", file=sys.stderr)
    
    for row_num, row in enumerate(reader, start=2):
        if len(row) < 3:
            print(f"Error: Row {row_num} has insufficient columns: {len(row)}", file=sys.stderr)
            continue
            
        locator, created_at, data = row[:3]
        
        try:
            # Parse the JSON data
            project_data = json.loads(data)
            projects.append(ProjectAnalysis(locator, created_at, project_data))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in row {row_num}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error processing row {row_num}: {e}", file=sys.stderr)
            continue
    
    return projects


def bucket_projects(projects: List[ProjectAnalysis]) -> Dict[str, List[ProjectAnalysis]]:
    """Bucket projects by their dependency graph signatures."""
    buckets = defaultdict(list)
    
    for project in projects:
        signature = project.get_signature()
        buckets[signature].append(project)
    
    return dict(buckets)


def format_created_at(created_at_str: str) -> str:
    """Format the created_at timestamp for display."""
    try:
        # Try to parse as ISO format timestamp
        dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        # If parsing fails, return as-is
        return created_at_str


def print_analysis_report(buckets: Dict[str, List[ProjectAnalysis]]):
    """Print a detailed analysis report."""
    print("=" * 100)
    print("CSV DEPENDENCY GRAPH ANALYSIS REPORT")
    print("=" * 100)
    print()
    
    print(f"Total unique graph patterns found: {len(buckets)}")
    print(f"Total project analyses: {sum(len(bucket) for bucket in buckets.values())}")
    print()
    
    # Sort buckets by size (largest first), then by earliest creation time
    def bucket_sort_key(item):
        signature, projects = item
        return (-len(projects), min(p.created_at for p in projects))
    
    sorted_buckets = sorted(buckets.items(), key=bucket_sort_key)
    
    for i, (signature, projects) in enumerate(sorted_buckets, 1):
        print(f"BUCKET {i}: {len(projects)} identical analyses")
        print(f"Graph Signature: {signature}")
        print("-" * 80)
        
        # Analyze the first project in this bucket for graph details
        sample_project = projects[0]
        print(f"Sample Project: {sample_project.name}")
        print(f"Source Units: {len(sample_project.source_units)}")
        
        for j, su in enumerate(sample_project.source_units):
            stats = su.get_stats()
            print(f"  [{j+1}] Type: {su.type}")
            print(f"      Graph Breadth: {su.graph_breadth}")
            print(f"      Build Succeeded: {su.build_succeeded}")
            print(f"      Direct Dependencies: {stats['direct_dependencies']}")
            print(f"      Total Dependencies: {stats['total_dependencies']}")
            print(f"      Origin Paths: {su.origin_paths}")
        
        print(f"\nAnalyses in this bucket (sorted by creation time):")
        
        # Sort projects by creation time
        sorted_projects = sorted(projects, key=lambda x: x.created_at)
        
        for project in sorted_projects:
            # Extract useful parts from the locator for display
            locator_parts = project.locator.split('$')
            if len(locator_parts) >= 2:
                repo_info = locator_parts[0]  # e.g., "custom+8617/github.com/..."
                revision_info = locator_parts[1] if len(locator_parts) > 1 else "unknown"
            else:
                repo_info = project.locator
                revision_info = "unknown"
            
            formatted_time = format_created_at(project.created_at)
            
            print(f"  • Locator: {repo_info}")
            print(f"    Created: {formatted_time}")
            print(f"    Revision: {revision_info}")
            print()
        
        print("=" * 100)
        print()


def print_summary_statistics(buckets: Dict[str, List[ProjectAnalysis]]):
    """Print summary statistics about the analysis."""
    unique_patterns = len(buckets)
    total_analyses = sum(len(bucket) for bucket in buckets.values())
    
    print("SUMMARY STATISTICS")
    print("=" * 50)
    
    if unique_patterns == 1:
        print(f"✓ All {total_analyses} analyses have IDENTICAL dependency graphs!")
    elif unique_patterns == total_analyses:
        print(f"⚠ All {total_analyses} analyses have DIFFERENT dependency graphs!")
    else:
        print(f"📊 Found {unique_patterns} unique patterns among {total_analyses} analyses")
        duplicates = total_analyses - unique_patterns
        print(f"   {duplicates} analyses are duplicates of others")
        
        # Show distribution of bucket sizes
        bucket_sizes = [len(bucket) for bucket in buckets.values()]
        bucket_sizes.sort(reverse=True)
        print(f"   Largest bucket: {bucket_sizes[0]} identical analyses")
        if len(bucket_sizes) > 1:
            print(f"   Bucket size distribution: {bucket_sizes[:5]}{'...' if len(bucket_sizes) > 5 else ''}")
    
    # Time range analysis
    all_projects = [p for bucket in buckets.values() for p in bucket]
    if all_projects:
        timestamps = [p.created_at for p in all_projects]
        timestamps.sort()
        print(f"   Time range: {format_created_at(timestamps[0])} to {format_created_at(timestamps[-1])}")
    
    print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            csv_data = f.read()
    else:
        # Read from stdin
        csv_data = sys.stdin.read()
    
    # Parse the CSV data
    projects = parse_csv_data(csv_data)
    
    if not projects:
        print("No valid project data found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Successfully parsed {len(projects)} project analyses from CSV data.\n")
    
    # Bucket the projects
    buckets = bucket_projects(projects)
    
    # Print the detailed analysis report
    print_analysis_report(buckets)
    
    # Print summary statistics
    print_summary_statistics(buckets)


if __name__ == "__main__":
    main()
