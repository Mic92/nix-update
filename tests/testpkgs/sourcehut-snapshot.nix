{
  buildGoModule,
  fetchFromSourcehut,
}:
buildGoModule {
  pname = "addr-book-combine";
  version = "0-unstable-2022-12-08";

  src = fetchFromSourcehut {
    owner = "~jcc";
    repo = "addr-book-combine";
    rev = "c3f3c7022837c7a93c0f6034c56ee0c73e7b76ba";
    hash = "sha256-SENur3p5LxMNnjo/+qiVdrEs+i+rI1PT1wYYdLLqWrg=";
  };

  vendorHash = null;
}
