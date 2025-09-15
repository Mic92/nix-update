{
  buildPythonPackage,
  fetchPypi,
  setuptools,
  twisted,
  mock,
  pytestCheckHook,
}:

buildPythonPackage rec {
  pname = "python-mpd2";
  version = "2.0.0";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  build-system = [ setuptools ];

  checkInputs = [
    pytestCheckHook
    twisted
    mock
  ];

  pytestFlagsArray = [ "mpd/tests.py" ];

  meta.changelog = "https://github.com/Mic92/python-mpd2/blob/${version}/doc/changes.rst";
}
