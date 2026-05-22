import os
import json
import requests
from requests.auth import HTTPBasicAuth

JIRA_EMAIL    = os.environ['JIRA_EMAIL']
JIRA_TOKEN    = os.environ['JIRA_API_TOKEN']
JIRA_BASE_URL = os.environ['JIRA_BASE_URL']

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)

JQL = 'project = ITSM AND issuetype = "[System] Change" AND cf[10160] is not EMPTY ORDER BY cf[10160] ASC'

FIELDS = ['summary', 'status', 'customfield_10160', 'customfield_10161', 'customfield_10166', 'customfield_12320']

def fetch_issues():
    issues = []
    next_page_token = None

    while True:
        url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
        payload = {
            'jql': JQL,
            'maxResults': 100,
            'fields': FIELDS
        }
        if next_page_token:
            payload['nextPageToken'] = next_page_token

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        resp = requests.post(url, auth=auth, headers=headers, json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Erro: {resp.text[:500]}")
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
                'start': f.get('customfield_10160') or '',
                'end': f.get('customfield_10161') or '',
                'tipo': tipo_obj['value'] if tipo_obj else '',
                'classificacao': classif_obj['value'] if classif_obj else ''
            })
        print(f"Buscados até agora: {len(issues)}")
        next_page_token = data.get('nextPageToken')
        if not next_page_token or data.get('isLast', True):
            break

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
