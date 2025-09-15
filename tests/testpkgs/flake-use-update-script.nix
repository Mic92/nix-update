{
  stdenv,
  fetchFromGitHub,
  nix-update-script,
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "equicord";
  version = "2025-08-23";

  src = fetchFromGitHub {
    owner = "Equicord";
    repo = "Equicord";
    tag = finalAttrs.version;
    hash = "sha256-eaTcPcLlSlabZpMakMjIj3J1OpPqhl5qPt3sVycRJxQ=";
  };

  passthru.updateScript = nix-update-script {
    extraArgs = [
      "--version-regex"
      "^(\\d{4}-\\d{2}-\\d{2})$"
    ];
  };
})
