"""Live monitoring of database writes"""
import time
from database.database import Database

db = Database('data/agents.db')
prev_count = 0

print("\n=== Live Database Monitor (Ctrl+C to stop) ===\n")

try:
    while True:
        stats = db.get_stats()
        collected = stats['collected']
        
        if collected != prev_count:
            delta = collected - prev_count
            print(f"[{time.strftime('%H:%M:%S')}] Total: {collected} (+{delta} new)")
            prev_count = collected
        
        time.sleep(2)
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
    print(f"Final count: {prev_count} agents collected")
