import os
import json
import requests
from requests.auth import HTTPBasicAuth

JIRA_EMAIL    = os.environ['JIRA_EMAIL']
JIRA_TOKEN    = os.environ['JIRA_API_TOKEN']
JIRA_BASE_URL = os.environ['JIRA_BASE_URL']

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = { 'Accept': 'application/json' }

# Usando customfield_10160 diretamente para evitar problema de encoding com caracteres especiais
JQL = 'project = ITSM AND issuetype = "[System] Change" AND cf[10160] is not EMPTY ORDER BY cf[10160] ASC'

def fetch_issues():
    issues = []
    start = 0
    max_results = 100
    while True:
        url = f"{JIRA_BASE_URL}/rest/api/2/search"
        # Usar POST para evitar problemas de encoding na URL
        payload = {
            'jql': JQL,
            'startAt': start,
            'maxResults': max_results,
            'fields': ['summary', 'status', 'customfield_10160', 'customfield_10161', 'customfield_10166', 'customfield_12320']
        }
        resp = requests.post(url, auth=auth, headers={**headers, 'Content-Type': 'application/json'}, json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Erro: {resp.text}")
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
        total = data.get('total', 0)
        print(f"Buscados: {start + len(batch)}/{total}")
        if start + max_results >= total:
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
