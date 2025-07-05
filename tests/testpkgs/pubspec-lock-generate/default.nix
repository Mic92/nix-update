{
  lib,
  fetchFromGitHub,
  flutter327,
}:

flutter327.buildFlutterApplication rec {
  pname = "sly";
  version = "0.4.0";

  src = fetchFromGitHub {
    owner = "kra-mo";
    repo = "Sly";
    tag = "v${version}";
    hash = "sha256-P7LhhXQQDRsDQ8bZgfvWazLRMYVGhFhMTD41fgs718g=";
  };

  pubspecLock = lib.importJSON ./pubspec.lock.json;
}
