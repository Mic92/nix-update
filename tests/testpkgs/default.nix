{
  pkgs ? import <nixpkgs> { },
}:
{
  bitbucket = pkgs.callPackage ./bitbucket.nix { isSnapshot = false; };
  bitbucket-snapshot = pkgs.callPackage ./bitbucket.nix { isSnapshot = true; };
  cargoLock.expand = pkgs.callPackage ./cargo-lock-expand { };
  cargoLock.generate.simple = pkgs.callPackage ./cargo-lock-generate/simple { };
  cargoLock.generate.with-lockfile-metadata-path =
    pkgs.callPackage ./cargo-lock-generate/with-lockfile-metadata-path
      { };
  cargoLock.generate.with-lockfile-metadata-path-outside-workspace =
    pkgs.callPackage ./cargo-lock-generate/with-lockfile-metadata-path-outside-workspace
      { };
  cargoLock.update = pkgs.callPackage ./cargo-lock-update { };
  composer = pkgs.callPackage ./composer.nix { };
  cargoVendorDeps.nonRustPackage = pkgs.callPackage ./cargo-vendor-deps/non-rust-package.nix { };
  cargoVendorDeps.rustPackage = pkgs.callPackage ./cargo-vendor-deps/rust-package.nix { };
  composer-old = pkgs.callPackage ./composer-old.nix { };
  crate = pkgs.callPackage ./crate.nix { };
  fetchurl-github-release = pkgs.callPackage ./fetchurl-github-release.nix { };
  nuget-deps-generate = pkgs.callPackage ./nuget-deps-generate { };
  gitea = pkgs.callPackage ./gitea.nix { };
  github = pkgs.callPackage ./github.nix { };
  github-no-release = pkgs.callPackage ./github-no-release.nix { };
  github-tag = pkgs.callPackage ./github-tag.nix { };
  gitlab = pkgs.callPackage ./gitlab.nix { };
  pypi = pkgs.python3.pkgs.callPackage ./pypi.nix { };
  sourcehut = pkgs.python3.pkgs.callPackage ./sourcehut.nix { };
  savanna = pkgs.python3.pkgs.callPackage ./savanna.nix { };
  net-news-wire = pkgs.callPackage ./net-news-wire.nix { };
  npm = pkgs.callPackage ./npm.nix { };
  npm-package = pkgs.callPackage ./npm-package.nix { };
  npm-lock-generate = pkgs.callPackage ./npm-lock-generate { };
  pnpm = pkgs.callPackage ./pnpm.nix { };
  maven = pkgs.callPackage ./maven.nix { };
  mix = pkgs.callPackage ./mix.nix { };
  set = pkgs.callPackage ./set.nix { };
  let-bound-version = pkgs.callPackage ./let-bound-version.nix { };
  subpackage = pkgs.callPackage ./subpackage.nix { };
}
