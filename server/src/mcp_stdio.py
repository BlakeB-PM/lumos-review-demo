"""Minimal shared MCP stdio transport for the two demo services."""

import json
import sys


def string(max_length=200):
    return {"type": "string", "minLength": 1, "maxLength": max_length}


def integer(minimum=0, maximum=1000):
    return {"type": "integer", "minimum": minimum, "maximum": maximum}


def array(items, max_items=20):
    return {"type": "array", "items": items, "minItems": 1, "maxItems": max_items}


def obj(required=None, **properties):
    return {"type": "object", "properties": properties, "required": list(required or ()),
            "additionalProperties": False}


def validate(value, schema, path="arguments"):
    kind = schema.get("type")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} is outside the allowed values.")
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object.")
        fields = schema["properties"]
        if set(value) - fields.keys() or set(schema["required"]) - value.keys():
            raise ValueError(f"{path} has missing or unsupported fields.")
        for key, entry in value.items():
            validate(entry, fields[key], f"{path}.{key}")
    if kind == "array":
        if not isinstance(value, list) or not schema["minItems"] <= len(value) <= schema["maxItems"]:
            raise ValueError(f"{path} has an invalid list length.")
        for entry in value:
            validate(entry, schema["items"], f"{path}[]")
    if kind == "string" and (not isinstance(value, str) or not value.strip()
                             or not schema["minLength"] <= len(value) <= schema["maxLength"]):
        raise ValueError(f"{path} must be a nonempty string of the allowed length.")
    if kind == "integer" and (type(value) is not int or not schema["minimum"] <= value <= schema["maximum"]):
        raise ValueError(f"{path} must be an integer in the allowed range.")
    if kind == "boolean" and type(value) is not bool:
        raise ValueError(f"{path} must be a boolean.")


def send(response):
    print(json.dumps({"jsonrpc": "2.0", **response}, ensure_ascii=True), flush=True)


def serve_stdio(server_name, instructions, tools, call, *, writes=(), destructive=(), non_idempotent=(),
                resources=None, tool_resources=None, structured=False):
    resources = resources or {}
    tool_resources = tool_resources or {}
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line)
        except (ValueError, UnicodeError):
            send({"id": None, "error": {"code": -32700, "message": "Invalid JSON."}})
            continue
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
            send({"id": None, "error": {"code": -32600, "message": "Invalid request."}})
            continue
        if "id" not in request:
            continue
        response = {"id": request["id"]}
        params = request.get("params", {})
        if not isinstance(params, dict):
            send({**response, "error": {"code": -32602, "message": "Invalid parameters."}})
            continue
        method = request["method"]
        if method == "initialize":
            requested = params.get("protocolVersion")
            supported = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
            result = {"protocolVersion": requested if requested in supported else supported[0],
                      "capabilities": {"tools": {}, **({"resources": {}} if resources else {})},
                      "serverInfo": {"name": server_name, "version": "1.0.0"},
                      "instructions": instructions}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [
                {"name": name, "description": description, "inputSchema": schema,
                 **({"_meta": {"ui": {"resourceUri": tool_resources[name]}}} if name in tool_resources else {}),
                 "annotations": {"readOnlyHint": name not in writes,
                                 "destructiveHint": name in destructive,
                                 "idempotentHint": name not in non_idempotent, "openWorldHint": False}}
                for name, (description, schema) in tools.items()
            ]}
        elif method == "resources/list" and resources:
            result = {"resources": [entry[0] for entry in resources.values()]}
        elif method == "resources/read" and resources:
            uri = params.get("uri")
            if not isinstance(uri, str) or uri not in resources:
                send({**response, "error": {"code": -32002, "message": "Resource not found."}})
                continue
            metadata, read = resources[uri]
            result = {"contents": [{"uri": uri, "mimeType": metadata["mimeType"], "text": read()}]}
        elif method == "tools/call":
            try:
                name = params.get("name")
                if not isinstance(name, str) or name not in tools:
                    raise ValueError("Tool unavailable in this mode.")
                arguments = params.get("arguments", {})
                validate(arguments, tools[name][1])
                data = call(name, arguments)
                result = {"content": [{"type": "text", "text": json.dumps(data)}],
                          **({"structuredContent": data} if structured else {})}
            except ValueError as error:
                result = {"isError": True, "content": [{"type": "text", "text": str(error)}]}
            except Exception:
                result = {"isError": True, "content": [
                    {"type": "text", "text": "Local server error. Retry the same submission and key if needed."}
                ]}
        else:
            send({**response, "error": {"code": -32601, "message": "Method not found."}})
            continue
        send({**response, "result": result})
