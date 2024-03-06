{ stdenv, fetchFromBitbucket, isSnapshot }:

let
  # Why this package? No reason, I just found a small package that uses tags
  # for release by grepping through nixpkgs for fetchFromBitbucket.
  owner = "jongsoftdev";
  repo = "youless-python-bridge";
  # As of 2023-11-22, latest version is 1.0.1, so we will be testing that it
  # finds a version greater than 1.0. The rev from 2022-10-01 is an untagged
  # commit.
  version =
    if (isSnapshot)
    then "0.16-unstable-2022-10-01"
    else "1.0";
  rev =
    if (isSnapshot)
    then "c04342ef36dd5ba8f7d9b9fce2fb4926ef401fd5"
    else "1.0";
in
stdenv.mkDerivation rec {
  pname = repo;
  inherit version;
  src = fetchFromBitbucket {
    inherit owner repo version rev;
    # dont care about hash
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
