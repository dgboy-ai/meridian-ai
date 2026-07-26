import sys; sys.path.insert(0, '.')
from backend.replay import ReplayDriver
rd = ReplayDriver()
incidents = rd.list_incidents()
print(f'Replay incidents: {len(incidents)}')
for inc in incidents:
    print(f'  {inc["id"]}: {inc["title"]} ({inc["severity"]})')
