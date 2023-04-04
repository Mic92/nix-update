{ rustPlatform, fetchFromGitHub }:

rustPlatform.buildRustPackage rec {
  pname = "ruff";
  version = "0.0.254";

  src = fetchFromGitHub {
    owner = "charliermarsh";
    repo = pname;
    rev = "v${version}";
    hash = "sha256-61Yw4YWolMZbi9nqDdkSH4UxIpPxUO4Aq44ABXZxMbU=";
  };

  cargoLock = {
    lockFile = src + "/Cargo.lock";
    outputHashes = {
      "libcst-0.1.0" = "sha256-jG9jYJP4reACkFLrQBWOYH6nbKniNyFVItD0cTZ+nW0=";
      "libcst_derive-0.1.0" = "sha256-jG9jYJP4reACkFLrQBWOYH6nbKniNyFVItD0cTZ+nW0=";
      "rustpython-ast-0.2.0" = "sha256-Q2PVP+noPvdjoe8OMzEZOHprSwvpu/rmMkllghnf/yI=";
      "rustpython-common-0.2.0" = "sha256-Q2PVP+noPvdjoe8OMzEZOHprSwvpu/rmMkllghnf/yI=";
      "rustpython-compiler-core-0.2.0" = "sha256-Q2PVP+noPvdjoe8OMzEZOHprSwvpu/rmMkllghnf/yI=";
      "rustpython-parser-0.2.0" = "sha256-Q2PVP+noPvdjoe8OMzEZOHprSwvpu/rmMkllghnf/yI=";
      "unicode_names2-0.6.0" = "sha256-eWg9+ISm/vztB0KIdjhq5il2ZnwGJQCleCYfznCI3Wg=";
    };
  };
}
