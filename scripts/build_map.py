#!/usr/bin/env python3
import re, os, datetime, sys

ROOT = os.path.dirname(os.path.dirname(__file__)) if '__file__' in globals() else os.getcwd()
LOG_DIR = os.path.join(ROOT, 'logs')
README = os.path.join(ROOT, 'README.md')
START = '<!-- LIFE_MAP_START -->'
END = '<!-- LIFE_MAP_END -->'
REPO_URL = os.environ.get('GITHUB_REPOSITORY_URL') or 'https://github.com/you/yourrepo'

class Log:
    def __init__(self, date, title='', ref_type='', ref_id=None):
        self.date = date  # yyyy-mm-dd
        self.title = title.strip() or date
        self.ref_type = ref_type  # 'Goal' or 'Struggle'
        self.ref_id = ref_id  # issue number as int

    @property
    def node_id(self):
        return 'D' + self.date.replace('-', '')

    @property
    def label(self):
        return f"{self.date} — {self.title}"

    @property
    def link(self):
        if self.ref_id:
            return f"{REPO_URL}/issues/{self.ref_id}"
        return None


def parse_header(text):
    title = ''
    ref_type = ''
    ref_id = None
    for line in text.splitlines()[:10]:  # first 10 lines
        if line.lower().startswith('title:'):
            title = line.split(':',1)[1].strip()
        elif line.lower().startswith('goal:'):
            ref_type = 'Goal'
            val = line.split(':',1)[1].strip()
            m = re.match(r'#(\d+)', val)
            if m: ref_id = int(m.group(1))
        elif line.lower().startswith('struggle:'):
            ref_type = 'Struggle'
            val = line.split(':',1)[1].strip()
            m = re.match(r'#(\d+)', val)
            if m: ref_id = int(m.group(1))
    return title, ref_type, ref_id


def collect_logs():
    items = []
    if not os.path.isdir(LOG_DIR):
        return items
    for name in os.listdir(LOG_DIR):
        if not re.match(r"\d{4}-\d{2}-\d{2}\.md$", name):
            continue
        date = name[:-3]
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            continue
        path = os.path.join(LOG_DIR, name)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        title, ref_type, ref_id = parse_header(text)
        items.append(Log(date, title, ref_type, ref_id))
    items.sort(key=lambda l: l.date)
    return items


def build_mermaid(logs):
    if not logs:
        return '_No logs yet. Add one in `logs/`_'

    lines = ['```mermaid', 'graph LR']
    # nodes
    for l in logs:
        nid = l.node_id
        label = l.label.replace('"', "'")
        lines.append(f'{nid}["{label}"]')
    # edges
    for a, b in zip(logs, logs[1:]):
        lines.append(f'{a.node_id} --> {b.node_id}')
    # clickable links
    for l in logs:
        if l.link:
            tooltip = f"{l.ref_type}: #{l.ref_id}" if l.ref_type else ''
            lines.append(f'click {l.node_id} "{l.link}" "{tooltip}"')
    lines.append('```')
    return "\n".join(lines)


def replace_section(readme_text, new_block):
    if START not in readme_text or END not in readme_text:
        raise SystemExit('Markers not found in README.')
    pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
    return pattern.sub(START + "\n" + new_block + "\n" + END, readme_text)


def main():
    logs = collect_logs()
    graph = build_mermaid(logs)
    with open(README, 'r', encoding='utf-8') as f:
        readme = f.read()
    updated = replace_section(readme, graph)
    if updated != readme:
        with open(README, 'w', encoding='utf-8') as f:
            f.write(updated)
        print('README updated.')
    else:
        print('No changes.')

if __name__ == '__main__':
    main()
