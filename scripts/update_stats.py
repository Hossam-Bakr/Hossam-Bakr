"""Render compact public GitHub statistics. Python standard library only."""
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

def render(profile, owned, languages, stamp, theme, mobile):
    bg, ink, muted, edge = ('#111f33','#edf5ff','#a8bdd8','#2a3e59') if theme=='dark' else ('#f1f6fc','#122a46','#4c6380','#c4d8ec')
    accent = '#75b6ff' if theme=='dark' else '#1965bd'
    colors = ['#65adff', '#55d7ce', '#b4a3ff', '#f5ce73', '#ed92b7', '#8393ab']
    total = sum(languages.values())
    top = languages.most_common(5)
    rest = total - sum(value for _, value in top)
    if rest:
        top.append(('Other', rest))
    width, height = (600,250) if mobile else (900,144)
    body = f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="8" fill="{bg}" stroke="{edge}"/>'
    metrics = [(profile['public_repos'],'Repositories'),(sum(r['stargazers_count'] for r in owned),'Stars'),(profile['followers'],'Followers')]
    if mobile:
        for i,(value,name) in enumerate(metrics):
            x=20+i*195
            body+=label(x,37,value,27,ink,600)+label(x,66,name,19,muted)
        body+=f'<path d="M20 83H580" stroke="{edge}"/>'
        body+=label(20,111,'Languages · public code',19,accent,600)
        bar_x,bar_y,bar_width=20,126,560
    else:
        body+=label(18,27,'Public activity',15,accent,600)
        for i,(value,name) in enumerate(metrics):
            x=18+i*95
            body+=label(x,62,value,26,ink,600)+label(x,84,name,12,muted)
        body+=label(18,123,f'Updated {stamp} UTC',11,muted)
        body+=f'<path d="M309 18V126" stroke="{edge}"/>'
        body+=label(332,27,'Languages · owned, non-fork repositories',15,accent,600)
        bar_x,bar_y,bar_width=332,43,548
    cursor=bar_x
    if total:
        for i,(name,value) in enumerate(top):
            segment=bar_width*value/total
            body+=f'<rect x="{cursor:.2f}" y="{bar_y}" width="{segment:.2f}" height="8" fill="{colors[i]}"/>'
            cursor+=segment
            x=(20+(i%2)*290) if mobile else (332+(i%3)*184)
            y=(163+(i//2)*28) if mobile else (79+(i//3)*26)
            body+=f'<circle cx="{x+4}" cy="{y-5}" r="4" fill="{colors[i]}"/>'
            body+=label(x+16,y,f'{name} {value/total:.1%}',19 if mobile else 13,ink)
    else:
        body+=label(bar_x,bar_y+32,'No public language data available.',19 if mobile else 13,muted)
    if mobile:
        body+=label(20,238,f'Code bytes · non-fork repos · {stamp} UTC',15,muted)
    else:
        body+=label(332,128,'Distribution by code bytes',11,muted)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><style>text{{font-family:Segoe UI,Arial,sans-serif}}</style>{body}</svg>'

def main():
    profile=get(f'/users/{USER}')
    repos=[]
    page=1
    while True:
        batch=get(f'/users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch)<100:
            break
        page+=1
    owned=[r for r in repos if not r['fork']]
    languages=Counter()
    for repo in owned:
        languages.update(get(f'/repos/{USER}/{repo["name"]}/languages'))
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for theme in ['dark','light']:
        for mobile in [False,True]:
            file=ROOT/'assets'/f'github-{theme}{"-mobile" if mobile else ""}.svg'
            file.write_text(render(profile,owned,languages,stamp,theme,mobile),encoding='utf-8')
    print(f'Updated {stamp}: {len(owned)} owned repositories, {len(languages)} languages.')

if __name__=='__main__':
    main()
