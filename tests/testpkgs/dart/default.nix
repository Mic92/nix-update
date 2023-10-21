{ fetchFromGitHub
, buildDartApplication
}:

buildDartApplication rec {
  pname = "dart-sass";
  version = "1.50.0";

  src = fetchFromGitHub {
    owner = "sass";
    repo = pname;
    rev = version;
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  pubspecLockFile = ./pubspec.lock;
  vendorHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
}
