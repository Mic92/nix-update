{
  stdenvNoCC,
  runCommand,
}:

stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "merged-patch";
  version = "1";

  src = if finalAttrs.version == "1" then ./source-old else ./source-new;

  patches = [
    (runCommand "merged.patch" { } ''
      cp ${./merged.patch} $out
    '')
    (runCommand "pending.patch" { } ''
      cp ${./pending.patch} $out
    '')
  ];

  dontBuild = true;
  installPhase = ''
    mkdir -p $out
  '';
})
