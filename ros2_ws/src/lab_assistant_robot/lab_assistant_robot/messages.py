import json
from typing import Any, Dict

from std_msgs.msg import String


def to_msg(payload: Dict[str, Any]) -> String:
    msg = String()
    msg.data = json.dumps(payload)
    return msg


def from_msg(msg: String) -> Dict[str, Any]:
    try:
        return json.loads(msg.data)
    except json.JSONDecodeError:
        return {"event": "invalid_json", "raw": msg.data}
