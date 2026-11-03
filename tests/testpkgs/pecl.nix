{ php, libyaml }:
php.buildPecl {
  pname = "yaml";
  version = "2.2.4";
  hash = "sha256-jrNTuvh/FbG2Ksbrcci1iWhZWKH+iw49IqxZVg0OiRM=";

  buildInputs = [ libyaml ];
  configureFlags = [ "--with-yaml=${libyaml.dev}" ];
}
