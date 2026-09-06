from database.database import Database

db = Database('data/agents.db')
stats = db.get_stats()

print(f"\n=== Database Stats ===")
print(f"Total agents: {stats['total']}")
print(f"Collected: {stats['collected']}")
print(f"Failed: {stats['failed']}")
print(f"Pending: {stats['pending']}")

# Show last 5 collected
conn = db._connect()
cursor = conn.execute("""
    SELECT agent_id, agent_name, mobile, email, city
    FROM agents 
    WHERE collection_status = 'collected'
    ORDER BY collected_at DESC
    LIMIT 5
""")

print(f"\n=== Last 5 Collected ===")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1][:30]:30} | {row[2] or '—':15} | {row[3] or '—':30}")
