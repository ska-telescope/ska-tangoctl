"""Global values."""

import datetime
import os

now = datetime.datetime.now()
CURRENT_TIME: str = now.strftime("%Y-%m-%d %H:%M:%S")
EOL: str = "\n"
HOME_PATH: str = os.getenv("HOME", "")
PYTHON_PATH: str = os.getenv("PYTHONPATH", "")
