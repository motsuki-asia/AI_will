#!/usr/bin/env python3
"""
OpenAPI spec validator script

Usage:
    python scripts/validate_openapi.py [--verbose]

Validates:
    1. OpenAPI 3.1 spec structure
    2. All $ref references resolve correctly
    3. Required fields are present
"""
import sys
import re
from pathlib import Path

def find_all_refs(obj, refs=None):
    """Recursively find all $ref values in the spec"""
    if refs is None:
        refs = set()
    
    if isinstance(obj, dict):
        if "$ref" in obj:
            refs.add(obj["$ref"])
        for value in obj.values():
            find_all_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            find_all_refs(item, refs)
    
    return refs

def resolve_ref(spec, ref):
    """Check if a $ref can be resolved"""
    if not ref.startswith("#/"):
        return True  # External refs not checked
    
    path_parts = ref[2:].split("/")
    current = spec
    
    try:
        for part in path_parts:
            # Handle URL-encoded characters
            part = part.replace("~1", "/").replace("~0", "~")
            current = current[part]
        return True
    except (KeyError, TypeError):
        return False

def validate_refs(spec):
    """Validate all $ref references"""
    refs = find_all_refs(spec)
    errors = []
    
    for ref in refs:
        if not resolve_ref(spec, ref):
            errors.append(f"Broken $ref: {ref}")
    
    return errors

def check_operationIds(spec):
    """Check for duplicate operationIds"""
    operation_ids = []
    errors = []
    
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            op_id = operation.get("operationId")
            if op_id:
                if op_id in operation_ids:
                    errors.append(f"Duplicate operationId: {op_id}")
                operation_ids.append(op_id)
    
    return errors

def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    spec_path = Path(__file__).parent.parent / "docs" / "api" / "openapi.yaml"
    
    print(f"Validating: {spec_path}")
    print("-" * 50)
    
    errors = []
    
    # Step 1: OpenAPI spec validation
    try:
        from openapi_spec_validator import validate
        from openapi_spec_validator.readers import read_from_filename
        
        spec_dict, base_uri = read_from_filename(str(spec_path))
        validate(spec_dict)
        print("[OK] OpenAPI 3.1 structure is valid")
    except Exception as e:
        errors.append(f"OpenAPI structure: {e}")
        print(f"[ERROR] OpenAPI structure: {e}")
        return 1
    
    # Step 2: $ref validation
    ref_errors = validate_refs(spec_dict)
    if ref_errors:
        errors.extend(ref_errors)
        for err in ref_errors:
            print(f"[ERROR] {err}")
    else:
        print("[OK] All $ref references are valid")
    
    # Step 3: operationId validation
    op_errors = check_operationIds(spec_dict)
    if op_errors:
        errors.extend(op_errors)
        for err in op_errors:
            print(f"[ERROR] {err}")
    else:
        print("[OK] All operationIds are unique")
    
    # Step 4: Count stats
    paths = spec_dict.get("paths", {})
    schemas = spec_dict.get("components", {}).get("schemas", {})
    endpoint_count = sum(
        1 for path in paths.values() if isinstance(path, dict)
        for method in path.keys() if method in ["get", "post", "put", "patch", "delete"]
    )
    
    print("-" * 50)
    print(f"Stats: {endpoint_count} endpoints, {len(schemas)} schemas")
    
    if errors:
        print(f"\n[FAILED] {len(errors)} error(s) found")
        return 1
    else:
        print("\n[SUCCESS] OpenAPI spec is valid!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
