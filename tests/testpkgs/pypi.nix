{
  buildPythonPackage,
  fetchPypi,
  setuptools,
  twisted,
  pytestCheckHook,
  hello,
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

  nativeCheckInputs = [
    pytestCheckHook
    twisted
  ];

  pytestFlagsArray = [ "mpd/tests.py" ];

  pythonImportsCheck = [ "mpd" ];

  passthru.tests = {
    testCompile = hello;
    testCreate = hello;
  };

  meta.changelog = "https://github.com/Mic92/python-mpd2/blob/${version}/doc/changes.rst";
}
