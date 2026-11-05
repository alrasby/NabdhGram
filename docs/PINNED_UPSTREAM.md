# Pinned Telegram Android baseline

Verified by GitHub Actions source checkout validation #1 on 2026-11-05.

- Repository: https://github.com/DrKLO/Telegram
- Full commit: `3de37c8cfb039452be7398909461da6288babf15`
- Recursive submodules recorded in the validation artifact: **19**
- Original validation artifact: `telegram-upstream-revision.zip` (retained in the GitHub Actions run; not committed here)

## Reproduce

```bash
git clone https://github.com/DrKLO/Telegram.git Telegram-upstream
git -C Telegram-upstream checkout --detach 3de37c8cfb039452be7398909461da6288babf15
git -C Telegram-upstream submodule update --init --recursive --jobs=4
bash scripts/verify-upstream.sh Telegram-upstream
```

The commit is fixed; `master` is not a reproducible baseline. Submodule SHAs are stored in the parent Git tree and were captured in the original validation artifact.

## Limitations

This proves a successful checkout and source-file validation, **not** a successful Android compilation. The complete Telegram source is not yet part of the NabdhGram Git tree, and the project's approved artwork, application identity, credentials and signing still require integration.
