import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.db import init_engine, session_scope, PullRecord
except ImportError:
    try:
        from backend.utils.db import init_engine, session_scope, PullRecord
    except ImportError:
        print("Could not import utils.db")
        sys.exit(1)

from sqlalchemy import func, select

def deduplicate():
    print("Initializing DB...")
    engine = init_engine()
    if not engine:
        print("Failed to initialize DB engine. Check environment variables.")
        return

    print("Checking for duplicates...")
    try:
        with session_scope() as s:
            # Get duplicate URLs
            dupes = s.execute(
                select(PullRecord.url, func.count(PullRecord.id))
                .group_by(PullRecord.url)
                .having(func.count(PullRecord.id) > 1)
            ).all()
            
            if not dupes:
                print("No duplicates found.")
                return

            print(f"Found {len(dupes)} URLs with duplicates.")
            
            deleted_count = 0
            for url, count in dupes:
                # Get all records for this URL, ordered by pull_time desc (latest first)
                records = s.execute(
                    select(PullRecord)
                    .filter_by(url=url)
                    .order_by(PullRecord.pull_time.desc(), PullRecord.id.desc())
                ).scalars().all()
                
                # Keep the first one (latest), delete others
                if len(records) > 1:
                    to_delete = records[1:]
                    for r in to_delete:
                        s.delete(r)
                        deleted_count += 1
            
            print(f"Deduplication complete. Deleted {deleted_count} records.")
    except Exception as e:
        print(f"Error during deduplication: {e}")

if __name__ == "__main__":
    deduplicate()
