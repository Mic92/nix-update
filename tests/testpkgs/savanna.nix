{
  stdenv,
  fetchurl,
  glib,
  gtk2,
  pkg-config,
  hamlib,
}:
stdenv.mkDerivation rec {
  pname = "xlog";
  version = "2.0.24";

  src = fetchurl {
    url = "mirror://savannah/${pname}/${pname}-${version}.tar.gz";
    hash = "sha256-NYC3LgoLXnJQURcZTc2xHOzOleotrWtOETMBgadf2qU=";
  };

  # glib-2.62 deprecations
  env.NIX_CFLAGS_COMPILE = "-DGLIB_DISABLE_DEPRECATION_WARNINGS";

  nativeBuildInputs = [ pkg-config ];
  buildInputs = [
    glib
    gtk2
    hamlib
  ];
}
