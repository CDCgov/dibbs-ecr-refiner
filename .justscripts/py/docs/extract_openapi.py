import json
import sys
from pathlib import Path
import types
import importlib.machinery
from unittest.mock import MagicMock

class LazyMockModule(types.ModuleType):
    def __getattr__(self, name):
        # Return a MagicMock to prevent infinite recursion and handle any access pattern
        val = MagicMock()
        setattr(self, name, val)
        return val

    def __getitem__(self, key):
        return self.__getattr__(str(key))

    def __iter__(self):
        return iter([])

    def __call__(self, *args, **kwargs):
        return self

class MockFinder:
    def __init__(self, prefixes):
        self.prefixes = prefixes

    def find_spec(self, fullname, path, target=None):
        if any(fullname.startswith(p) for p in self.prefixes):
            return importlib.machinery.ModuleSpec(fullname, self)
        return None

    def create_module(self, spec):
        return LazyMockModule(spec.name)

    def exec_module(self, module):
        pass

    def load_module(self, fullname):
        return LazyMockModule(fullname)

def extract_openapi():
    print("Extracting OpenAPI schema...")
    import os
    # FIX: Set environment variables BEFORE importing any app modules.
    # This prevents crashes in app.core.config which evaluates ENVIRONMENT at import time.
    os.environ["ENV"] = "local"
    os.environ["VERSION"] = "0.0.0"
    os.environ["DB_URL"] = "mock"
    os.environ["DB_PASSWORD"] = "mock"
    os.environ["SESSION_SECRET_KEY"] = "mock"
    os.environ["AUTH_PROVIDER"] = "mock"
    os.environ["AUTH_CLIENT_ID"] = "mock"
    os.environ["AUTH_CLIENT_SECRET"] = "mock"
    os.environ["AUTH_ISSUER"] = "mock"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["S3_BUCKET_CONFIG"] = "mock"

    # Use absolute path to project root
    project_root = Path(__file__).parent.parent.parent.parent.absolute()
    sys.path.append(str(project_root / "refiner"))

    try:
        # FIX: Use a custom meta_path finder to mock all binary-dependent libraries.
        # This bypasses _cffi_backend errors and handles deep nested imports
        # (e.g. cryptography.hazmat.primitives.asymmetric) without manual mapping.
        sys.meta_path.insert(0, MockFinder(["psycopg", "cryptography"]))

        from app.main import create_fastapi_app
        from app.core.app.openapi import create_custom_openapi

        mock_lifespan = MagicMock()
        app = create_fastapi_app(mock_lifespan)

        schema = create_custom_openapi(app)

        output_dir = project_root / "docs/_data"
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_dir / "openapi.json", "w") as f:
            json.dump(schema, f, indent=2)

        # Count endpoints
        endpoint_count = sum(len(paths) for paths in schema.get("paths", {}).values())
        print(f"Wrote OpenAPI schema with {endpoint_count} endpoints to {output_dir / 'openapi.json'}")

    except Exception as e:
        print(f"Error extracting OpenAPI schema: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    extract_openapi()
