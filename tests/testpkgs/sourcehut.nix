{
  buildGoModule,
  fetchFromSourcehut,
  lib,
  jq,
  installShellFiles,
  makeWrapper,
  scdoc,
}:

buildGoModule rec {
  pname = "ijq";
  version = "0.3.5";

  src = fetchFromSourcehut {
    owner = "~gpanders";
    repo = pname;
    rev = "v${version}";
    hash = "sha256-0xLmjidPxjSkYmLI4lWieT2rswZsWBY/IUXFOrUFAMo=";
  };

  vendorHash = "sha256-7UuQXnQdlUMC0ZIgHydQ5bZMB5XrE7dhx5+1NI+zFkM=";

  nativeBuildInputs = [
    installShellFiles
    makeWrapper
    scdoc
  ];

  ldflags = [
    "-s"
    "-w"
    "-X main.Version=${version}"
  ];

  postBuild = ''
    scdoc < ijq.1.scd > ijq.1
        installManPage ijq.1
  '';

  postInstall = ''
    wrapProgram "$out/bin/ijq" \
          --prefix PATH : "${lib.makeBinPath [ jq ]}"
  '';
}
