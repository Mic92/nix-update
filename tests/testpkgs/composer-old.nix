{
  fetchFromGitHub,
  php,
}:

php.buildComposerProject (finalAttrs: {
  pname = "castor";
  version = "0.10.0";

  src = fetchFromGitHub {
    owner = "jolicode";
    repo = "castor";
    rev = "v${finalAttrs.version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  vendorHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
})
