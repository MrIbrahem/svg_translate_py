
# Usage

```python
from pathlib import Path
from svg_translate import start_on_template_title

title = "Template:OWID/Parkinsons prevalence"

output_dir = Path(__file__).parent / "svg_data"

result = start_on_template_title(title, output_dir=output_dir, titles_limit=None, overwrite=False)
files = result.get("files", {})

```
