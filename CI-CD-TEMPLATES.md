# CI/CD Integration Templates

## Azure DevOps Pipeline

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - 'database/stored-procedures/*.sql'

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.8'
  displayName: 'Use Python 3.8'

- script: |
    pip install -r requirements.txt
  displayName: 'Install Dependencies'

- script: |
    python sp_analyze.py analyze "database/stored-procedures/*.sql" \
      --batch \
      --json \
      --fail-on-quality --min-quality 80 \
      --fail-on-security --min-security 85
  displayName: 'Analyze Stored Procedures'

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: '$(Build.SourcesDirectory)'
    ArtifactName: 'sp-analysis-reports'
  condition: always()
  displayName: 'Publish Analysis Reports'
```

## GitHub Actions

```yaml
# .github/workflows/sp-analysis.yml
name: SQL SP Quality Gate

on:
  pull_request:
    paths:
      - 'database/stored-procedures/**.sql'
  push:
    branches: [ main, develop ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Analyze Stored Procedures
      run: |
        python sp_analyze.py analyze "database/stored-procedures/*.sql" \
          --batch \
          --html \
          --json \
          --markdown \
          --csv summary.csv \
          --fail-on-quality --min-quality 80 \
          --fail-on-security --min-security 85
    
    - name: Upload Reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: sp-analysis-reports
        path: |
          **/*_report.html
          **/*_analysis.json
          **/*_report.md
          summary.csv
    
    - name: Comment PR
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request'
      with:
        script: |
          const fs = require('fs');
          const summary = fs.readFileSync('summary.csv', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.name,
            body: '## 📊 SP Analysis Results\n\n```\n' + summary + '\n```'
          });
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - analyze

sp-quality-gate:
  stage: analyze
  image: python:3.8
  script:
    - pip install -r requirements.txt
    - python sp_analyze.py analyze "database/stored-procedures/*.sql" 
        --batch 
        --json 
        --fail-on-quality --min-quality 80 
        --fail-on-security --min-security 85
  artifacts:
    when: always
    paths:
      - '**/*_report.html'
      - '**/*_analysis.json'
    expire_in: 30 days
  only:
    changes:
      - database/stored-procedures/*.sql
```

## Usage Instructions

1. **Azure DevOps**: Place `azure-pipelines.yml` in repository root
2. **GitHub Actions**: Place in `.github/workflows/sp-analysis.yml`
3. **GitLab**: Place `.gitlab-ci.yml` in repository root

## Customization

Adjust thresholds based on your needs:
- `--min-quality`: Minimum quality score (default: 70)
- `--min-security`: Minimum security score (default: 80)
- `--min-performance`: Minimum performance score (default: 70)

## Benefits

✅ Automated quality gates
✅ Prevents low-quality code merges
✅ Security vulnerability blocking
✅ Trend tracking via artifacts
✅ PR comments with results
