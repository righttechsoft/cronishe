#!/usr/bin/env python3
"""
Example job script for testing cronishe scheduler.
This script prints some output and exits with success.
"""
import time
import sys
from datetime import datetime

print(f"Job started at {datetime.now()}")
print("Processing step 1...")
time.sleep(1)
print("Processing step 2...")
time.sleep(1)
print("Processing step 3...")
time.sleep(1)
print(f"Job completed successfully at {datetime.now()}")

sys.exit(0)
