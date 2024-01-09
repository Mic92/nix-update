{ buildNpmPackage
, fetchFromGitHub
}:
buildNpmPackage rec {
  pname = "immich-cli";
  # version of immich and immich cli differes
  version = (builtins.fromJSON (builtins.readFile "${src}/cli/package.json")).version;

  immich_version = "1.91.0";
  src = fetchFromGitHub {
    owner = "immich-app";
    repo = "immich";
    rev = "v${immich_version}";
    hash = "sha256-tFaa2rN4iGMlrPjHqSbMOE2xbyJh7Ro+Fm8j0+wa1MM=";
  };

  npmDepsHash = "sha256-NvU+v8MrwPK6q8RdVEHhzi5g6qRRmdTtInf7o2E5y6Y=";

  postPatch = ''
    cd cli
  '';
}
