# nix-update

Update nix packages likes it is 2020.
This tool is still in early development.

## Dependencies

- python 3
- [nix-prefetch](https://github.com/msteen/nix-prefetch/)

## USAGE

First change to your directory containing the nix expression (Could be a nixpkgs or your own repository). Than run `nix-update` as follows

```
$ python nix-update.py attribute [version]
```

This example will fetch the latest github release:

```
$ python nix-update.py nixpkgs-review
```

It is also possible to specify the version manually

```
$ python nix-update.py nixpkgs-review 2.1.1
```

## TODO

- [ ] make it a proper python/nix package
- [ ] optionally commit update
- [ ] optionally(?) build update
