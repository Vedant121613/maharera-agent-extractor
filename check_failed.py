from database.database import Database

db = Database('data/agents.db')
conn = db._connect()

# Show failed agents
cursor = conn.execute("""
    SELECT agent_id, agent_name, failure_reason
    FROM agents 
    WHERE collection_status = 'failed'
    ORDER BY agent_id
""")

print("\n=== Failed Agents ===")
failed = cursor.fetchall()
for row in failed:
    print(f"  {row[0]} | {row[1][:40]:40} | {row[2][:50]}")

print(f"\nTotal failed: {len(failed)}")

# Show last 10 collected successfully
cursor = conn.execute("""
    SELECT agent_id, agent_name, mobile, email
    FROM agents 
    WHERE collection_status = 'collected'
    ORDER BY collected_at DESC
    LIMIT 10
""")

print(f"\n=== Last 10 Successfully Collected ===")
for row in cursor.fetchall():
    mobile = row[2] or '—'
    email = row[3] or '—'
    print(f"  {row[0]} | {row[1][:30]:30} | {mobile:15} | {email[:30]:30}")
