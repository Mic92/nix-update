{ stdenv, fetchFromRadicle }:

stdenv.mkDerivation (finalAttrs: {
  pname = "radicle-node";
  version = "1.10.2";

  src = fetchFromRadicle {
    seed = "seed.radicle.dev";
    repo = "z3gqcJUoA1n9HaHKufZs5FCSGazv5";
    tag = "releases/${finalAttrs.version}";
    hash = "sha256-AANtEDn0zNR85sJ3f8YVVf6LF+3rXteT+mV5+4Ew4tE=";
  };
})
