{ stdenv }:

let
  fetchFromInternalGitHub =
    {
      githubBase,
      owner,
      repo,
      hash,
      tag ? null,
      rev ? null,
    }:
    stdenv.mkDerivation (finalAttrs: rec {
      # fetchFromGitHub derivation name is always "source"
      name = "source";

      revWithTag = if tag != null then "refs/tags/${tag}" else rev;
      url = "https://${githubBase}/repos/${owner}/${repo}/tarball/${revWithTag}";
      src = builtins.fetchTree {
        type = "tarball";
        url = url;

        # use hash of final derivation attributes, once it will get overwritten on the outer derivation
        narHash = finalAttrs.outputHash;
      };

      dontUnpack = true;
      buildPhase = ''
        cp -a ${src}/ $out/
      '';

      # fixed output derivation
      outputHashAlgo = "sha256";
      outputHashMode = "recursive";
      outputHash = hash;
    });
in
stdenv.mkDerivation rec {
  pname = "fd";
  version = "8.0.0";

  src = fetchFromInternalGitHub {
    githubBase = "api.github.com";
    owner = "sharkdp";
    repo = pname;
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
