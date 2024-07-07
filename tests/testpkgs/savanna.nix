{
  stdenv,
  fetchurl,
  gamin,
}:

stdenv.mkDerivation rec {
  pname = "fileschanged";
  version = "0.6.8";

  src = fetchurl {
    url = "mirror://savannah/fileschanged/fileschanged-${version}.tar.gz";
    sha256 = "0ajc9h023vzpnlqqjli4wbvs0q36nr5p9msc3wzbic8rk687qcxc";
  };

  buildInputs = [ gamin ];

  doCheck = true;
}
