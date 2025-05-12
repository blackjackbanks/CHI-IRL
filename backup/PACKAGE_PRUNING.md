# Package Size Optimization

## Purpose
This script helps reduce the package size of the virtual environment while maintaining core functionality.

## Steps to Prune Packages

1. Activate your virtual environment
```bash
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows
```

2. Run the pruning script
```bash
python package_size_prune.py
```

## What Gets Removed
- Large scientific computing libraries (`numpy`, `pandas`)
- Unnecessary Google Cloud libraries
- Redundant Google API dependencies
- Large gRPC and protobuf packages

## What Gets Preserved
- Web scraping capabilities
- Google Calendar integration
- Web API functionality

## Troubleshooting
- If any core functionality breaks, reinstall requirements:
```bash
pip install -r requirements-slim.txt
```

## Recommended Package Management
- Regularly review and update `requirements-slim.txt`
- Use `pip freeze > requirements.txt` to capture exact versions
- Consider using lightweight alternatives for heavy libraries
