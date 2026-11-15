"""PreToolUse guard for the report-auditor subagent: keeps it read-only with allowlists.

Write and Edit may only touch the agent's own memory folder.
Bash may run only read-only commands (READ_ONLY) and the project Python (.venv/bin/python -I)
with code given by `-c` or a quoted heredoc. That code is parsed: only SAFE_MODULES may be
imported, open() must be read-only, and dunder access, exec/eval and similar are refused.
Anything not recognised is blocked. Exit 2 blocks the call and tells the agent why.
"""

import ast
import json
import os
import re
import shlex
import sys

PROJECT = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
MEMORY = os.path.join(PROJECT, ".claude", "agent-memory", "report-auditor")
PYTHON = {".venv/bin/python", os.path.join(PROJECT, ".venv/bin/python")}
READ_ONLY = {"cat", "head", "tail", "ls", "wc", "grep", "cut", "tr", "echo", "printf", "cd", "pwd", "diff", "jq", "true"}
SEPARATORS = {"&&", "||", ";", "|"}
SAFE_REDIRECTS = {("2>", "/dev/null"), (">", "/dev/null"), ("2>", "&1")}
SAFE_MODULES = {"csv", "json", "re", "statistics", "collections", "datetime", "math", "itertools",
                "decimal", "fractions", "textwrap", "random"}
CALL_ONLY = {"open", "type", "object"}  # allowed only as the direct target of a call, never passed around
def _module_attrs() -> set:
    """Attribute names on the allowed modules that lead to other modules (collections.sys, re.functools)."""
    import importlib, types
    names = {"system", "modules", "popen", "spawn", "builtins", "loader", "spec"}
    for m in SAFE_MODULES:
        mod = importlib.import_module(m)
        names.update(a for a in dir(mod) if isinstance(getattr(mod, a, None), types.ModuleType))
    return names


MODULE_ATTRS = _module_attrs()
BANNED_NAMES = {"exec", "eval", "compile", "__import__", "getattr", "setattr", "delattr", "globals",
                "locals", "vars", "breakpoint", "input", "memoryview", "help", "exit", "quit"}
# Only <<'WORD' (no <<-): the quoted word must end at a space, an operator or the line end, and the
# closing line must be exactly WORD, so the guard reads the heredoc the same way bash does.
HEREDOC = re.compile(r"<<[ \t]*'(\w+)'(?=[ \t;&|<>\n]|$)([^\n]*)\n(.*?)\n\1(?=\n|$)", re.S)
INTROSPECTION = re.compile(r"^(f|tb|co|gi|cr|ag)_|^(mro|func|im_\w+)$")


def block(msg: str) -> None:
    print(f"report-auditor is read-only: {msg}", file=sys.stderr)
    sys.exit(2)


