using UnityEngine;
using UnityEngine.UI; // Required for Canvas/Text

public static class Narrative
{
    private static GameObject GetRoot() => GameObject.Find("Root");

    /// <summary>
    /// Spawns a floating UI Canvas with educational text.
    /// </summary>
    /// <param name="title">Title text.</param>
    /// <param name="content">Body content text.</param>
    /// <param name="position">World position for the card.</param>
    /// <returns>The canvas GameObject.</returns>
    public static GameObject SpawnInfoCard(string title, string content, Vector3 position)
    {
        GameObject canvasObj = new GameObject($"InfoCard_{title}");
        canvasObj.transform.SetParent(GetRoot().transform);
        canvasObj.transform.localPosition = position;
        
        // Setup World Space Canvas
        Canvas canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;
        canvasObj.GetComponent<RectTransform>().sizeDelta = new Vector2(400, 300);
        canvasObj.transform.localScale = Vector3.one * 0.002f; // Scale down for VR

        // Add Background
        GameObject bg = new GameObject("Background");
        bg.transform.SetParent(canvasObj.transform, false);
        Image img = bg.AddComponent<Image>();
        img.color = new Color(0, 0, 0, 0.8f); // Semi-transparent black
        bg.GetComponent<RectTransform>().anchorMin = Vector2.zero;
        bg.GetComponent<RectTransform>().anchorMax = Vector2.one;

        // Add Text
        GameObject textObj = new GameObject("Text");
        textObj.transform.SetParent(canvasObj.transform, false);
        Text txt = textObj.AddComponent<Text>();
        txt.text = $"<size=40><b>{title}</b></size>\n\n{content}";
        txt.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = Color.white;
        textObj.GetComponent<RectTransform>().sizeDelta = new Vector2(380, 280);

        return canvasObj;
    }

    /// <summary>
    /// Spawns a particle effect (e.g., Acid Fumes, Sparks) at a location.
    /// </summary>
    /// <param name="resourcePath">Path to the particle prefab.</param>
    /// <param name="position">World position to spawn at.</param>
    /// <returns>The particle system GameObject.</returns>
    public static GameObject SpawnParticleEffect(string resourcePath, Vector3 position)
    {
        GameObject prefab = Resources.Load<GameObject>(resourcePath);
        if (prefab == null) return null;

        GameObject fx = Object.Instantiate(prefab, GetRoot().transform);
        fx.transform.localPosition = position;
        return fx;
    }

    /// <summary>
    /// Plays an audio clip at a specific location (e.g., Alarm or NPC voice).
    /// </summary>
    /// <param name="clipPath">Path to the audio clip resource.</param>
    /// <param name="position">World position for the sound source.</param>
    /// <param name="loop">Whether the audio should loop.</param>
    public static void PlayAudio(string clipPath, Vector3 position, bool loop = false)
    {
        GameObject audioObj = new GameObject("Audio_" + clipPath);
        audioObj.transform.SetParent(GetRoot().transform);
        audioObj.transform.localPosition = position;

        AudioSource source = audioObj.AddComponent<AudioSource>();
        source.clip = Resources.Load<AudioClip>(clipPath);
        source.spatialBlend = 1.0f; // 3D Sound
        source.loop = loop;
        source.Play();
        
        if (!loop) Object.Destroy(audioObj, source.clip.length + 1f);
    }
}