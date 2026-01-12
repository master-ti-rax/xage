using UnityEngine;

public static class Actions
{
    /// <summary>
    /// Action: The user successfully taped the battery.
    /// </summary>
    /// <param name="battery">The battery GameObject that was secured.</param>
    public static void OnBatterySecured(GameObject battery)
    {
        Debug.Log("[ScenarioActions] Battery Secured Triggered");

        // 1. Visual Feedback: Show "Safe" UI
        Narrative.SpawnInfoCard(
            "SAFE", 
            "Terminals Isolated.\nProceed to next station.", 
            battery.transform.position + new Vector3(0, 0.8f, 0)
        );

        // 2. Audio Feedback: Positive Chime
        Narrative.PlayAudio("Audio/success", battery.transform.position);

        // 3. Optional: Change the battery color or swap mesh to show tape
        battery.GetComponent<Renderer>().material.color = Color.green;
    }

    /// <summary>
    /// Action: The user touched live terminals with a tool or hand.
    /// </summary>
    /// <param name="battery">The battery GameObject that triggered the flash.</param>
    public static void OnArcFlashTriggered(GameObject battery)
    {
        Debug.Log("[ScenarioActions] Arc Flash Triggered");

        // 1. Visual Feedback: Explosion Particle
        Narrative.SpawnParticleEffect("FX/ArcFlashExplosion", battery.transform.position);

        // 2. Audio Feedback: Loud Zap
        Narrative.PlayAudio("Audio/electricZap", battery.transform.position);

        // 3. Visual Feedback: Warning UI
        Narrative.SpawnInfoCard(
            "CRITICAL FAILURE", 
            "Arc Flash Detected!\n19,000°F Heat.\nUser Injured.", 
            battery.transform.position + new Vector3(0, 0.8f, 0)
        );

        // 4. Physics: Maybe push the tool away (Simulate explosion force)
        // We find the tool near the battery (logic simplified for example)
        Rigidbody rb = battery.GetComponent<Rigidbody>();
        if(rb != null) rb.AddExplosionForce(500f, battery.transform.position, 3f);
    }

    /// <summary>
    /// Action: The user enters the safety shower area.
    /// </summary>
    /// <param name="playerCollider">The collider of the player entering the shower.</param>
    public static void OnShowerEntered(Collider playerCollider)
    {
        Debug.Log("[ScenarioActions] Player entered Shower");

        // 1. Visual: Water particles
        Narrative.SpawnParticleEffect("FX/Shower", playerCollider.transform.position + Vector3.up * 2);

        // 2. Audio: Water sound
        //Narrative.PlayAudio("Audio/WaterFlow", playerCollider.transform.position, loop: true);
    }
}