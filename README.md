# FOSSA CSV Dependency Graph Comparator

A Python script that analyzes FOSSA CLI dependency graph data from CSV format and groups projects with identical dependency graphs.

## Overview

This tool parses CSV data containing FOSSA dependency graph analyses and buckets them based on whether their dependency graphs are identical. It compares the actual dependency relationships and imports, ignoring temporary paths or
manifest locations.

## CSV Format

The script expects CSV data with the following columns:

```csv
locator, createdAt, data
```
Where:
- locator: Project locator string (e.g., custom+27932/test$sha256:7167ec...)
- createdAt: Timestamp when analysis was created (ISO format preferred)
- data: JSON string containing the full dependency graph data (quoted)

## Usage

From File

`python csv_dependency_graph_comparator.py data.csv`

From Standard Input

`cat data.csv | python csv_dependency_graph_comparator.py`

##  Output

The script generates a comprehensive analysis report including:

##  Bucket Analysis

- Groups projects with identical dependency graphs
- Shows graph signatures for comparison
- Displays sample project details for each bucket

##  Project Details

For each bucket, the report shows:
- Sample Project: Name and structure overview
- Source Units: Number and types of analyzers used
- Graph Statistics:
- Graph breadth (complete/partial)
- Build success status
- Direct and total dependency counts
- Origin paths (manifest files)

##  Project Listings

- Projects sorted by creation time within each bucket
- Clean repository information extraction
- Formatted timestamps
- Revision information (commit hash/tag)

## Summary Statistics

- Total unique graph patterns found
- Distribution analysis
- Time range of analyses
- Duplicate detection results

## Example Output

```
====================================================================================================
CSV DEPENDENCY GRAPH ANALYSIS REPORT
====================================================================================================

Total unique graph patterns found: 2
Total project analyses: 5

BUCKET 1: 3 identical analyses
Graph Signature: a1b2c3d4e5f6...
--------------------------------------------------------------------------------
Sample Project: https://github.com/example/project
Source Units: 2
[1] Type: gomod
    Graph Breadth: complete
    Build Succeeded: true
    Direct Dependencies: 13
    Total Dependencies: 23
    Origin Paths: ['go.mod']

Analyses in this bucket (sorted by creation time):
• Locator: custom+1/github.com/example/project
  Created: 2024-01-15 14:30:22 UTC
  Revision: sha256:abc123...

====================================================================================================

SUMMARY STATISTICS
==================================================
📊 Found 2 unique patterns among 5 analyses
 3 analyses are duplicates of others
 Largest bucket: 3 identical analyses
 Time range: 2024-01-15 10:00:00 UTC to 2024-01-15 16:45:00 UTC
```
## Key Features

- Intelligent Graph Comparison: Compares actual dependency relationships, not temporary file paths
- Metadata Preservation: Includes locator and timestamp information in analysis
- Flexible Input: Supports both file input and stdin piping
- Detailed Reporting: Comprehensive statistics and project groupings
- Error Handling: Robust CSV parsing with helpful error messages
- Time Analysis: Chronological sorting and time range reporting

## Dependencies

- Python 3.6+
- Standard library modules only (json, csv, hashlib, datetime)
