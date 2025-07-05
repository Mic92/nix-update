{
  lib,
  flutter324,
  fetchFromGitHub,
}:

flutter324.buildFlutterApplication rec {
  pname = "localsend";
  version = "1.16.1";

  src = fetchFromGitHub {
    owner = "localsend";
    repo = "localsend";
    tag = "v${version}";
    hash = "sha256-9nW1cynvRgX565ZupR+ogfDH9Qem+LQH4XZupVsrEWo=";
  };

  sourceRoot = "${src.name}/app";

  pubspecLock = lib.importJSON ./pubspec.lock.json;

  gitHashes = {
    pasteboard = "sha256-lJA5OWoAHfxORqWMglKzhsL1IFr9YcdAQP/NVOLYB4o=";
    permission_handler_windows = "sha256-+TP3neqlQRZnW6BxHaXr2EbmdITIx1Yo7AEn5iwAhwM=";
  };
}
