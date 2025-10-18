import io
from typing import Any

import yaml


def dump_yaml(data: Any) -> str:
    buffer = io.StringIO()
    yaml.safe_dump(data, buffer, default_flow_style=False, sort_keys=False)
    return buffer.getvalue()
