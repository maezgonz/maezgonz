# Branch protection baseline (main)

Recommended repository settings for `main`:

- Require a pull request before merging
- Require at least 1 approving review
- Require status checks to pass before merging
  - `Validate dashboard inputs / validate`
  - `Regenerate profile dashboard / regenerate`
- Restrict pushes to matching branches (no direct pushes to `main`)
- Require conversation resolution before merging

These rules are configured in GitHub repository settings (Rules/Branch protection).
