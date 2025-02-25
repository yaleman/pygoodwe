# Doing a release

1. Commit things
2. Ensure the version's bumped in `pyproject.toml`
3. Do the tag: `git tag -a v0.0.10 -m 'Lint all the things'`
4. Check the tag showed up: `git tag`
5. Check the tag: `git show v0.0.10`
6. Push the tag: `git push origin v0.0.10`
7. [Draft a release on Github](https://github.com/yaleman/pygoodwe/releases/new)
8. Publish to pypi: `uv publish --build`
