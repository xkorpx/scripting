"""
This script assumes it is being run from within a virtual environment.
Usage:
    python devpi.py --server https://server-ip --username USER --password PASS --index INDEX
"""

import argparse
import subprocess
import sys
import os
import shutil
from pathlib import Path


GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'


def run_command(cmd, check=True, capture_output=True):
    print(f"  Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        capture_output=capture_output,
        text=True,
        check=False
    )

    if check and result.returncode != 0:
        print(f"{RED}Command failed with exit code {result.returncode}{RESET}", file=sys.stderr)
        if result.stderr:
            print(f"stderr: {result.stderr}", file=sys.stderr)
        if result.stdout:
            print(f"stdout: {result.stdout}")
        raise subprocess.CalledProcessError(result.returncode, cmd)

    return result


def test_login(server, username, password):
    print("Testing login to devpi server...")

    try:
        run_command(["devpi", "use", server])
        print(f"Connected to server: {server}")

        run_command(["devpi", "login", username, "--password", password])
        print(f"Successfully logged in as: {username}")

        return True
    except subprocess.CalledProcessError:
        print(f"{RED}Login test failed{RESET}", file=sys.stderr)
        return False


def test_upload(index, package_dir):
    print("Testing package upload...")

    try:
        run_command(["devpi", "use", index])
        print(f"Using index: {index}")

        original_dir = os.getcwd()
        os.chdir(package_dir)

        try:
            for dir_name in ["build", "dist", "*.egg-info"]:
                if os.path.exists(dir_name):
                    shutil.rmtree(dir_name, ignore_errors=True)

            run_command([sys.executable, "setup.py", "sdist", "bdist_wheel"])
            print("Package built successfully")

            run_command(["devpi", "upload"])
            print("Package uploaded successfully")

            return True
        finally:
            os.chdir(original_dir)

    except subprocess.CalledProcessError:
        print(f"{RED}Upload test failed{RESET}", file=sys.stderr)
        return False


def test_download(package_name, package_version):
    print("Testing package download and installation...")

    try:
        package_spec = f"{package_name}=={package_version}"

        print(f"  Installing {package_spec} from devpi...")
        run_command([sys.executable, "-m", "pip", "install", package_spec])

        print(f"Package {package_spec} installed successfully")
        print("  Cleaning up test package...")
        run_command([sys.executable, "-m", "pip", "uninstall", "-y", package_name], capture_output=True)

        return True

    except subprocess.CalledProcessError:
        print(f"{RED}Download/install test failed{RESET}", file=sys.stderr)
        try:
            run_command([sys.executable, "-m", "pip", "uninstall", "-y", package_name], capture_output=True, check=False)
        except:
            pass
        return False


def main():
    parser = argparse.ArgumentParser(description="Test devpi server functionality (login, upload, download)",formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python devpi.py --server https://blah.com --username testuser --password testpass --index testuser/dev
  python devpi.py -s https://blah.com -u testuser -p testpass -i testuser/dev
        """
    )
    parser.add_argument("-s", "--server",required=True,help="DevPI server URL (e.g., https://blahblah.blah)")
    parser.add_argument("-u", "--username",required=True,help="DevPI username")
    parser.add_argument("-p", "--password",required=True,help="DevPI password")
    parser.add_argument("-i", "--index",required=True,help="DevPI index (e.g., username/indexname)")

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    package_dir = script_dir / "test-package"
    package_name = "hello-devpi-test"
    package_version = "0.0.1"

    if not package_dir.exists():
        print(f"{RED}Package directory not found: {package_dir}{RESET}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"Server: {args.server}")
    print(f"Username: {args.username}")
    print(f"Index: {args.index}")
    print(f"Package: {package_name} v{package_version}")
    print("=" * 60 + "\n")

    results = {}

    results['login'] = test_login(args.server, args.username, args.password)
    print()

    if results['login']:
        results['upload'] = test_upload(args.index, package_dir)
    else:
        print("Skipping upload test due to login failure")
        results['upload'] = False
    print()

    if results['upload']:
        results['download'] = test_download(package_name, package_version)
    else:
        print("Skipping download test due to upload failure")
        results['download'] = False
    print()

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, result in results.items():
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"  {test_name.capitalize()}: {status}")
        if not result:
            all_passed = False

    print("=" * 60 + "\n")

    if all_passed:
        print(f"{GREEN}All tests passed!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}Some tests failed{RESET}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
