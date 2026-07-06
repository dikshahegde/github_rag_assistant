SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".md",
    ".java"
    ".html"
}

IGNORE_PATTERNS = {
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml"
}

# Mapping extensions to tree-sitter language identifiers
LANGUAGE_MAPPING = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java"
}
