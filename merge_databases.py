"""
Merge multiple SQLite databases from different scraper runs
Useful for combining data from local PC + AWS EC2
"""

import sqlite3
import sys
from pathlib import Path

def merge_databases(source_db: str, target_db: str):
    """
    Merge source database into target database
    Skips duplicates based on agent_id
    """
    
    print(f"\n=== Merging Databases ===")
    print(f"Source: {source_db}")
    print(f"Target: {target_db}")
    
    # Connect to both databases
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    # Get all agents from source
    source_cursor.execute("SELECT * FROM agents")
    source_agents = source_cursor.fetchall()
    
    # Get column names
    column_names = [description[0] for description in source_cursor.description]
    
    print(f"\nSource database: {len(source_agents)} agents")
    
    # Count existing in target
    target_cursor.execute("SELECT COUNT(*) FROM agents")
    target_count_before = target_cursor.fetchone()[0]
    print(f"Target database (before): {target_count_before} agents")
    
    # Merge data
    added = 0
    skipped = 0
    updated = 0
    
    for agent in source_agents:
        agent_dict = dict(zip(column_names, agent))
        agent_id = agent_dict['agent_id']
        
        # Check if exists in target
        target_cursor.execute("SELECT id FROM agents WHERE agent_id=?", (agent_id,))
        exists = target_cursor.fetchone()
        
        if exists:
            # Update if source has better data (collected vs failed)
            if agent_dict.get('collection_status') == 'collected':
                # Prepare update
                set_clauses = []
                values = []
                for col in column_names:
                    if col not in ('id', 'created_at'):
                        set_clauses.append(f"{col}=?")
                        values.append(agent_dict[col])
                
                values.append(agent_id)
                query = f"UPDATE agents SET {', '.join(set_clauses)} WHERE agent_id=?"
                target_cursor.execute(query, values)
                updated += 1
            else:
                skipped += 1
        else:
            # Insert new agent
            cols = [c for c in column_names if c != 'id']
            placeholders = ','.join(['?'] * len(cols))
            values = [agent_dict[c] for c in cols]
            
            query = f"INSERT INTO agents ({','.join(cols)}) VALUES ({placeholders})"
            target_cursor.execute(query, values)
            added += 1
    
    # Commit changes
    target_conn.commit()
    
    # Get final count
    target_cursor.execute("SELECT COUNT(*) FROM agents")
    target_count_after = target_cursor.fetchone()[0]
    
    # Close connections
    source_conn.close()
    target_conn.close()
    
    print(f"\n=== Merge Complete ===")
    print(f"Added: {added} new agents")
    print(f"Updated: {updated} agents")
    print(f"Skipped: {skipped} duplicates")
    print(f"Target database (after): {target_count_after} agents")
    print(f"Net increase: +{target_count_after - target_count_before}")
    
    return {
        'added': added,
        'updated': updated,
        'skipped': skipped,
        'total': target_count_after
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Database Merge Tool - MahaRERA Scraper")
    print("="*60)
    
    # Default files
    local_db = "data/agents.db"
    aws_db = "agents_aws.db"
    
    if len(sys.argv) >= 3:
        local_db = sys.argv[1]
        aws_db = sys.argv[2]
    
    # Check files exist
    if not Path(local_db).exists():
        print(f"\n❌ Target database not found: {local_db}")
        print("This should be your main local database.")
        sys.exit(1)
    
    if not Path(aws_db).exists():
        print(f"\n❌ Source database not found: {aws_db}")
        print("Download from AWS first:")
        print(f'  scp -i "key.pem" ubuntu@IP:~/maharera-scraper/data/agents.db ./{aws_db}')
        sys.exit(1)
    
    # Backup target first
    backup_path = f"{local_db}.backup"
    print(f"\n📋 Creating backup: {backup_path}")
    import shutil
    shutil.copy2(local_db, backup_path)
    
    # Merge
    try:
        result = merge_databases(aws_db, local_db)
        print(f"\n✅ Success! Combined database has {result['total']} agents")
        print(f"   Backup saved at: {backup_path}")
    except Exception as e:
        print(f"\n❌ Error during merge: {e}")
        print(f"Your original database is safe at: {backup_path}")
        sys.exit(1)
