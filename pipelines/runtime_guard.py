import importlib.metadata as metadata

REQUIRED_VERSIONS = {
    "pandas": "3.0.1",
    "SQLAlchemy": "2.0.48",
    "psycopg2-binary": "2.9.11",
    "python-dotenv": "1.2.2",
    "yfinance": "1.2.0",
}


def get_runtime_versions():
    return {
        package_name: metadata.version(package_name)
        for package_name in REQUIRED_VERSIONS
    }


def validate_runtime():
    current_versions = get_runtime_versions()
    mismatches = {
        package_name: (current_versions[package_name], required_version)
        for package_name, required_version in REQUIRED_VERSIONS.items()
        if current_versions[package_name] != required_version
    }
    if mismatches:
        details = ", ".join(
            f"{package_name}={current} (expected {expected})"
            for package_name, (current, expected) in mismatches.items()
        )
        raise RuntimeError(f"Runtime dependency mismatch: {details}")


if __name__ == "__main__":
    validate_runtime()
    for package_name, version in get_runtime_versions().items():
        print(f"{package_name}=={version}")
