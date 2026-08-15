#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "usage: install.sh TARGET_ROOT [PROFILE] [--apply]" >&2
  exit 2
fi

target_root=$1
profile=${2:-core}
apply=${3:-}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(dirname -- "$script_dir")

if [ "$apply" = "--apply" ]; then
  exec python3 "$script_dir/install_toolkit.py" --source-root "$repo_root" --target-root "$target_root" --profile "$profile" --apply
fi

exec python3 "$script_dir/install_toolkit.py" --source-root "$repo_root" --target-root "$target_root" --profile "$profile"
