#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, time

if len(sys.argv) != 4:
    raise SystemExit("Usage: deploy_ssm.py REGION INSTANCE_ID IMAGE_URI")
region, instance_id, image_uri = sys.argv[1:4]
allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._/:")
if not image_uri or any(c not in allowed for c in image_uri):
    raise SystemExit("Invalid image URI")

remote = f"""#!/bin/bash
set -euo pipefail
REGION='{region}'
IMAGE_URI='{image_uri}'
REGISTRY="${{IMAGE_URI%%/*}}"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"
docker pull "$IMAGE_URI"
docker rm -f demo-app || true
docker run -d --name demo-app --restart unless-stopped -p 80:80 "$IMAGE_URI"
docker image prune -f
"""
payload = {
    "DocumentName": "AWS-RunShellScript",
    "InstanceIds": [instance_id],
    "Comment": "Deploy " + image_uri,
    "Parameters": {"commands": [remote]},
    "TimeoutSeconds": 600
}
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(payload, f)
    path = f.name
try:
    sent = subprocess.run(["aws", "ssm", "send-command", "--cli-input-json", "file://" + path,
                           "--region", region, "--output", "json"], check=True, capture_output=True, text=True)
finally:
    os.unlink(path)
command_id = json.loads(sent.stdout)["Command"]["CommandId"]
print("SSM command:", command_id)
for _ in range(60):
    result = subprocess.run(["aws", "ssm", "get-command-invocation", "--command-id", command_id,
                             "--instance-id", instance_id, "--region", region, "--output", "json"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        status = data.get("Status")
        print("Deployment status:", status)
        if status == "Success":
            print(data.get("StandardOutputContent", "Deployment successful"))
            sys.exit(0)
        if status in ("Failed", "TimedOut", "Cancelled", "Cancelling"):
            print(data.get("StandardErrorContent", ""), file=sys.stderr)
            print(data.get("StandardOutputContent", ""))
            sys.exit(1)
    time.sleep(5)
raise SystemExit("Timed out waiting for SSM. Check Systems Manager Run Command.")
