import json
import os
from src.api.main import app

def export_openapi():
    openapi_schema = app.openapi()
    os.makedirs("docs", exist_ok=True)
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Exported OpenAPI schema to docs/openapi.json")

if __name__ == "__main__":
    export_openapi()
