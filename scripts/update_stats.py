"""Render public GitHub stats as local SVGs. Python standard library only."""
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import json
import os
import urllib.request

USER = 'Hossam-Bakr'
ROOT = Path(__file__).resolve().parents[1]
HEADERS = {'User-Agent': f'{USER}-profile', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
if os.environ.get('GITHUB_TOKEN'):
    HEADERS['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']

def get(path):
    req = urllib.request.Request('https://api.github.com' + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def label(x, y, value, size, color, weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'

def main():
    profile = get(f'/users/{USER}')
    repos = []
    page = 1
    while True:
        batch = get(f'/users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    owned = [r for r in repos if not r['fork']]
    languages = Counter()
    for repo in owned:
        languages.update(get(f'/repos/{USER}/{repo["name"]}/languages'))
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    total = sum(languages.values())
    colors = ['#65adff', '#55d7ce', '#b4a3ff', '#f5ce73', '#ed92b7', '#8393ab']
    top = languages.most_common(5)
    rest = total - sum(v for _, v in top)
    if rest:
        top.append(('Other', rest))
    for theme in ['dark', 'light']:
        bg, ink, muted, edge = ('#111f33','#edf5ff','#a8bdd8','#2a3e59') if theme=='dark' else ('#f1f6fc','#122a46','#4c6380','#c4d8ec')
        accent = '#75b6ff' if theme=='dark' else '#1965bd'
        body = f'<rect x="1" y="1" width="758" height="466" rx="16" fill="{bg}" stroke="{edge}"/>'
        body += label(28,38,'PUBLIC GITHUB SNAPSHOT',13,accent,600)
        metrics = [(28,profile['public_repos'],'Public repos'),(275,sum(r['stargazers_count'] for r in owned),'Stars earned'),(522,profile['followers'],'Followers')]
        for x,value,name in metrics:
            body += label(x,95,value,38,ink,700)+label(x,123,name,14,muted)
        body += f'<path d="M28 148H732" stroke="{edge}"/>'
        body += label(28,181,'Languages across my repositories',19,ink,600)
        if total:
            x = 28
            for i,(name,value) in enumerate(top):
                width = 704*value/total
                body += f'<rect x="{x:.2f}" y="201" width="{width:.2f}" height="12" fill="{colors[i]}"/>'
                x += width
            for i,(name,value) in enumerate(top):
                x,y = 28+(i%2)*352,251+(i//2)*37
                body += f'<circle cx="{x+5}" cy="{y-5}" r="5" fill="{colors[i]}"/>'
                body += label(x+18,y,f'{name}  {value/total:.1%}',15,ink)
        else:
            body += label(28,251,'No public language data available yet.',15,muted)
        body += label(28,389,f'{len(owned)} owned, non-fork public repositories analyzed',13,muted)
        body += label(28,414,'Language share by code bytes · GitHub REST API',13,muted)
        body += label(28,441,f'Updated {stamp} UTC',12,muted)
        out = '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="468" viewBox="0 0 760 468"><style>text{font-family:Segoe UI,Arial,sans-serif}</style>'+body+'</svg>'
        (ROOT/'assets'/f'github-{theme}.svg').write_text(out,encoding='utf-8')
        mobile = f'<rect x="1" y="1" width="638" height="668" rx="16" fill="{bg}" stroke="{edge}"/>'
        mobile += label(26,44,'PUBLIC GITHUB SNAPSHOT',20,accent,600)
        for i,(_,value,name) in enumerate(metrics):
            x=26+i*206
            mobile += label(x,116,value,46,ink,700)+label(x,151,name,21,muted)
        mobile += f'<path d="M26 183H614" stroke="{edge}"/>'
        mobile += label(26,227,'Languages across my repositories',25,ink,600)
        x=26
        for i,(name,value) in enumerate(top):
            width=588*value/total
            mobile += f'<rect x="{x:.2f}" y="250" width="{width:.2f}" height="16" fill="{colors[i]}"/>'
            x+=width
            y=310+i*42
            mobile += f'<circle cx="33" cy="{y-7}" r="6" fill="{colors[i]}"/>'
            mobile += label(52,y,f'{name}  {value/total:.1%}',23,ink)
        mobile += label(26,587,f'{len(owned)} owned, non-fork public repositories',19,muted)
        mobile += label(26,618,'Share by code bytes · GitHub REST API',19,muted)
        mobile += label(26,648,f'Updated {stamp} UTC',18,muted)
        (ROOT/'assets'/f'github-{theme}-mobile.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="670" viewBox="0 0 640 670"><style>text{font-family:Segoe UI,Arial,sans-serif}</style>'+mobile+'</svg>',encoding='utf-8')
    print(f'Updated {stamp}: {len(owned)} owned repositories, {len(languages)} languages.')

if __name__ == '__main__':
    main()
