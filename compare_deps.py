import tomllib

with open('E:/PROJECT/MARQUEE/ipo-intelligence-agent/backend/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)

pyproject_deps = {}
if 'project' in data and 'dependencies' in data['project']:
    for dep in data['project']['dependencies']:
        if '==' in dep:
            name, version = dep.split('==', 1)
            pyproject_deps[name.strip().lower().replace('-', '_')] = version.strip()

print(f"Found {len(pyproject_deps)} dependencies in pyproject.toml")

with open('E:/PROJECT/MARQUEE/ipo-intelligence-agent/backend/requirements.txt', 'r') as f:
    reqs = {}
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '==' in line:
            name, version = line.split('==', 1)
            reqs[name.strip().lower().replace('-', '_')] = version.strip()

print(f"Found {len(reqs)} dependencies in requirements.txt")

print('\n=== Version Differences ===')
all_names = set(pyproject_deps.keys()) | set(reqs.keys())
for name in sorted(all_names):
    pv = pyproject_deps.get(name, 'NOT IN PYPROJECT')
    rv = reqs.get(name, 'NOT IN REQUIREMENTS')
    if pv != rv:
        print(f'{name}: pyproject={pv} vs requirements={rv}')

print('\n=== Only in pyproject.toml ===')
for name in sorted(set(pyproject_deps.keys()) - set(reqs.keys())):
    print(f'{name}=={pyproject_deps[name]}')

print('\n=== Only in requirements.txt ===')
for name in sorted(set(reqs.keys()) - set(pyproject_deps.keys())):
    print(f'{name}=={reqs[name]}')