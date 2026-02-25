{ stdenv, fetchFromGitHub }:

stdenv.mkDerivation (finalAttrs: {
  pname = "cargo-nextest";
  version = "0.9.0";

  src = fetchFromGitHub {
    owner = "nextest-rs";
    repo = "nextest";
    tag = "cargo-nextest-${finalAttrs.version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
})
