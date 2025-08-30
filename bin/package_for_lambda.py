
#!/usr/bin/env python3
"""
Package Python code for AWS Lambda deployment.
Based on official Strands Agents AWS Lambda documentation.
"""

import os
import zipfile
from pathlib import Path


def create_lambda_package():
    """Create deployment packages for AWS Lambda."""
    current_dir = Path.cwd()
    packaging_dir = current_dir / "packaging"

    # Application code directory
    app_dir = current_dir / "src"
    app_deployment_zip = packaging_dir / "app.zip"

    # Dependencies directory
    dependencies_dir = packaging_dir / "_dependencies"
    dependencies_deployment_zip = packaging_dir / "dependencies.zip"

    # Create packaging directory if it doesn't exist
    packaging_dir.mkdir(exist_ok=True)

    print(f"Packaging application code from: {app_dir}")
    print(f"Packaging dependencies from: {dependencies_dir}")

    # Create dependencies zip (Lambda layer)
    if dependencies_dir.exists():
        print(f"Creating dependencies package: {dependencies_deployment_zip}")
        with zipfile.ZipFile(dependencies_deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(dependencies_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Create the proper structure for Lambda layers: python/lib/python3.x/site-packages/...
                    arcname = Path("python") / os.path.relpath(file_path, dependencies_dir)
                    zipf.write(file_path, arcname)
        print(f"Dependencies package created: {dependencies_deployment_zip}")
    else:
        print(f"Warning: Dependencies directory not found: {dependencies_dir}")

    # Create application code zip
    if app_dir.exists():
        print(f"Creating application package: {app_deployment_zip}")
        with zipfile.ZipFile(app_deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(app_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, app_dir)
                    zipf.write(file_path, arcname)
        print(f"Application package created: {app_deployment_zip}")
    else:
        print(f"Warning: Application directory not found: {app_dir}")

    # Print package sizes
    if dependencies_deployment_zip.exists():
        size_mb = dependencies_deployment_zip.stat().st_size / (1024 * 1024)
        print(f"Dependencies package size: {size_mb:.1f} MB")

    if app_deployment_zip.exists():
        size_mb = app_deployment_zip.stat().st_size / (1024 * 1024)
        print(f"Application package size: {size_mb:.1f} MB")


if __name__ == "__main__":
    create_lambda_package()
