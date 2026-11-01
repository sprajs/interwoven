#!/usr/bin/env bash
# Exercise Python numerics/plotting and a compiled, parallel Rust simulation.
set -euo pipefail

workspace_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$workspace_dir/.venv/bin:$HOME/.local/share/big-idea-tools/bin:$HOME/.cargo/bin:$PATH"
check_dir="$(mktemp -d)"
trap 'rm -rf "$check_dir"' EXIT

"$workspace_dir/.venv/bin/python" - "$check_dir" <<'PY'
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp
import sympy as sp

solution = solve_ivp(lambda t, y: -y, (0, 1), [1.0], rtol=1e-9, atol=1e-12)
assert abs(solution.y[0, -1] - math.exp(-1)) < 1e-8
assert np.allclose(np.linalg.solve([[2., 0.], [0., 4.]], [2., 8.]), [1., 2.])
assert pd.Series([1, 2, 3]).sum() == 6
x = sp.Symbol("x")
assert sp.diff(x**2, x) == 2*x
plt.plot(solution.t, solution.y[0])
output = pathlib.Path(sys.argv[1]) / "decay.png"
plt.savefig(output)
assert output.stat().st_size > 0
print(f"Python {sys.version.split()[0]}, NumPy {np.__version__}, SciPy {scipy.__version__}: numerics and plotting passed")
PY

mkdir -p "$check_dir/src"
cat > "$check_dir/Cargo.toml" <<'TOML'
[package]
name = "big-idea-environment-check"
version = "0.1.0"
edition = "2024"

[dependencies]
rayon = "1"
TOML
cat > "$check_dir/src/main.rs" <<'RS'
use rayon::prelude::*;

fn main() {
    let steps = 100_000_u64;
    let integral: f64 = (0..steps)
        .into_par_iter()
        .map(|i| {
            let x = (i as f64 + 0.5) / steps as f64;
            4.0 / (1.0 + x * x) / steps as f64
        })
        .sum();
    assert!((integral - std::f64::consts::PI).abs() < 1e-9);
    println!("Rust release build and parallel numerical integration passed: pi = {integral:.12}");
}
RS
rustc --version
cargo --version
cargo run --release --manifest-path "$check_dir/Cargo.toml"
python -m pytest --version
ruff --version
echo 'Environment checks passed.'
