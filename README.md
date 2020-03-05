# nixpkgs-updater

Update packages in nixpkgs likes it is 2020.
This tool is still in early development.

## Dependencies

- python 3
- [nix-prefetch](https://github.com/msteen/nix-prefetch/)

## USAGE

````
$ NIX_PATH=nixpkgs=/path/to/git python nixpkgs-updater.py attribute [version]
```

Example:

````
$ NIX_PATH=nixpkgs=/path/to/git python nixpkgs-updater.py nixpkgs-review
```

(fetches the latest github release)

or:

```
$ NIX_PATH=nixpkgs=/path/to/git python nixpkgs-updater.py nixpkgs-review 2.1.1
```
