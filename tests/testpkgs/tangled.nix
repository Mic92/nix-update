{ stdenv, fetchFromTangled }:

stdenv.mkDerivation (finalAttrs: {
  pname = "tranquil-pds";
  version = "0.8.0";

  src = fetchFromTangled {
    did = "did:plc:jj6ajj6duxnlthwtnob4qyuv";
    tag = "v${finalAttrs.version}";
    hash = "sha256-0/eBbeO31lCI99TNSSQlk9QaWzegpAuYyGCQMupPb9s=";
  };
})
