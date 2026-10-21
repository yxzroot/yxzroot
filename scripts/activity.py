"""Generate a small monochrome graph from public GitHub contributions."""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.request

username = 'yxzroot'
now = dt.datetime.now(dt.timezone.utc)
start = (now - dt.timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
query = '''query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){contributionsCollection(from:$from,to:$to){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}
  }}
}'''
payload = dict(query=query, variables=dict(login=username, **{'from':start.isoformat(), 'to':now.isoformat()}))
request = urllib.request.Request('https://api.github.com/graphql',
    data=json.dumps(payload).encode(),
    headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
             'Content-Type':'application/json', 'User-Agent':'yxzroot-profile'})
with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)
if data.get('errors'):
    raise RuntimeError('GitHub rejected the contribution query')
calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
days = [d for w in calendar['weeks'] for d in w['contributionDays']
        if start.date().isoformat() <= d['date'] <= now.date().isoformat()]
if not days:
    raise RuntimeError('No contribution dates returned')
counts = [d['contributionCount'] for d in days]
total, active, peak = sum(counts), sum(c > 0 for c in counts), max(1,max(counts))
left, right, top, bottom = 44, 856, 125, 230
points = [(left+i*(right-left)/max(1,len(days)-1),bottom-c/peak*(bottom-top)) for i,c in enumerate(counts)]
line = ' '.join(f'{x:.1f},{y:.1f}' for x,y in points)
area = f'{left},{bottom} '+line+f' {right},{bottom}'
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="285" viewBox="0 0 900 285" role="img" aria-label="Public GitHub activity for {username}: {total} contributions over {len(days)} days">
<rect width="900" height="285" rx="12" fill="#0d1117"/>
<g font-family="Arial,Helvetica,sans-serif">
<text x="44" y="35" font-size="13" letter-spacing="2" fill="#8b949e">RECENT ACTIVITY / LAST {len(days)} DAYS</text>
<text x="44" y="79" font-size="30" font-weight="700" fill="#e6edf3">{total}<tspan font-size="14" font-weight="400" fill="#aab3bf"> public contributions</tspan></text>
<text x="856" y="77" text-anchor="end" font-size="14" fill="#aab3bf">Active on {active} of {len(days)} days</text>''']
for fraction in [0,.5,1]:
    y=bottom-fraction*(bottom-top)
    parts.append(f'<path d="M44 {y}H856" stroke="#30363d" stroke-width="1" stroke-dasharray="3 6"/>')
parts += [f'<polygon points="{area}" fill="#cbd5e1" opacity=".10"/>',
          f'<polyline points="{line}" fill="none" stroke="#e5e7eb" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>']
for (x,y),d in zip(points,days):
    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#f0f3f6"><title>{d["date"]}: {d["contributionCount"]} contributions</title></circle>')
parts += [f'<text x="44" y="260" font-size="12" fill="#8b949e">{days[0]["date"]}</text>',
          f'<text x="856" y="260" text-anchor="end" font-size="12" fill="#8b949e">{days[-1]["date"]}</text>', '</g></svg>']
target=Path(__file__).resolve().parents[1]/'assets/activity.svg'
target.write_text('\n'.join(parts)+'\n', encoding='utf-8')
print(f'Activity graph generated: {total} public contributions, {active} active days.')
