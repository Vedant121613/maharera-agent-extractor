from database.database import Database

db = Database('data/agents.db')
conn = db._connect()

# Get recent entries
cursor = conn.execute("""
    SELECT agent_id, agent_name, mobile, email, collection_status, collected_at
    FROM agents 
    WHERE collected_at IS NOT NULL
    ORDER BY collected_at DESC 
    LIMIT 15
""")

print("\n=== Last 15 Collected Agents (Most Recent First) ===")
for row in cursor.fetchall():
    agent_id, name, mobile, email, status, collected_at = row
    mobile = mobile or "—"
    email = (email or "—")[:30]
    print(f"{agent_id} | {name[:30]:30} | {mobile:15} | {email:30} | {collected_at}")

# Count by hour
cursor = conn.execute("""
    SELECT 
        substr(collected_at, 1, 13) as hour,
        COUNT(*) as count
    FROM agents 
    WHERE collected_at IS NOT NULL
    GROUP BY hour
    ORDER BY hour DESC
    LIMIT 5
""")

print("\n=== Collection Rate (Last 5 Hours) ===")
for row in cursor.fetchall():
    print(f"{row[0]} → {row[1]} agents")
