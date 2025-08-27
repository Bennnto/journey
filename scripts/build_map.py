#!/usr/bin/env python3
import os
import re
import datetime

ROOT = os.path.dirname(os.path.dirname(__file__)) if '__file__' in globals() else os.getcwd()
LOG_DIR = os.path.join(ROOT, 'logs')
README = os.path.join(ROOT, 'README.md')
START = '<!-- LIFE_MAP_START -->'
END = '<!-- LIFE_MAP_END -->'
REPO_URL = os.environ.get('GITHUB_REPOSITORY_URL') or 'https://github.com/Bennnto/journey/'


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
    lines = ["```mermaid", "graph TD"]

    # Define styles (electric pole look)
    lines.append("  classDef mainLine stroke-width:3px,stroke:#333,fill:#fff;")
    lines.append("  classDef goal fill:#c8f7c5,stroke:#2b7a0b;")
    lines.append("  classDef struggle fill:#fdd,stroke:#c00;")

    # Create main dots (the vertical electric line)
    for log in logs:
        lines.append(f'  {log.node_id}(("●")):::mainLine')

    # Connect dots in chronological order (top-down line)
    for i in range(1, len(logs)):
        lines.append(f'  {logs[i-1].node_id} --> {logs[i].node_id}')

    # Add clickable links
    for log in logs:
        if log.link:  # If linked to a GitHub issue (Goal/Struggle)
            lines.append(f'  click {log.node_id} "{log.link}" "{log.date}"')
        else:  # Default: link to the log markdown file
            lines.append(
                f'  click {log.node_id} "{REPO_URL}/blob/main/logs/{log.date}.md" "{log.date}"'
            )

    # Branch out Goals and Struggles
    for log in logs:
        if log.ref_type == "Goal":
            g_id = f"G{log.node_id}"
            lines.append(f'  {log.node_id} --- {g_id}["🏆 {log.title}"]:::goal')
            if log.link:
                lines.append(f'  click {g_id} "{log.link}" "Goal"')
        elif log.ref_type == "Struggle":
            s_id = f"S{log.node_id}"
            lines.append(f'  {log.node_id} --- {s_id}["⚡ {log.title}"]:::struggle')
            if log.link:
                lines.append(f'  click {s_id} "{log.link}" "Struggle"')

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
