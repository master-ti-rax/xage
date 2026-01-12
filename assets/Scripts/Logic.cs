using UnityEngine;
using UnityEngine.Events;

public static class Logic
{
    private static GameObject GetRoot() => GameObject.Find("Root");

    /// <summary>
    /// Creates an invisible trigger zone. Useful for detecting if player is in the shower or near the conveyor.
    /// </summary>
    /// <param name="name">Name of the zone object.</param>
    /// <param name="position">World position of the center of the zone.</param>
    /// <param name="size">Size of the box collider trigger.</param>
    /// <param name="onEnter">Action to execute when a collider enters.</param>
    /// <returns>The trigger zone GameObject.</returns>
    public static GameObject CreateTriggerZone(string name, Vector3 position, Vector3 size, UnityAction<Collider> onEnter)
    {
        GameObject zone = new GameObject(name);
        zone.transform.SetParent(GetRoot().transform);
        zone.transform.localPosition = position;

        BoxCollider box = zone.AddComponent<BoxCollider>();
        box.isTrigger = true;
        box.size = size;

        // Attach a simple runtime script to handle the Unity Event
        var handler = zone.AddComponent<RuntimeTriggerHandler>();
        handler.OnEnter.AddListener(onEnter);

        return zone;
    }

    /// <summary>
    /// Sets up a collision rule between a Hazard (Battery) and a Tool (Tape/Spray).
    /// </summary>
    /// <param name="hazardObj">The battery or dangerous object</param>
    /// <param name="requiredTag">The tag the tool must have (e.g., "InsulationTape")</param>
    /// <param name="onSuccess">Action to run if correct tool touches it</param>
    /// <param name="onFail">Action to run if WRONG object touches it (Short Circuit)</param>
	public static void DefineHazardInteraction(GameObject hazardObj, string requiredType, UnityAction onSuccess, UnityAction onFail = null)
    {
        if (hazardObj == null) return;

        var handler = hazardObj.AddComponent<RuntimeCollisionHandler>();
        handler.TargetType= requiredType; // Now looking for "InsulationTape" via ScenarioID
        handler.OnCorrectCollision.AddListener(onSuccess);
        
        if(onFail != null) 
            handler.OnWrongCollision.AddListener(onFail);
    }
}

// --- Helper Runtime Scripts (These stick to the objects) ---

public class RuntimeTriggerHandler : MonoBehaviour
{
    public UnityEvent<Collider> OnEnter = new UnityEvent<Collider>();
    private void OnTriggerEnter(Collider other) => OnEnter.Invoke(other);
}

public class RuntimeCollisionHandler : MonoBehaviour
{
    public string TargetType; 
    public UnityEvent OnCorrectCollision = new UnityEvent();
    public UnityEvent OnWrongCollision = new UnityEvent();

    private void OnCollisionEnter(Collision collision)
    {
        // 1. Try to get our custom ID component from the object hitting us
        Identifier incomingType = collision.gameObject.GetComponent<Identifier>();

        // If the object has no ID, ignore it (or treat as generic collision)
        if (incomingType == null) return;

        // 2. Check logic
        if (incomingType.type == TargetType)
        {
            OnCorrectCollision.Invoke();
        }
        else if (incomingType.type == "PlayerHand" || incomingType.type == "MetalTool")
        {
            // Optional: Logic for failure conditions
            OnWrongCollision.Invoke();
        }
    }
}