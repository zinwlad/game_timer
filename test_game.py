import time
import sys

print("Test game is running...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Test game closed.")
    sys.exit(0)
