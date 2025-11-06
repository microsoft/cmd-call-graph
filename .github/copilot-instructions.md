# GitHub Copilot Instructions for cmd-call-graph

## Repository Overview
This repository contains tools and utilities for analyzing and visualizing call graphs in Windows batch files (.cmd, .bat) and command scripts.

## Project Context
- **Purpose**: Generate and analyze call graphs for Windows command/batch scripts
- **Primary Languages**: The codebase likely includes parsers and analyzers for CMD/BAT files
- **Target Platform**: Windows command line environments

## Coding Standards and Conventions

### General Guidelines
- Follow existing code patterns and style in the repository
- Maintain backward compatibility with existing command line interfaces
- Ensure all code works on Windows platforms
- Include appropriate error handling for file I/O operations

### Command/Batch File Parsing
- Handle both .cmd and .bat file extensions
- Support common batch file constructs (CALL, GOTO, labels, etc.)
- Account for case-insensitive command names in Windows
- Handle environment variable expansion appropriately

### Graph Generation
- Use standard graph notation and formats where applicable
- Support multiple output formats if possible (DOT, JSON, etc.)
- Ensure graph visualization is clear and readable

## Key Components
- **Parser**: Handles parsing of CMD/BAT files
- **Analyzer**: Builds call relationships and dependencies
- **Visualizer**: Generates graph outputs

## Testing Guidelines
- Test with various complexity levels of batch files
- Include edge cases like recursive calls, conditional calls
- Verify cross-file call detection works correctly
- Test on different Windows versions when applicable

## Documentation
- Include examples of usage in code comments
- Document any limitations or known issues
- Provide clear error messages for user-facing components

## Security Considerations
- Sanitize file paths to prevent directory traversal
- Be cautious with executing or evaluating batch file content
- Validate input files before processing

## Performance Considerations
- Optimize for large batch file repositories
- Consider memory usage when processing multiple files
- Implement caching where appropriate for repeated analyses

## Common Patterns to Follow
- Use consistent naming for graph nodes (e.g., script names, labels)
- Maintain a clear separation between parsing and visualization logic
- Follow Windows path conventions and handle both forward and backslashes

## Dependencies and Libraries
- List any specific libraries used for graph generation
- Note any Windows-specific dependencies
- Specify minimum supported Windows/PowerShell versions if applicable

## When Generating Code
- Prefer clarity over brevity for batch file parsing logic
- Include helpful comments explaining Windows-specific behaviors
- Consider cross-platform compatibility where feasible
- Add appropriate logging for debugging call graph generation

## Areas Needing Special Attention
- Complex batch file constructs (nested calls, dynamic label generation)
- Cross-file dependencies and external script calls
- Performance optimization for large codebases
- Edge cases in Windows command parsing
