from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .nix_ast import remove_list_elements
from .utils import info, nix_command, run

if TYPE_CHECKING:
    from .eval import Package
    from .options import Options


def _merged_patch_indices(opts: Options) -> set[int]:
    """Unpack the new source and find patches that apply cleanly in reverse."""
    package_expr = opts.get_package()
    expression = f"""let
      pkg = {package_expr};
      originalPatches = pkg.patches or [ ];
      patches = map (candidate:
        if builtins.isPath candidate then
          builtins.path {{ path = candidate; name = builtins.baseNameOf candidate; }}
        else candidate
      ) originalPatches;
      lib = (import <nixpkgs> {{ }}).lib;
      flagsValue = pkg.patchFlags or [ "-p1" ];
      flags = if builtins.isList flagsValue then flagsValue else [ flagsValue ];
    in pkg.overrideAttrs (old: {{
      name = "${{pkg.name}}-merged-patches";
      patches = [ ];
      patchInputs = patches;
      phases = [ "unpackPhase" "installPhase" ];
      installPhase = ''
        mkdir -p "$out"
        i=0
        for candidate in ${{lib.escapeShellArgs (map toString patches)}}; do
          if patch --force --reverse --silent --dry-run ${{lib.escapeShellArgs flags}} < "$candidate"; then
            touch "$out/$i"
          fi
          i=$((i + 1))
        done
      '';
    }})"""
    result = run(
        [
            *nix_command("build", "--no-link", "--print-out-paths"),
            *opts.extra_flags,
            "--impure",
            "--expr",
            expression,
        ],
    )
    output = Path(result.stdout.strip())
    return {int(marker.name) for marker in output.iterdir() if marker.name.isdigit()}


def drop_merged_patches(opts: Options, package: Package) -> None:
    if not package.patches or package.patches_position is None:
        return
    merged = _merged_patch_indices(opts)
    dropped = remove_list_elements(
        package.filename,
        "patches",
        package.patches_position.line,
        merged,
        len(package.patches),
    )
    for index in sorted(dropped):
        patch = Path(str(package.patches[index]["path"])).name
        info(f"Drop patch already applied upstream: {patch}")
