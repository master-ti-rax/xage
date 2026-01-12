using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables; // Required for XRGrabInteractable
using Viroo.Interactions.Grab;
using Virtualware.Networking.Client;                   // Required for NetworkObject
using Virtualware.Networking.Client.Components;                   // Required for NetworkTransform
public static class Spawner
{
    private static GameObject GetRoot() => GameObject.Find("Root");

    /// <summary>
    /// Spawns a non-interactive object (Decor, Furniture, Walls).
    /// </summary>
    /// <param name="resourcePath">Path to the resource prefab.</param>
    /// <param name="position">World position to spawn at.</param>
    /// <param name="rotation">World rotation to spawn with.</param>
    /// <returns>The spawned static GameObject.</returns>
    public static GameObject SpawnStatic(string resourcePath, Vector3 position, Vector3 rotation)
    {
        GameObject obj = LoadAndInstantiate(resourcePath, position, rotation);
        if (obj == null) return null;

        // Ensure it has a collider for physics interactions (even if static)
        if (obj.GetComponent<Collider>() == null)
            obj.AddComponent<MeshCollider>();

        return obj;
    }

    /// <summary>
    /// Spawns an interactable object using the specific Viroo Component stack.
    /// Stack: Rigidbody -> XRGrabInteractable -> NetworkObject -> NetworkTransform
    /// </summary>
    /// <param name="resourcePath">Path to the resource prefab.</param>
    /// <param name="position">World position to spawn at.</param>
    /// <param name="rotation">World rotation to spawn with.</param>
    /// <param name="mass">Mass of the Rigidbody.</param>
    /// <param name="tag">Identifier tag for logic checks.</param>
    /// <returns>The spawned interactable GameObject.</returns>
    public static GameObject SpawnInteractable(string resourcePath, Vector3 position, Vector3 rotation, float mass = 0.5f, string tag = "Untagged")
    {
        // 1. Load the asset (Mesh + Collider usually included in prefab)
        GameObject grabObj = LoadAndInstantiate(resourcePath, position, rotation);
        if (grabObj == null) return null;

        var id = grabObj.AddComponent<Identifier>();
        //id.ID = objectID;
        id.type = tag;

        grabObj.AddComponent<BoxCollider>();

        // 2. Add Rigidbody (Required for physics interaction)
        Rigidbody rb = grabObj.AddComponent<Rigidbody>();
        rb.mass = mass;
        rb.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;

        // 3. Add Unity's XR Grab Interactable
        // This handles the local physical grabbing logic
        XRGrabInteractable grabInteractable = grabObj.AddComponent<XRGrabInteractable>();
        grabInteractable.movementType = XRBaseInteractable.MovementType.Kinematic; 

        // 4. Add Viroo Network Object
        // Gives the object a unique identity across the network
        NetworkObject netObj = grabObj.AddComponent<NetworkObject>();
        netObj.ObjectId = NetworkObject.GenerateRandomId(grabObj.scene);

        // 5. Add Network Transform
        // Syncs the position/rotation across users (Replacing my previous error)
        grabObj.AddComponent<NetworkTransform>();

        grabObj.AddComponent<VirooXRGrabInteractable>();

        // Optional: Debug log
        Debug.Log($"[VirooSpawner] Spawned Viroo Grabbable: {grabObj.name}");
        
        return grabObj;
    }

    // Internal Helper
    private static GameObject LoadAndInstantiate(string path, Vector3 pos, Vector3 rot)
    {
        GameObject prefab = Resources.Load<GameObject>(path);
        if (prefab == null)
        {
            Debug.LogError($"[VirooSpawner] Resource not found: {path}");
            return null;
        }

        GameObject instance = Object.Instantiate(prefab, GetRoot().transform);
        instance.name = prefab.name; // Clean name
        instance.transform.localPosition = pos;
        instance.transform.localRotation = Quaternion.Euler(rot);
        return instance;
    }
}