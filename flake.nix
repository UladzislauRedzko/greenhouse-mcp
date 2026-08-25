{
  description = "Greenhouse Harvest API v3 MCP server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-darwin"
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python313;
        in
        rec {
          default = python.pkgs.buildPythonApplication {
            pname = "greenhouse-mcp";
            version = "0.1.0";
            src = ./.;
            pyproject = true;

            build-system = with python.pkgs; [
              setuptools
              wheel
            ];

            dependencies = with python.pkgs; [
              fastmcp
              httpx
              pydantic
              python-dotenv
            ];

            pythonImportsCheck = [
              "src.greenhouse_client"
              "src.greenhouse_mcp"
            ];

            meta = {
              description = "MCP server for Greenhouse Harvest API v3";
              mainProgram = "greenhouse-mcp";
            };
          };
          greenhouse-mcp = default;
        });

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/greenhouse-mcp";
        };
      });

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python313.withPackages (ps: with ps; [
            fastmcp
            httpx
            pydantic
            python-dotenv
            pytest
            pytest-asyncio
            ruff
            black
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
            ];

            shellHook = ''
              echo "Greenhouse MCP dev shell"
              echo "Run: python test_server.py"
              echo "Run server: python -m src.greenhouse_mcp"
            '';
          };
        });

      formatter = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        pkgs.nixpkgs-fmt);
    };
}
