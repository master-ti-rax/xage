using UnityEngine;
using System.Collections.Generic;

public class SafetyGlovesPlacement : MonoBehaviour
{
    public Vector3 glovesPosition = new Vector3(0.5f, 1.2f, 2.0f); // Position relative to the user's starting position
    public Vector3 glovesScale = new Vector3(1.0f, 1.0f, 1.0f);   // Scale of the gloves

    void Start()
    {
        PlaceGloves();
    }

    void PlaceGloves()
    {
        // Load the Safety Gloves prefab
        GameObject safetyGlovesPrefab = Resources.Load<GameObject>("SafetyGloves/SafetyGloves");    

        if (safetyGlovesPrefab != null)
        {
            // Instantiate the gloves at the specified position and scale
            GameObject glovesInstance = Instantiate(safetyGlovesPrefab, transform.position + glovesPosition, Quaternion.identity, transform);

            // Apply scaling
            glovesInstance.transform.localScale = glovesScale;

            // Ensure the gloves are visible to the user
            if (glovesInstance.GetComponent<Renderer>() != null)
            {
                glovesInstance.GetComponent<Renderer>().enabled = true;
            }

            Debug.Log("Safety Gloves placed successfully at position: " + glovesPosition);
        }
        else
        {
            Debug.LogError("Failed to load Safety Gloves prefab. Please check the asset path.");    
        }
    }
}