def check_python(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        block(f"Python could not be parsed ({e.msg}).")
    called = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    aliases = {(a.asname or a.name).split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    attr_bases = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    top_imports = {id(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if id(node) not in top_imports:
                block("imports are allowed only at the top level of the code.")
            if isinstance(node, ast.Import) and any("." in a.name for a in node.names):
                block("dotted imports are not allowed; import the module itself.")
            if isinstance(node, ast.ImportFrom) and (node.level or node.module not in SAFE_MODULES):
                block(f"from-imports are allowed only from {', '.join(sorted(SAFE_MODULES))}.")
            for a in node.names:
                for n in (a.name, a.asname or ""):
                    if n.startswith("_") or n in BANNED_NAMES or n in CALL_ONLY:
                        block(f"importing or naming {n} is not allowed.")
        if isinstance(node, ast.Attribute) and node.attr in aliases | SAFE_MODULES:
            block(f"attribute {node.attr} names a module and is not allowed.")
        if isinstance(node, ast.Name) and node.id in aliases and id(node) not in attr_bases \
                and not isinstance(node.ctx, ast.Store):
            block(f"module {node.id} may only be used as {node.id}.<name>, never passed around.")
        if isinstance(node, ast.Attribute) and node.attr in MODULE_ATTRS:
            block(f"attribute {node.attr} leads to another module and is not allowed.")
        if isinstance(node, ast.ImportFrom) and any(a.name in MODULE_ATTRS or a.name == "*" for a in node.names):
            block("that import pulls in another module and is not allowed.")
        if isinstance(node, ast.Call) and (any(isinstance(a, ast.Starred) for a in node.args)
                                           or any(k.arg is None for k in node.keywords)):
            block("* and ** unpacking in calls is not allowed.")
        if isinstance(node, ast.Name) and node.id in CALL_ONLY and id(node) not in called:
            block(f"{node.id} may only be called directly.")
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and \
                ("__" in (node.value if isinstance(node.value, str) else node.value.decode("latin-1"))):
            block("strings containing '__' are not allowed.")
        if isinstance(node, ast.Attribute) and node.attr in ("format", "format_map"):
            block("str.format is not allowed; use an f-string.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print" and \
                any(k.arg == "file" for k in node.keywords):
            block("print(file=...) is not allowed.")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            bad = [n for n in names if n.split(".")[0] not in SAFE_MODULES]
            if bad or (isinstance(node, ast.ImportFrom) and node.level):
                block(f"import of {bad or 'a relative module'} is not allowed. Allowed: {', '.join(sorted(SAFE_MODULES))}.")
        elif isinstance(node, ast.Name) and (node.id in BANNED_NAMES or node.id.startswith("_")):
            block(f"{node.id} is not allowed.")
        elif isinstance(node, ast.Attribute) and (node.attr.startswith("_") or node.attr in BANNED_NAMES
                                                  or INTROSPECTION.search(node.attr)):
            block(f"attribute {node.attr} is not allowed.")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
            if len(node.args) > 2:
                block("open() takes at most a path and a mode.")
            if mode is not None and not (isinstance(mode, ast.Constant) and mode.value in ("r", "rb", "rt")):
                block("open() is allowed only for reading ('r').")
            if any(k.arg not in ("mode", "encoding", "newline", "errors") for k in node.keywords):
                block("open() is allowed only with mode, encoding, newline or errors.")


def check_bash(cmd: str) -> None:
    heredocs = [m.group(3) for m in HEREDOC.finditer(cmd)]
    # Keep the rest of each heredoc's opening line: it is shell and must be checked.
    shell = HEREDOC.sub(lambda m: "<<HEREDOC" + m.group(2), cmd)
    if "<<-" in cmd or cmd.count("<<") != len(heredocs):
        block("heredocs must use a quoted delimiter, e.g. <<'PY'.")
    if re.search(r"\$\(|`|<\(|>\(|\$\{|\\\n", shell):
        block("no command substitution, process substitution or line continuations.")
    if re.search(r"[\n\r]", shell):
        block("put the shell part on one line; line breaks are allowed only inside a quoted heredoc.")
    lex = shlex.shlex(shell.replace("<<HEREDOC", " HEREDOC_MARK "), posix=True, punctuation_chars=";&|<>")
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        tokens = list(lex)
    except ValueError as e:
        block(f"command could not be parsed ({e}).")

    commands, cur, i = [], [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in SEPARATORS:
            commands.append(cur); cur = []
        elif re.fullmatch(r"[;&|<>]+", t) and t not in (">", ">&", "&>"):
            block(f"shell operator {t!r} is not allowed. Use only &&, ||, ;, | and >/dev/null, 2>/dev/null, 2>&1.")
        elif t in (">", ">&", "&>") or (t.isdigit() and i + 1 < len(tokens) and tokens[i + 1] in (">", ">&")):
            op = t
            if t.isdigit():
                i += 1; op = t + tokens[i]
            target = tokens[i + 1] if i + 1 < len(tokens) else ""
            if (op, target) in SAFE_REDIRECTS or (op in ("2>&", ">&") and target == "1"):
                i += 2; continue
            block(f"redirection {op} {target} is not allowed. Print results to stdout.")
        else:
            cur.append(t)
        i += 1
    commands.append(cur)

    py_code = list(heredocs)
    for argv in commands:
        if not argv:
            continue
        if re.fullmatch(r"[A-Za-z_]\w*=.*", argv[0]) or "#" in argv[0]:
            block("environment variable assignments are not allowed.")
        prog = argv[0]
        if prog in READ_ONLY:
            if prog == "jq" and any(a.startswith("--") and a not in ("--raw-output", "--compact-output") for a in argv):
                block("jq options other than --raw-output and --compact-output are not allowed.")
            continue
        if prog in PYTHON:
            args = [a for a in argv[1:] if a != "HEREDOC_MARK"]
            if not args or args[0] != "-I":
                block("run Python as `.venv/bin/python -I -c '...'` or `.venv/bin/python -I - <<'PY'`.")
            if args[1:2] == ["-c"] and len(args) == 3:
                py_code.append(args[2])
            elif args[1:] == ["-"] and heredocs:
                pass
            else:
                block("Python may run only inline code (-c or a heredoc), never a script file.")
            continue
        block(f"`{prog}` is not on the read-only list ({', '.join(sorted(READ_ONLY))}, .venv/bin/python -I).")
    for code in py_code:
        check_python(code)


def main() -> None:
    event = json.load(sys.stdin)
    tool, args = event.get("tool_name", ""), event.get("tool_input", {}) or {}
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = os.path.realpath(args.get("file_path") or args.get("notebook_path") or "")
        if not path.startswith(os.path.realpath(MEMORY) + os.sep):
            block(f"{tool} is allowed only inside {MEMORY}. Report the fix instead of making it.")
    elif tool == "Bash":
        check_bash(args.get("command", ""))


if __name__ == "__main__":
    main()
