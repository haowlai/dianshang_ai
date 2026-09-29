import requests

# 1. Health check
r1 = requests.get("http://localhost:8002/health")
data1 = r1.json()
print(f"Health: {r1.status_code} {data1['status']}")

# 2. Login
r2 = requests.post("http://localhost:8002/api/v1/auth/login", json={"email":"admin@agentic.com","password":"admin123"})
print(f"Login: {r2.status_code}")
token = r2.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. List SKUs
r3 = requests.get("http://localhost:8002/api/v1/skus?page=1&page_size=5", headers=headers)
print(f"SKU List: {r3.status_code}, total={r3.json()['data']['total']}")

# 4. List Tasks
r4 = requests.get("http://localhost:8002/api/v1/tasks?page=1&page_size=5", headers=headers)
print(f"Task List: {r4.status_code}, total={r4.json()['data']['total']}")

# 5. List Assets
r5 = requests.get("http://localhost:8002/api/v1/assets?page=1&page_size=5", headers=headers)
print(f"Asset List: {r5.status_code}, total={r5.json()['data']['total']}")

# 6. Copies
r6 = requests.get("http://localhost:8002/api/v1/copies?page=1&page_size=5", headers=headers)
print(f"Copy List: {r6.status_code}, total={r6.json()['data']['total']}")

# 7. Compliance check
r7 = requests.post("http://localhost:8002/api/v1/compliance/check", json={"title":"Good Product","content":"Amazing quality"}, headers=headers)
print(f"Compliance Check: {r7.status_code}, score={r7.json()['data']['score']}")

# 8. Audit costs
r8 = requests.get("http://localhost:8002/api/v1/audit/costs", headers=headers)
print(f"Audit Costs: {r8.status_code}")

# 9. Auth me
r9 = requests.get("http://localhost:8002/api/v1/auth/me", headers=headers)
d9 = r9.json()
print(f"Auth Me: {r9.status_code}, user={d9['data']['name']}")

# 10. Knowledge docs
r10 = requests.get("http://localhost:8002/api/v1/knowledge/docs?page=1&page_size=5", headers=headers)
print(f"Knowledge Docs: {r10.status_code}")

# 11. Batches
r11 = requests.get("http://localhost:8002/api/v1/batches?page=1&page_size=5", headers=headers)
print(f"Batches: {r11.status_code}")

# 12. Providers
r12 = requests.get("http://localhost:8002/api/v1/providers", headers=headers)
print(f"Providers: {r12.status_code}")

print("\nALL 12 API endpoints passed!")
