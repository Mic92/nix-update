{
  stdenv,
  fetchFromBitbucket,
  isSnapshot,
}:

let
  # Why this package? No reason, I just found a small package that uses tags
  # for release by grepping through nixpkgs for fetchFromBitbucket.
  owner = "nielsenb";
  repo = "aniso8601";
  # As of 2024-04-23, latest version is 9.0.1, so we will be testing that it
  # finds a version greater than 9.0.0. The rev from 2021-03-02 is an untagged
  # commit.
  version = if (isSnapshot) then "0.16-unstable-2022-10-01" else "9.0.0";
  rev = if (isSnapshot) then "55b1b849a57341a303ae47eb67c7ecf8c283b7f8" else "v9.0.0";
in
stdenv.mkDerivation rec {
  pname = repo;
  inherit version;
  src = fetchFromBitbucket {
    inherit
      owner
      repo
      version
      rev
      ;
    # dont care about hash
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
