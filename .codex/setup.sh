#!/usr/bin/env bash
# Install the Linux cloud workspace. Run from any directory.
set -euo pipefail

workspace_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$workspace_dir"

if [[ "$(uname -s)" != Linux ]] || ! command -v apt-get >/dev/null; then
    echo 'This installer targets Debian/Ubuntu cloud environments.' >&2
    exit 1
fi

admin=()
if [[ "$(id -u)" != 0 ]]; then
    admin=(sudo)
fi
"${admin[@]}" apt-get update
"${admin[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake curl git libssl-dev pkg-config \
    python3 python3-venv

# Keep tooling separate from both system Python and experiment dependencies.
tools_dir="$HOME/.local/share/big-idea-tools"
python3 -m venv "$tools_dir"
"$tools_dir/bin/python" -m pip install --disable-pip-version-check 'uv==0.12.9'
export PATH="$tools_dir/bin:$HOME/.cargo/bin:$PATH"

uv python install 3.12
uv venv --python 3.12 --allow-existing .venv
uv pip install --python .venv/bin/python -r .codex/requirements.txt

if ! command -v rustup >/dev/null; then
    installer="$(mktemp)"
    trap 'rm -f "$installer"' EXIT
    curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs -o "$installer"
    sh "$installer" -y --no-modify-path --profile minimal --default-toolchain none
fi
rustup toolchain install 1.97.0 --profile minimal --component rustfmt --component clippy
rustup default 1.97.0

bash .codex/check-environment.sh
