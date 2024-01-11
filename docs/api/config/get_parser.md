
::: wellies.config.get_parser

```python exec="true" id="parser-help"
import os,sys
sys.path.insert(0, os.environ['MKDOCS_CONFIG_DIR'])
from wellies.config import get_parser
help_message=get_parser().format_help()
help_message = help_message.replace("mkdocs", "deploy")
print(f"```\n{help_message}\n```")
```

