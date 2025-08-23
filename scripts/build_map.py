#!/usr/bin/env python3
import os
import re
import datetime

ROOT = os.path.dirname(os.path.dirname(__file__)) if '__file__' in globals() else os.getcwd()
LOG_DIR = os.path.join(ROOT, 'logs')
README = os.path.join(ROOT, 'README.md')
START = '<!-- LIFE_MAP_START -->'
END = '<!-- LIFE_MAP_END -->'
REPO_URL = os.environ.get('GITHUB_REPOSITORY_URL') or 'https://github.com/you/yourrepo'


class Log:
    def __init__(self, date, title='', ref_type='', ref_id=None):
        self.date = date  # YYYY-MM-DD
        self.title = title
        self.ref_type = ref_type  # 'Goal' or 'Struggle'
        self.ref_id = ref_id

    @property
    def node_id(self):
        return 'D' + self.date.replace('-', '')

    @property
    def label_id(self):
        return 'L' + self.node_id

    @property
    def link(self):
        if self.ref_id:
            return f"{REPO_URL}/issues/{self.ref_id}"
        return None


def parse_header(text):
    title = ''
    ref_type = ''
    ref_id = None
    for line in text.splitlines()[:10]:
        line_lower = line.lower()
        if line_lower.startswith('title:'):
            title = line.split(':', 1)[1].strip()
        elif line_lower.startswith('goal:'):
            ref_type = 'Goal'
            val = line.split(':', 1)[1].strip()
            m = re.match(r'#(\d+)', val)
            if m:
                ref_id = int(m.group(1))
        elif line_lower.startswith('struggle:'):
            ref_type = 'Struggle'
            val = line.split(':', 1)[1].strip()
            m = re.match(r'#(\d+)', val)
            if m:
                ref_id = int(m.group(1))
    return title, ref_type, ref_id


def collect_logs():
    logs = []
    if not os.path.isdir(LOG_DIR):
        return logs
    for fname in os.listdir(LOG_DIR):
        if not re.match(r'\d{4}-\d{2}-\d{2}\.md$', fname):
            continue
        date = fname[:-3]
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            continue
        path = os.path.join(LOG_DIR, fname)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        title, ref_type, ref_id = parse_header(text)
        logs.append(Log(date, title, ref_type, ref_id))
    logs.sort(key=lambda l: l.date)
    return logs


def build_mermaid(logs):
    lines = ["```mermaid", "graph LR"]

    # Create dot nodes
    for log in logs:
        node_id = f"D{log.date.replace('-', '')}"
        lines.append(f'  {node_id}(("●"))')  # simple bracket node

    # Connect nodes chronologically
    for i in range(1, len(logs)):
        prev_id = f"D{logs[i-1].date.replace('-', '')}"
        curr_id = f"D{logs[i].date.replace('-', '')}"
        lines.append(f'  {prev_id} --- {curr_id}')

    # Add clickable links separately
    for log in logs:
        node_id = f"D{log.date.replace('-', '')}"
        lines.append(f'  click {node_id} "logs/{log.date}.md" "{log.date}"')

    lines.append("```")
    return "\n".join(lines)


def replace_section(readme_text, new_block):
    if START not in readme_text or END not in readme_text:
        raise SystemExit("Markers not found in README.md")
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
        print("README updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
