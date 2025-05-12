import os
import subprocess
import shutil

def get_package_sizes(path):
    """Get sizes of packages in the specified path."""
    package_sizes = {}
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                       for dirpath, _, filenames in os.walk(full_path) 
                       for filename in filenames)
            package_sizes[item] = size / (1024 * 1024)  # Convert to MB
    return sorted(package_sizes.items(), key=lambda x: x[1], reverse=True)

def prune_packages(venv_path, max_size_mb=250):
    """Prune packages to stay under max size."""
    site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
    
    # Get package sizes
    sizes = get_package_sizes(site_packages)
    
    # Print current total size
    total_size = sum(size for _, size in sizes)
    print(f"Current total package size: {total_size:.2f} MB")
    
    # Packages to keep (core functionality)
    essential_packages = {
        'flask', 'flask-cors', 'requests', 
        'beautifulsoup4', 'python-dateutil', 
        'google-api-python-client', 'google-auth-oauthlib', 
        'python-dotenv'
    }
    
    # Packages to remove
    removable_packages = [
        'numpy', 'pandas', 'google-cloud-bigquery', 
        'grpcio', 'protobuf', 'google-auth', 
        'google-auth-httplib2', 'google-cloud-core',
        'google-resumable-media', 'googleapis-common-protos'
    ]
    
    removed_size = 0
    for package in removable_packages:
        for pkg_name, size in sizes:
            if package in pkg_name.lower():
                pkg_path = os.path.join(site_packages, pkg_name)
                try:
                    shutil.rmtree(pkg_path)
                    removed_size += size
                    print(f"Removed {pkg_name}: {size:.2f} MB")
                except Exception as e:
                    print(f"Could not remove {pkg_name}: {e}")
    
    # Uninstall packages
    for package in removable_packages:
        try:
            subprocess.run(['pip', 'uninstall', '-y', package], check=True)
        except subprocess.CalledProcessError:
            print(f"Could not uninstall {package}")
    
    # Verify new size
    new_sizes = get_package_sizes(site_packages)
    new_total_size = sum(size for _, size in new_sizes)
    print(f"New total package size: {new_total_size:.2f} MB")
    print(f"Removed: {removed_size:.2f} MB")

    # Reinstall requirements to ensure core functionality
    try:
        subprocess.run(['pip', 'install', '-r', 'requirements-slim.txt'], check=True)
        print("Reinstalled core requirements")
    except subprocess.CalledProcessError:
        print("Error reinstalling requirements")

def main():
    # Path to your virtual environment
    venv_path = r'C:\Users\Lenovo\OneDrive\Desktop\CHIIRL\venv'
    prune_packages(venv_path)

if __name__ == '__main__':
    main()
