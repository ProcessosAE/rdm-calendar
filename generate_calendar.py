import os
import json
import requests
from base64 import b64encode

JIRA_EMAIL    = os.environ['JIRA_EMAIL']
JIRA_TOKEN    = os.environ['JIRA_API_TOKEN']
JIRA_BASE_URL = os.environ['JIRA_BASE_URL']
FILTER_ID     = os.environ['JIRA_FILTER_ID']

auth = b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
headers = {
    'Authorization': f'Basic {auth}',
    'Content-Type': 'application/json'
}

def fetch_issues():
    issues = []
    start = 0
    max_results = 100
    while True:
        url = f"{JIRA_BASE_URL}/rest/api/3/search"
        params = {
            'jql': f'filter={FILTER_ID} ORDER BY "Data e hora de início" ASC',
            'startAt': start,
            'maxResults': max_results,
            'fields': 'summary,status,customfield_10160,customfield_10161,customfield_10166,customfield_12320'
        }
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get('issues', [])
        for i in batch:
            f = i['fields']
            tipo_obj = f.get('customfield_10166')
            classif_obj = f.get('customfield_12320')
            issues.append({
                'key': i['key'],
                'summary': f['summary'],
                'status': f['status']['name'],
                'start': f.get('customfield_10160', ''),
                'end': f.get('customfield_10161', ''),
                'tipo': tipo_obj['value'] if tipo_obj else '',
                'classificacao': classif_obj['value'] if classif_obj else ''
            })
        if start + max_results >= data['total']:
            break
        start += max_results
    print(f"Total de RDMs: {len(issues)}")
    return issues

def generate_html(issues):
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    issues_json = json.dumps(issues, ensure_ascii=False)

    import re
    content = re.sub(
        r'const ISSUES = \[.*?\];',
        f'const ISSUES = {issues_json};',
        content,
        flags=re.DOTALL
    )

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("index.html atualizado com sucesso!")

if __name__ == '__main__':
    issues = fetch_issues()
    generate_html(issues)
