# project-snapshot-generator

Generates a complete textual snapshot of a project's source code and directory structure for LLM consumption.

## Upload to PYPI

```bash
pip install --upgrade pkginfo twine packaging

cd src
python -m build
twine upload dist/*
```
