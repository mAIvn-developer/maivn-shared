# Deployment

## Release Order

`maivn-shared` is the foundation package, so publish it before the packages that
depend on it:

1. Tag or pin `maivn-shared` in GitHub so downstream consumers can use an immutable ref.
2. Publish `maivn-shared` to PyPI.
3. Publish `maivn` to PyPI.
4. Publish `maivn-studio` to PyPI.

## Repo Role

`maivn-shared` is a public GitHub repository and a public PyPI package. It is the foundation for
the SDK. Downstream consumers can use it from an immutable GitHub ref before
you publish it to PyPI.

## GitHub Setup

1. Create the repo as public.
2. Set `main` as the protected default branch.
3. Enable GitHub Actions.
4. Create an environment named `pypi`.
5. Configure PyPI Trusted Publishing for this repository and workflow:
   `.github/workflows/publish-pypi.yml`.

No GitHub secrets are required when Trusted Publishing is configured correctly.

## Release Steps

1. Update `version` in `pyproject.toml`.
2. Run local verification:
   ```bash
   uv sync --frozen
   uv run --no-sync ruff check .
   uv run --no-sync pyright
   uv run --no-sync pytest
   ```
3. Merge the release commit to `main`.
4. Create and push an annotated tag such as `v0.1.0`.
5. Confirm the `Publish PyPI` workflow succeeds.
6. Verify the package is installable:
   ```bash
   pip install maivn-shared==0.1.0
   ```

## Rollback

PyPI releases are effectively immutable. If a bad release escapes:

1. Yank the affected version on PyPI.
2. Cut a new patch release.
3. Move downstream repos to the replacement version.
