using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using System.Text.Json;

namespace RoslynValidator
{
    class Program
    {
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
                string code = File.ReadAllText(filePath);
                var syntaxTree = CSharpSyntaxTree.ParseText(code);
                
                // Gather references
                var references = new List<MetadataReference>();
                
                // 1. System References (Basic)
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

                // 2. Unity References
                // Try to find Unity references in standard locations
                string unityBasePath = "/home/amartis/Unity/Hub/Editor/2022.3.40f1/Editor/Data/Managed/UnityEngine";
                
                if (Directory.Exists(unityBasePath))
                {
                    var unityModules = Directory.GetFiles(unityBasePath, "UnityEngine.*Module.dll");
                    foreach (var dll in unityModules)
                    {
                        references.Add(MetadataReference.CreateFromFile(dll));
                    }
                }
                else
                {
                    // Fallback to previous path if the new one doesn't exist (though ls showed it does)
                     string oldUnityBasePath = "/home/amartis/Unity/Hub/Editor/2022.3.40f1/Editor/Data/Managed";
                     string[] unityDlls = {
                        Path.Combine(oldUnityBasePath, "UnityEngine/UnityEngine.CoreModule.dll"),
                        Path.Combine(oldUnityBasePath, "UnityEngine/UnityEngine.PhysicsModule.dll"),
                        Path.Combine(oldUnityBasePath, "UnityEngine/UnityEngine.AnimationModule.dll")
                    };

                    foreach (var dll in unityDlls)
                    {
                        if (File.Exists(dll))
                        {
                            references.Add(MetadataReference.CreateFromFile(dll));
                        }
                    }
                }

                // Create Compilation
                var compilation = CSharpCompilation.Create("ValidatorAssembly")
                    .WithOptions(new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary))
                    .AddReferences(references)
                    .AddSyntaxTrees(syntaxTree);

                var diagnostics = compilation.GetDiagnostics();

                var errors = diagnostics
                    .Where(d => d.Severity == DiagnosticSeverity.Error)
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
