using UnityEngine;

public static class Environment
{
    private static GameObject GetRoot() => GameObject.Find("Root");

    public static void SetupStandardScenary()
    {
        GameObject root = GetRoot();

        CreateDirectionalLight(root);
        Spawner.SpawnStatic(
            "Scenary/Scenary", 
            Vector3.zero, 
            Vector3.zero
        );
        
        Debug.Log("[VirooEnvironment] Standard room initialized.");
    }
    /// <summary>
    /// Master function to set up a standard Viroo room (Ground + Sun).
    /// </summary>
    public static void SetupStandardRoom()
    {
        GameObject root = GetRoot();
        if (root == null) return;

        CreateGround(root);
        CreateDirectionalLight(root);
        
        Debug.Log("[VirooEnvironment] Standard room initialized.");
    }

    /// <summary>
    /// Creates a walkable floor.
    /// </summary>
    /// <param name="root">The root GameObject to attach the ground to.</param>
    public static void CreateGround(GameObject root)
    {
        // Check if ground already exists to avoid duplicates
        if (root.transform.Find("Ground Plane") != null) return;

        GameObject ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground Plane";
        ground.transform.SetParent(root.transform);
        ground.transform.localPosition = Vector3.zero;
        ground.transform.localScale = Vector3.one * 2.0f; // Make it 20x20 meters

        // Add a simple material color if available, otherwise default white
        Renderer rend = ground.GetComponent<Renderer>();
        rend.material.color = new Color(0.3f, 0.3f, 0.3f); // Dark grey concrete look
        
        // Ensure Teleportation works (Viroo usually needs a Collider, which Plane has)
    }

    /// <summary>
    /// Creates a sun-like light source.
    /// </summary>
    /// <param name="root">The root GameObject to attach the light to.</param>
    public static void CreateDirectionalLight(GameObject root)
    {
        if (root.transform.Find("Directional Light") != null) return;

        GameObject lightObj = new GameObject("Directional Light");
        lightObj.transform.SetParent(root.transform);
        
        // Angled to look like generic afternoon sun
        lightObj.transform.localPosition = new Vector3(0, 10, 0);
        lightObj.transform.localRotation = Quaternion.Euler(50f, -30f, 0f);

        Light lightComp = lightObj.AddComponent<Light>();
        lightComp.type = LightType.Directional;
        lightComp.intensity = 1.0f;
        lightComp.shadows = LightShadows.Soft;
    }
}