# CSV Dependency Graph Comparator

A Python script that analyzes CSV dependency graph data to identify projects where the same code revision produces different dependency analysis results (alternating dependency graphs).

## Overview

This tool helps identify non-deterministic dependency analysis behavior by:
- Parsing CSV data containing dependency graph information
- Grouping analyses by project and code revision
- Detecting cases where identical source code produces different dependency signatures
- Generating detailed Excel reports with comprehensive analysis

## Key Features

- **Source Unit Matching**: Properly matches source units by OriginPaths rather than by type
- **Path Normalization**: Only normalizes build environment paths while preserving dependency identifiers
- **Comprehensive Analysis**: Tracks direct imports, transitive dependencies, and build success status
- **Temporal Analysis**: Considers timestamps for reproducibility assessment
- **Detailed Reporting**: Generates Excel reports with summary and detailed comparison sheets

## Installation

### Requirements
- Python 3.6+
- Required packages: `openpyxl`

```bash
pip install openpyxl
# or if using system Python on macOS:
python3 -m pip install --break-system-packages openpyxl
```

## Usage

### Command Line
```bash
python3 csv_dependency_graph_comparator_v2.py <csv_file> [--excel <output_file>]
```

### Arguments
- `csv_file`: Path to CSV file containing dependency graph data (required)
- `--excel`: Generate Excel report to specified path (optional)

### Example
```bash
python3 csv_dependency_graph_comparator_v2.py data.csv --excel alternating_graphs.xlsx
```

## CSV Format

Expected CSV format with header:
```
build id,locator,createdAt,data
```

Or without build ID:
```
locator,createdAt,data
```

Where:
- `build id`: Unique identifier for the build/scan (optional)
- `locator`: Project locator in format `custom+<org-id>/<project-title>$<revision>`
- `createdAt`: Timestamp when analysis was created (ISO 8601 format)
- `data`: JSON string containing full dependency graph data

## What It Detects

### High Priority Issues
**Same Revision Alternating Dependency Graphs**: Cases where:
- Same project and code revision
- Multiple dependency analysis scans
- Different dependency graph signatures

This indicates non-deterministic behavior in the dependency analysis process.

## Excel Report Structure

### Summary Sheet
- Total alternating revisions found
- Project overview with scan counts and build IDs
- Time ranges for each alternating case

### Detailed Analysis Sheet
For each alternating case:
- **Graph Comparisons**: Side-by-side comparison of different dependency graphs
- **Related Builds**: All build IDs that produce the same graph signature
- **Dependency Analysis**: 
  - Common dependencies between graphs
  - Dependencies unique to each graph
  - Direct vs transitive dependency counts
- **Origin Path Analysis**: Comparison of source unit origin paths

## Key Improvements Over V1

1. **Reduced False Positives**: From 197 to ~15 true alternating cases (92% reduction)
2. **Proper Source Unit Matching**: Uses OriginPaths instead of treating projects as monolithic units
3. **Better Path Normalization**: Only normalizes build environment paths, preserves dependency identifiers
4. **Comprehensive Build Tracking**: Shows all related build IDs for each graph signature
5. **Enhanced Temporal Analysis**: Better handling of timestamps and build sequences

## Algorithm Details

### Dependency Graph Signature Generation
1. **Source Unit Processing**: Each source unit is processed individually based on OriginPaths
2. **Dependency Extraction**: 
   - Direct imports from `Build.Imports`
   - Transitive dependencies from `Build.Dependencies`
3. **Path Normalization**: Only temporary build paths (`/tmp/tmp*/unpacked/`) are normalized
4. **Signature Creation**: SHA256 hash of normalized dependency data

### Comparison Logic
1. **Project Grouping**: Group analyses by `<org-id>/<project-title>`
2. **Revision Grouping**: Group by code revision within each project
3. **Signature Analysis**: Generate dependency graph signatures for each analysis
4. **Alternating Detection**: Identify revisions with multiple unique signatures

## Output Example

```
🚨 HIGH PRIORITY - Same Revision Alternating Dependency Graphs: 15
   These revisions have the SAME code but DIFFERENT dependency analysis results!
   • 123/some-project.git @ revision
     3 scans → 2 different dependency graphs
     Build IDs: 121212, 12222, 222222
     Time range: 2025-08-19 16:43:18.025000+00:00 to 2025-08-19 20:48:26.854000+00:00
```

## Technical Details

### Classes
- `SourceUnitSignature`: Represents a normalized signature for a single source unit
- `ProjectDependencyGraph`: Represents a project's complete dependency graph organized by OriginPaths
- `ParsedLocator`: Parsed project locator with org, project, and revision components

### Key Methods
- `get_signature()`: Generates SHA256 hash of dependency data
- `is_equivalent_to()`: Compares two dependency graphs for equivalence
- `compare_with()`: Detailed comparison between two graphs
- `analyze_project_revisions()`: Main analysis logic for finding alternating patterns

## Troubleshooting

### Common Issues
1. **CSV Field Size Error**: Script automatically handles large JSON fields (10MB limit)
2. **Missing openpyxl**: Install with `pip install openpyxl`
3. **Multiple Source Units Warning**: Normal for projects with duplicate OriginPaths

### Performance
- Processes ~10,000 project analyses efficiently
- Memory usage scales with unique project-revision combinations
- Excel generation time depends on number of alternating cases found
