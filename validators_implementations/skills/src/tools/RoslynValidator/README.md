# Roslyn Validator Tool

This tool is a C# Console Application that uses the Roslyn compiler (Microsoft.CodeAnalysis) to validate C# code syntax.

## Prerequisites

- .NET SDK 8.0 or later

## Usage

You can run the validator directly using `dotnet run`:

```bash
dotnet run --project RoslynValidator.csproj -- <path_to_cs_file>
```

Or build it first for better performance:

```bash
dotnet build -c Release
./bin/Release/net8.0/RoslynValidator <path_to_cs_file>
```

## Integration

The Python tool `fetch_csharp_errors` in `src/tools/langchain_tools.py` is configured to run this project using `dotnet run`.
If you want to use a pre-built binary, you would need to modify the Python tool to point to the binary instead of using `dotnet run`.
