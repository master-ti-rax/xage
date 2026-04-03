using UnityEngine;
using System.Collections.Generic;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;
using Viroo.Interactions.Grab;
using Viroo.Interactions.XRInteractionToolkit;

public class SceneLogic
{
    static void CreateScene()
    {
        // Initialize environment
        EnvironmentHelper.SetupStandardScenary();

        // #region Step 1: Instantiate the Scenery

        GameObject inspectionTable = Object.Instantiate(Resources.Load<GameObject>("GAIA_Under_Table_Inspection/model"));

        GameObject controlConsole = Object.Instantiate(Resources.Load<GameObject>("Control_Console/model"));

        GameObject exitSign = Object.Instantiate(Resources.Load<GameObject>("Exit_Sign_Board/model"));

        GameObject gloves = Object.Instantiate(Resources.Load<GameObject>("gloves/model"));

        GameObject battery = Object.Instantiate(Resources.Load<GameObject>("Battery/model"));

        GameObject robotArm = Object.Instantiate(Resources.Load<GameObject>("Robot_Arm/model"));


        if (inspectionTable != null) inspectionTable.name = "Inspection Table";

        if (controlConsole != null) controlConsole.name = "Control Console";

        if (exitSign != null) exitSign.name = "Emergency Exit";

        if (gloves != null) gloves.name = "Protective Gloves";

        if (battery != null) battery.name = "Battery";

        if (robotArm != null) robotArm.name = "Robot Arm";
        // #endregion Step 1

    }
}
