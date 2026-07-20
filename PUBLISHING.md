# Publishing to PyPI

`termdat-mcp` is published to [PyPI](https://pypi.org/project/termdat-mcp/) so it
can be installed with `uvx termdat-mcp` / `pip install termdat-mcp`.

Publishing uses **PyPI Trusted Publishing (OIDC)** — no long-lived API token is
stored anywhere. A published GitHub Release triggers
[`.github/workflows/publish.yml`](.github/workflows/publish.yml), which builds
the distribution and uploads it to PyPI on the repo's behalf.

---

## One-time setup

Do these steps once, before the first release.

### 1. Create a PyPI account

- Register at <https://pypi.org/account/register/> and enable 2FA.
- (Optional but recommended) also register at <https://test.pypi.org/> for a dry run.

### 2. Register the Trusted Publisher on PyPI

Because the project does not exist on PyPI yet, add it as a **pending publisher**:

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Under **Add a new pending publisher**, fill in:
   - **PyPI Project Name:** `termdat-mcp`
   - **Owner:** `malkreide`
   - **Repository name:** `termdat-mcp`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. Save. On the first successful publish, PyPI converts this into the real project
   and a normal trusted publisher.

### 3. Create the `pypi` GitHub environment

The workflow runs in an environment named `pypi` (matching the trusted-publisher
config above):

1. GitHub → repo **Settings** → **Environments** → **New environment** → name it `pypi`.
2. (Optional) add a required reviewer or a tag protection rule so a human approves
   each publish.

No secrets are needed — OIDC handles authentication.

---

## Releasing a new version

Repeat these steps for every release.

### 1. Bump the version

Edit `pyproject.toml` and bump `version` following [SemVer](https://semver.org/):

```toml
version = "0.1.0"   # -> 0.1.1 (patch) / 0.2.0 (minor) / 1.0.0 (major)
```

Also update the version badge in `README.md` / `README.de.md` if it is pinned.

### 2. Update the changelog

In `CHANGELOG.md`, move the `[Unreleased]` notes into a new dated version section:

```markdown
## [0.1.1] — 2026-07-19
```

### 3. Verify locally before tagging

```bash
# tests + lint
PYTHONPATH=src pytest tests/ -m "not live"
ruff check src/ tests/

# build and validate the artifacts
python -m build
twine check dist/*
```

`twine check` must report `PASSED` for both the `.whl` and the `.tar.gz`.

### 4. Commit, tag, and push

```bash
git add pyproject.toml CHANGELOG.md README.md README.de.md
git commit -m "chore: release v0.1.1"
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin main --follow-tags
```

### 5. Create the GitHub Release

Creating a **published** GitHub Release for the tag is what triggers publishing:

- GitHub → **Releases** → **Draft a new release** → choose tag `v0.1.1` →
  **Publish release**, or with the CLI:

```bash
gh release create v0.1.1 --title "v0.1.1" --notes-file CHANGELOG.md --latest
```

### 6. Watch the workflow

- The **Publish to PyPI** workflow runs automatically: it builds, runs
  `twine check`, then uploads via OIDC.
- If you added a required reviewer to the `pypi` environment, approve the run.
- Confirm the new version at <https://pypi.org/project/termdat-mcp/>.

### 7. Smoke-test the published package

```bash
uvx termdat-mcp@latest --help    # or run it and confirm it starts
```

---

## Manual publish (fallback)

Only needed if the workflow is unavailable. Requires a PyPI API token
(<https://pypi.org/manage/account/token/>).

```bash
python -m build
twine check dist/*

# optional: dry run against TestPyPI first
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps termdat-mcp

# real upload
twine upload dist/*
```

With `uv` this is simply:

```bash
uv build
uv publish            # uses UV_PUBLISH_TOKEN or prompts
```

---

## Checklist

- [ ] `version` bumped in `pyproject.toml` (SemVer)
- [ ] `CHANGELOG.md` has a dated section for the release
- [ ] Version badge updated in both READMEs (if pinned)
- [ ] `pytest -m "not live"` and `ruff check` pass
- [ ] `python -m build` + `twine check dist/*` pass
- [ ] Tag `vX.Y.Z` pushed and GitHub Release published
- [ ] New version visible on PyPI and `uvx termdat-mcp` works
