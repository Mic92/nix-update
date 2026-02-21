{
  importPath,
  flakeImportPath ? null,
  attribute,
  system ? builtins.currentSystem,
  isFlake ? false,
  sanitizePositions ? true,
}:

let
  inherit (builtins)
    getFlake
    stringLength
    substring
    foldl'
    fromJSON
    ;

  # Parse the attribute path from JSON string
  attributePath = fromJSON attribute;
  # In case of flakes, we must pass a url with git attrs of the flake
  # otherwise the entire directory is copied to nix store
  flakeOrImportPath = if flakeImportPath != null then flakeImportPath else importPath;

  # Try to navigate nested attributes, returning { success = bool; value = ...; }
  tryGetAttrPath =
    attrPath: root:
    foldl'
      (
        acc: attr:
        if acc.success && acc.value ? ${attr} then
          {
            success = true;
            value = acc.value.${attr};
          }
        else
          {
            success = false;
            value = null;
          }
      )
      {
        success = true;
        value = root;
      }
      attrPath;

  pkg =
    if isFlake then
      let
        flake = getFlake flakeOrImportPath;
        packages = flake.packages.${system} or { };
        # Try packages.${system} first, fall back to flake root if attribute not found
        packagesResult = tryGetAttrPath attributePath packages;
      in
      if packagesResult.success then packagesResult.value else (tryGetAttrPath attributePath flake).value
    else
      let
        pkgs = import importPath;
        args = builtins.functionArgs pkgs;
        inputs =
          (if args ? system then { system = system; } else { })
          // (if args ? overlays then { overlays = [ ]; } else { });
      in
      (tryGetAttrPath attributePath (pkgs inputs)).value;

  sanitizePosition =
    if isFlake && sanitizePositions then
      let
        flake = getFlake flakeOrImportPath;
        outPath = flake.outPath;
        outPathLen = stringLength outPath;
      in
      { file, ... }@pos:
      if substring 0 outPathLen file != outPath then
        throw "${file} is not in ${outPath}"
      else
        pos // { file = importPath + substring outPathLen (stringLength file - outPathLen) file; }
    else
      x: x;

  positionFromMeta =
    pkg:
    let
      parts = builtins.match "(.*):([0-9]+)" pkg.meta.position;
    in
    {
      file = builtins.elemAt parts 0;
      line = builtins.fromJSON (builtins.elemAt parts 1);
    };

  raw_version_position = sanitizePosition (builtins.unsafeGetAttrPos "version" pkg);

  position =
    if pkg ? isRubyGem then
      raw_version_position
    else if pkg ? isPhpExtension then
      raw_version_position
    else if (builtins.unsafeGetAttrPos "src" pkg) != null then
      sanitizePosition (builtins.unsafeGetAttrPos "src" pkg)
    else
      sanitizePosition (positionFromMeta pkg);

  has_update_script = pkg.passthru.updateScript or null != null;

in
{
  name = pkg.name;
  pname = pkg.pname;
  old_version = pkg.version or (builtins.parseDrvName pkg.name).version;
  inherit raw_version_position;
  filename = position.file;
  line = position.line;
  urls = pkg.src.urls or null;
  url = pkg.src.url or null;
  rev = pkg.src.rev or null;
  tag = pkg.src.tag or null;
  hash = pkg.src.outputHash or null;
  fod_subpackage = pkg.outputHash or null;
  go_modules = pkg.goModules.outputHash or null;
  go_modules_old = pkg.go-modules.outputHash or null;
  cargo_deps = pkg.cargoDeps.outputHash or null;
  cargo_vendor_deps = pkg.cargoDeps.vendorStaging.outputHash or null;
  raw_cargo_lock =
    if pkg ? cargoDeps.lockFile then
      let
        inherit (pkg.cargoDeps) lockFile;
        res = builtins.tryEval (sanitizePosition {
          file = toString lockFile;
        });
      in
      if res.success then res.value.file else false
    else
      null;
  composer_deps = pkg.composerVendor.outputHash or null;
  composer_deps_old = pkg.composerRepository.outputHash or null;
  npm_deps = pkg.npmDeps.outputHash or null;
  pnpm_deps = pkg.pnpmDeps.outputHash or null;
  yarn_deps = pkg.yarnOfflineCache.outputHash or null;
  yarn_deps_old = pkg.offlineCache.outputHash or null;
  bun_deps = pkg.bunDeps.outputHash or null;
  maven_deps = pkg.fetchedMavenDeps.outputHash or null;
  has_nuget_deps = pkg ? nugetDeps;
  has_gradle_mitm_cache = pkg ? mitmCache;
  mix_deps = pkg.mixFodDeps.outputHash or null;
  zig_deps = pkg.zigDeps.outputHash or null;
  tests = builtins.attrNames (pkg.passthru.tests or { });
  inherit has_update_script;
  src_homepage = pkg.src.meta.homepage or null;
  changelog = pkg.meta.changelog or null;
  maintainers = pkg.meta.maintainers or null;
}
