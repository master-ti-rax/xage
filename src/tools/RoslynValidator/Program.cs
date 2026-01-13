using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using System.Text.Json;
using System.Xml.Linq;

namespace RoslynValidator
{
    class Program
    {
        static List<string> ParseCsprojReferences(string csprojPath)
        {
            var references = new List<string>();
            try
            {
                var doc = XDocument.Load(csprojPath);
                var ns = doc.Root?.Name.Namespace;
                var csprojDir = Path.GetDirectoryName(csprojPath) ?? string.Empty;
                
                // Extract HintPath from Reference elements
                var hintPaths = doc.Descendants()
                    .Where(e => e.Name.LocalName == "Reference")
                    .Elements()
                    .Where(e => e.Name.LocalName == "HintPath")
                    .Select(e => e.Value)
                    .Where(p => !string.IsNullOrWhiteSpace(p))
                    .Select(p => {
                        // Resolve relative paths based on csproj directory
                        if (!Path.IsPathRooted(p))
                        {
                            return Path.GetFullPath(Path.Combine(csprojDir, p));
                        }
                        return p;
                    })
                    .Where(p => File.Exists(p))
                    .ToList();
                
                references.AddRange(hintPaths);
            }
            catch { }
            return references;
        }

        static void Main(string[] args)
        {
            // Force English culture for error messages
            CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");
            Thread.CurrentThread.CurrentCulture = new CultureInfo("en-US");
            Thread.CurrentThread.CurrentUICulture = new CultureInfo("en-US");

            if (args.Length == 0)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { status = "error", message = "No file path provided" }));
                return;
            }

            string filePath = args[0];
            if (!File.Exists(filePath))
            {
                Console.WriteLine(JsonSerializer.Serialize(new { status = "error", message = "File not found" }));
                return;
            }

            try 
            {
                // Collect all .cs files in the same directory (and subdirectories)
                // so the validator compiles the file together with its peers
                var fileDir = Path.GetDirectoryName(filePath) ?? Directory.GetCurrentDirectory();
                var csFiles = Directory.GetFiles(fileDir, "*.cs", SearchOption.AllDirectories);
                var syntaxTrees = new List<SyntaxTree>();
                foreach (var f in csFiles)
                {
                    try
                    {
                        var txt = File.ReadAllText(f);
                        syntaxTrees.Add(CSharpSyntaxTree.ParseText(txt, path: f));
                    }
                    catch { }
                }

                // Fallback: if no other files found, parse the provided file alone
                if (!syntaxTrees.Any())
                {
                    var code = File.ReadAllText(filePath);
                    syntaxTrees.Add(CSharpSyntaxTree.ParseText(code, path: filePath));
                }

                // If Environment.cs (or related assets) are not in the same folder,
                // attempt to locate them in the repository root (search for eXRage.sln),
                // and include `Environment.cs` and all files under `assets/Scripts`.
                bool hasEnvironmentFile = syntaxTrees.Any(st => !string.IsNullOrEmpty(st.FilePath) && Path.GetFileName(st.FilePath).Equals("Environment.cs", StringComparison.OrdinalIgnoreCase));
                if (!hasEnvironmentFile)
                {
                    DirectoryInfo dirInfo2 = new DirectoryInfo(fileDir);
                    DirectoryInfo repoRoot2 = dirInfo2;
                    while (repoRoot2 != null && !repoRoot2.GetFiles("eXRage.sln", SearchOption.TopDirectoryOnly).Any())
                    {
                        repoRoot2 = repoRoot2.Parent;
                    }

                    string searchRoot = repoRoot2?.FullName ?? Directory.GetCurrentDirectory();

                    try
                    {
                        var assetsScripts = Path.Combine(searchRoot, "assets", "Scripts");
                        if (Directory.Exists(assetsScripts))
                        {
                            var assetFiles = Directory.GetFiles(assetsScripts, "*.cs", SearchOption.AllDirectories);
                            foreach (var f in assetFiles)
                            {
                                try
                                {
                                    var txt = File.ReadAllText(f);
                                    syntaxTrees.Add(CSharpSyntaxTree.ParseText(txt, path: f));
                                }
                                catch { }
                            }
                        }
                    }
                    catch { }
                }
                
                // Gather references
                var references = new List<MetadataReference>();
                
                // 1. Add Unity's mono runtime references only (avoid type forwarding conflicts)
                string unityMonoPath = "/home/amartis/Unity/Hub/Editor/2022.3.40f1/Editor/Data/MonoBleedingEdge/lib/mono/unityaot-linux";
                if (Directory.Exists(unityMonoPath))
                {
                    // Core mono assemblies - these contain all the types Unity uses
                    var monoRefs = new[] { 
                        "mscorlib.dll", 
                        "System.dll", 
                        "System.Core.dll",
                        "System.Xml.dll",
                        "System.Numerics.dll",
                        "System.Runtime.Serialization.dll",
                        "System.ComponentModel.Composition.dll"
                    };
                    foreach (var asm in monoRefs)
                    {
                        var path = Path.Combine(unityMonoPath, asm);
                        if (File.Exists(path))
                        {
                            try
                            {
                                references.Add(MetadataReference.CreateFromFile(path));
                            }
                            catch { }
                        }
                    }
                    
                    // Add netstandard 2.1.0.0 from Facades folder
                    var netstandardPath = Path.Combine(unityMonoPath, "Facades", "netstandard.dll");
                    if (File.Exists(netstandardPath))
                    {
                        try
                        {
                            references.Add(MetadataReference.CreateFromFile(netstandardPath));
                        }
                        catch { }
                    }
                }
                
                // 2. Fallback to system references if Unity mono not found
                if (references.Count == 0)
                {
                    var objectPath = typeof(object).Assembly.Location;
                    var coreDir = Path.GetDirectoryName(objectPath);
                    
                    if (coreDir == null)
                    {
                        throw new Exception("Could not determine system assembly directory.");
                    }

                    // Add common system assemblies
                    string[] systemAssemblies = {
                        "System.Private.CoreLib.dll",
                        "System.Runtime.dll",
                        "System.Console.dll",
                        "netstandard.dll",
                        "System.Linq.dll",
                        "System.Collections.dll"
                    };

                    foreach (var asm in systemAssemblies)
                    {
                        var path = Path.Combine(coreDir, asm);
                        if (File.Exists(path))
                            references.Add(MetadataReference.CreateFromFile(path));
                    }
                }

                // 3. Unity References from .csproj
                // Find either the Unity project root directly or via eXRage repo
                DirectoryInfo dirInfo = new DirectoryInfo(fileDir);
                string unityProjectPath = null;
                
                // First check if we're already in a Unity project (look for .csproj files)
                DirectoryInfo currentDir = dirInfo;
                while (currentDir != null)
                {
                    if (currentDir.GetFiles("Assembly-CSharp.csproj", SearchOption.TopDirectoryOnly).Any())
                    {
                        unityProjectPath = currentDir.FullName;
                        break;
                    }
                    currentDir = currentDir.Parent;
                }
                
                // If not found, look for eXRage repo and read .env
                if (unityProjectPath == null)
                {
                    DirectoryInfo repoRoot = dirInfo;
                    while (repoRoot != null && !repoRoot.GetFiles("eXRage.sln", SearchOption.TopDirectoryOnly).Any())
                    {
                        repoRoot = repoRoot.Parent;
                    }

                    if (repoRoot != null)
                    {
                        // Try to find UNITY_PROJECT_PATH from .env file
                        var envPath = Path.Combine(repoRoot.FullName, ".env");
                        
                        if (File.Exists(envPath))
                        {
                            var envLines = File.ReadAllLines(envPath);
                            foreach (var line in envLines)
                            {
                                if (line.StartsWith("UNITY_PROJECT_PATH="))
                                {
                                    unityProjectPath = line.Substring("UNITY_PROJECT_PATH=".Length).Trim();
                                    // Resolve relative path
                                    if (!Path.IsPathRooted(unityProjectPath))
                                    {
                                        unityProjectPath = Path.GetFullPath(Path.Combine(repoRoot.FullName, unityProjectPath));
                                    }
                                    break;
                                }
                            }
                        }
                    }
                }
                
                if (!string.IsNullOrEmpty(unityProjectPath) && Directory.Exists(unityProjectPath))
                {
                    var csprojPath = Path.Combine(unityProjectPath, "Assembly-CSharp.csproj");
                    if (File.Exists(csprojPath))
                    {
                        var csprojRefs = ParseCsprojReferences(csprojPath);
                        foreach (var dllPath in csprojRefs)
                        {
                            try
                            {
                                references.Add(MetadataReference.CreateFromFile(dllPath));
                            }
                            catch { }
                        }
                    }
                }

                // 4. Always add Unity engine modules as fallback (needed even with csproj refs)
                string unityBasePath = "/home/amartis/Unity/Hub/Editor/2022.3.40f1/Editor/Data/Managed/UnityEngine";
                
                if (Directory.Exists(unityBasePath))
                {
                    var unityModules = Directory.GetFiles(unityBasePath, "UnityEngine.*Module.dll");
                    foreach (var dll in unityModules)
                    {
                        try
                        {
                            references.Add(MetadataReference.CreateFromFile(dll));
                        }
                        catch { }
                    }
                }

                // Create Compilation
                var compilation = CSharpCompilation.Create("ValidatorAssembly")
                    .WithOptions(new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary))
                    .AddReferences(references)
                    .AddSyntaxTrees(syntaxTrees.ToArray());

                var diagnostics = compilation.GetDiagnostics();

                // Filter errors to only include those from the target file
                var normalizedTargetPath = Path.GetFullPath(filePath);
                var errors = diagnostics
                    .Where(d => d.Severity == DiagnosticSeverity.Error)
                    .Where(d => {
                        var diagPath = d.Location.SourceTree?.FilePath;
                        if (string.IsNullOrEmpty(diagPath)) return false;
                        var normalizedDiagPath = Path.GetFullPath(diagPath);
                        return normalizedDiagPath.Equals(normalizedTargetPath, StringComparison.OrdinalIgnoreCase);
                    })
                    .Select(d => new
                    {
                        id = d.Id,
                        message = d.GetMessage(),
                        line = d.Location.GetLineSpan().StartLinePosition.Line + 1,
                        column = d.Location.GetLineSpan().StartLinePosition.Character + 1
                    })
                    .ToList();

                var result = new
                {
                    status = errors.Any() ? "error" : "success",
                    errors = errors
                };

                Console.WriteLine(JsonSerializer.Serialize(result));
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { status = "error", message = ex.Message }));
            }
        }
    }
}
