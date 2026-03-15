"""
RLM Hybrid REPL Bootstrap
=========================
Paste the full contents of this file as the `code` argument of a single
`execute_code` call (MCP_DOCKER server) at the start of every Composer session
or after a repo switch.

Do NOT pass `session_id` on this first call — omit it or pass 0. The response
will return the assigned session integer. Store that integer and pass it as
`session_id` on every subsequent `execute_code` call to maintain state.

This file is NOT a standalone script. It is REPL code executed by the agent
via the MCP_DOCKER `execute_code` tool.

Expected output on success:
    ✅ Bootstrap complete
    Helpers ready: load_batch(), reset_repl(), get_status(), mark_as_loaded()
    Status -> files_loaded: 0 | signature: None
"""

from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Persistent state — survives across all execute_code calls sharing session_id
# ---------------------------------------------------------------------------

if "codebase" not in globals():
    codebase: Dict[str, str] = {}

if "repo_signature" not in globals():
    repo_signature: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def load_batch(files_dict: Dict[str, str]) -> None:
    """
    Inject files gathered by Cursor into the persistent codebase store.

    Description:
        Merges the provided path->content mapping into the global `codebase`
        dict. Existing entries are overwritten if the same path is provided
        again. All content must be passed as Python strings — the container
        has no host filesystem access.

    Preconditions:
        - files_dict is a non-empty dict mapping file path strings to their
          string content as fetched by Cursor's native tools.

    Postconditions:
        - All entries in files_dict are present in the global `codebase` dict.

    Parameters:
        files_dict: Mapping of file path strings to file content strings.

    Returns:
        None. Prints a confirmation with the count of files loaded.
    """
    global codebase
    codebase.update(files_dict)
    print("Loaded {} file(s). Total in codebase: {}".format(
        len(files_dict), len(codebase)
    ))


def reset_repl() -> None:
    """
    Clear all persistent state for a clean repo switch.

    Description:
        Resets the global `codebase` dict and `repo_signature` to their
        initial empty states. Call this when switching to a different
        repository to avoid stale data contaminating analysis.

    Preconditions:
        - None.

    Postconditions:
        - `codebase` is an empty dict.
        - `repo_signature` is None.

    Parameters:
        None.

    Returns:
        None. Prints a confirmation message.
    """
    global codebase, repo_signature
    codebase.clear()
    repo_signature = None
    print("REPL reset — codebase cleared, ready for new repository.")


def get_status() -> Dict[str, object]:
    """
    Return the current REPL state for dirty detection.

    Description:
        Reports how many files are loaded and what repo signature is stored.
        The agent compares the returned signature against the current workspace
        identifier to determine whether a reset and reload is needed.

    Preconditions:
        - None.

    Postconditions:
        - No state is modified.

    Parameters:
        None.

    Returns:
        dict with keys:
            - "files_loaded" (int): number of entries in `codebase`
            - "signature" (str or None): stored repo signature or None if unset
    """
    status = {
        "files_loaded": len(codebase),
        "signature": repo_signature,
    }
    print("Status -> files_loaded: {} | signature: {}".format(
        status["files_loaded"], status["signature"]
    ))
    return status


def mark_as_loaded(signature: str) -> None:
    """
    Record the current repo signature after a successful load.

    Description:
        Stores the provided signature string as the active `repo_signature`.
        Call this after `load_batch()` completes to mark the REPL as clean
        for the current repository.
        Format: "{workspace_folder_name}:{git_branch}" e.g. "PJTemplate:main"

    Preconditions:
        - signature is a non-empty string.
        - Files have been loaded via load_batch().

    Postconditions:
        - `repo_signature` is set to the provided signature.

    Parameters:
        signature: String identifying the current repo and branch state.

    Returns:
        None. Prints a confirmation message.
    """
    global repo_signature
    repo_signature = signature
    print("Marked as loaded — signature: {}".format(repo_signature))


# ---------------------------------------------------------------------------
# Bootstrap verification — runs once when this code is executed
# ---------------------------------------------------------------------------

try:
    _test_batch = {"__bootstrap_test__": "ok"}
    load_batch(_test_batch)
    del codebase["__bootstrap_test__"]
    print("")
    print("Bootstrap complete")
    print("Helpers ready: load_batch(), reset_repl(), get_status(), mark_as_loaded()")
    get_status()
except Exception as _e:
    print("Bootstrap error: {}".format(_e))
