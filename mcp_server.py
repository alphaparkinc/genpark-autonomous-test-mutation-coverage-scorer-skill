"""
MCP Server for genpark-autonomous-test-mutation-coverage-scorer-skill
Standard JSON-RPC 2.0 protocol over stdio.
"""

import sys
import json
from client import TestMutationCoverageScorerClient

client = TestMutationCoverageScorerClient()

def handle_request(req):
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "evaluate_mutation_score",
                        "description": "Execute mutation testing on Python source code and test suite.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "original_code": {"type": "string", "description": "Original Python code under test"},
                                "test_cases": {"type": "array", "description": "Array of test case objects (fn_name, args, expected)"}
                            },
                            "required": ["original_code", "test_cases"]
                        }
                    }
                ]
            }
        }
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name == "evaluate_mutation_score":
            res = client.evaluate_mutation_score(args.get("original_code", ""), args.get("test_cases", []))
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
            }
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
