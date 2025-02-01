import os
from pathlib import Path

package_path = Path(__file__).resolve().parent
module_name = os.path.basename(package_path)
base_path = os.path.dirname(package_path)
