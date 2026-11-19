{
  inputs = {
    nixpkgs.url = "https://channels.nixos.org/nixos-unstable/nixexprs.tar.zst";
  };

  outputs =
    inputs:
    let
      mkAndroidToolchain =
        pkgs:
        pkgs.androidenv.composeAndroidPackages {
          platformVersions = [
            "34"
            "35"
            "36"
          ];
          buildToolsVersions = [ "36.0.0" ];
          includeEmulator = true;
          includeSystemImages = false;
          includeNDK = true;
          # abiVersions = [ "x86_64" ];
          extraLicenses = [
            "android-googletv-license"
            "android-googlexr-license"
            "android-sdk-arm-dbt-license"
            "android-sdk-preview-license"
            "google-gdk-license"
            "mips-android-sysimage-license"
          ];
          ndkVersion = "28.2.13676358";
          cmakeVersions = [ "3.22.1" ];
        };
    in
    {
      devShells = builtins.mapAttrs (system: pkgs: {
        python = pkgs.callPackage ./api/shell.nix { venvDir = "./api/.venv"; };
        default = pkgs.mkShell (
          let
            pkgs = import inputs.nixpkgs {
              inherit system;
              config.android_sdk.accept_license = true;
              config.allowUnfree = true;
            };
            androidPkgs = mkAndroidToolchain pkgs;
          in
          rec {
            packages = with pkgs; [
              flutter347
              androidPkgs.androidsdk
              androidPkgs.ndk-bundle
              androidPkgs.build-tools
              androidPkgs.cmake
              openjdk17
              gradle
            ];

            GRADLE_OPTS = "-Dorg.gradle.project.android.aapt2FromMavenOverride=${builtins.head androidPkgs.build-tools}/libexec/android-sdk/build-tools/35.0.0/aapt2";

            ANDROID_HOME = "${androidPkgs.androidsdk}/libexec/android-sdk";
            ANDROID_SDK_ROOT = ANDROID_HOME;

            NDK_HOME = androidPkgs.ndk-bundle;
            ANDROID_NDK_HOME = NDK_HOME;
          }
        );
      }) inputs.nixpkgs.legacyPackages;
    };
}
