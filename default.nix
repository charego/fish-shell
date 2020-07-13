with import <nixpkgs> {};

stdenv.mkDerivation {
    name = "fish-dev";

    src = if lib.inNixShell then null else lib.cleanSource ./.;

    nativeBuildInputs = [
        cmake
    ];

    buildInputs = [
        gettext
        ncurses
        pcre2
        python38Packages.sphinx
    ];

    patchPhase = ''
        patchShebangs build_tools/git_version_gen.sh
    '';

    shellHook = ''
        echo "Welcome to the fish-shell build environment!"
    '';
}
