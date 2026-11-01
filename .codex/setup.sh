#!/usr/bin/env bash
# Install the Linux cloud workspace. Run from any directory.
set -euo pipefail

workspace_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$workspace_dir"

if [[ "$(uname -s)" != Linux ]] || ! command -v apt-get >/dev/null; then
    echo 'This installer targets Debian/Ubuntu cloud environments.' >&2
    exit 1
fi

# Managed cloud images often include build tools but do not provide sudo.
# Only request system packages when something required is actually missing.
missing=()
for tool in cc c++ make cmake curl git pkg-config python3; do
    if ! command -v "$tool" >/dev/null; then
        missing+=("$tool")
    fi
done
if command -v pkg-config >/dev/null && ! pkg-config --exists openssl; then
    missing+=(libssl-dev)
fi
if command -v python3 >/dev/null && ! python3 -c 'import venv, ensurepip' 2>/dev/null; then
    missing+=(python3-venv)
fi
if [[ ${#missing[@]} -gt 0 ]]; then
    admin=()
    if [[ "$(id -u)" != 0 ]]; then
        if ! command -v sudo >/dev/null || ! sudo -n true 2>/dev/null; then
            echo "Missing system prerequisites: ${missing[*]}. Install them in the base image or run setup with package-install privileges." >&2
            exit 1
        fi
        admin=(sudo -n)
    fi
    "${admin[@]}" apt-get update
    "${admin[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential ca-certificates cmake curl git libssl-dev pkg-config \
        python3 python3-venv
fi

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
