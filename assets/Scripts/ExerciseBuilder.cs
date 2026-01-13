using UnityEngine;
using UnityEngine.Events;
using System.Collections.Generic;
using System.Reflection;
using System.Linq;
using System;
using Viroo.ExerciseBuilder.Steps;
using Viroo.ExerciseBuilder.Execution.Handlers;
using Viroo.ExerciseBuilder.Localization;
using Viroo.ExerciseBuilder.Execution;
using Viroo.ExerciseBuilder.Scene;
using Viroo.ExerciseBuilder.Process;
using Viroo.ExerciseBuilder.Instructions;
using Viroo.ExerciseBuilder;
using Viroo.Interactions.XRInteractionToolkit;
using Viroo.Teleport;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;
using Viroo.Interactions.Grab;
using Viroo.Interactions;

/// <summary>
/// Defines the type of interaction required for an objective.
/// </summary>
public enum InteractionType
{
    Grab,
    Use,
    Snap,
    Touch
}

/// <summary>
/// A static builder class to construct educational exercises in the scene using Viroo Exercise Builder components.
/// </summary>
public static class ExerciseBuilder
{
    private static GameObject exercise;
	private static string title;
	private static string description;
    private static StepRunner _stepRunner;
    // private static ProcessStep _ProcessStep;
    // private static StepGroup _groupStep;
    // private static MultipleProcessStep _multipleStep;
	private static GameObject GetRoot() => GameObject.Find("Root");

    /// <summary>
    /// Initializes the exercise container. Must be called first.
    /// </summary>
    /// <param name="title">The title of the exercise (e.g., "Pill Maker Training").</param>
    /// <param name="description">A short description of the exercise.</param>
    /// <returns>The root GameObject of the created exercise.</returns>
    public static GameObject CreateExercise(string title, string description)
    {

        GameObject root = GetRoot();

		exercise = new GameObject($"{title}");
		exercise.transform.SetParent(root.transform);

		ExerciseBuilder.title = title;
		ExerciseBuilder.description = description;

		// Create StepRunner
		GameObject stepRunnerObj = new GameObject("StepRunner");
        stepRunnerObj.transform.SetParent(exercise.transform);
        _stepRunner = stepRunnerObj.AddComponent<StepRunner>();
        
        // Create the main ProcessStep
        GameObject sceneNetworkVariablesObj = new GameObject("sceneNetworkVariables");
        sceneNetworkVariablesObj.transform.SetParent(root.transform);
        
        Debug.Log($"[ExerciseBuilder] Initialized Exercise: {title}");

        return exercise;
    }

    /// <summary>
    /// Instantiates the interactive panel prefab and allows disabling specific child views.
    /// </summary>
    /// <param name="prefabPath">Resource path to the panel prefab.</param>
    /// <param name="position">World position for the panel.</param>
    /// <param name="rotation">World rotation for the panel.</param>
    /// <param name="parentTransform">Parent transform to attach the panel to.</param>
    /// <param name="viewsToDisable">List of names of child objects (views) to disable.</param>
    /// <returns>The instantiated panel GameObject.</returns>
    public static GameObject CreateInteractivePanel(string prefabPath, Vector3 position, Vector3 rotation, Transform parentTransform, List<string> viewsToDisable = null)
    {

        GameObject panelInstance = Spawner.SpawnStatic(prefabPath, position, rotation);
        panelInstance.transform.SetParent(parentTransform);

        panelInstance.name = "InteractivePanel";

        if (viewsToDisable != null)
        {
            foreach (string viewName in viewsToDisable)
            {
                Transform viewTransform = FindDeepChild(panelInstance.transform, viewName);
                if (viewTransform != null)
                {
                    viewTransform.gameObject.SetActive(false);
                }
                else
                {
                    Debug.LogWarning($"[ExerciseBuilder] Could not find view to disable: {viewName}");
                }
            }
        }

        return panelInstance;
    }

    /// <summary>
    /// Adds a step to the execution list of its parent (StepRunner, StepGroup, ProcessStep, etc.).
    /// </summary>
    /// <param name="step">The step component to add.</param>
    public static void AddExecutionStep(StepBehaviour step)
    {
        Transform parentTransform = step.transform.parent;

        if (parentTransform != null)
        {
            // 1. Try adding to StepRunner
            var runner = parentTransform.GetComponent<StepRunner>();
            if (runner != null)
            {
                var executionSteps = GetPrivateField<List<StepBehaviour>>(runner, "executionSteps");
                if (executionSteps == null) 
                {
                    executionSteps = new List<StepBehaviour>();
                    SetPrivateField(runner, "executionSteps", executionSteps);
                }
                
                if (!executionSteps.Contains(step)) executionSteps.Add(step);
                return;
            }

            // 2. Try adding to parent StepGroup
            var parentGroup = parentTransform.GetComponent<StepGroup>();
            if (parentGroup != null)
            {
                 var groupSteps = GetPrivateField<List<StepBehaviour>>(parentGroup, "groupSteps");
                 if (groupSteps == null) { groupSteps = new List<StepBehaviour>(); SetPrivateField(parentGroup, "groupSteps", groupSteps); }
                 if (!groupSteps.Contains(step)) groupSteps.Add(step);
                 return;
            }
            
            // 3. Try adding to parent ProcessStep
            var parentProcess = parentTransform.GetComponent<ProcessStep>();
            if (parentProcess != null)
            {
                 var processSteps = GetPrivateField<List<StepBehaviour>>(parentProcess, "processSteps");
                 if (processSteps == null) { processSteps = new List<StepBehaviour>(); SetPrivateField(parentProcess, "processSteps", processSteps); }
                 if (!processSteps.Contains(step)) processSteps.Add(step);
                 return;
            }
            
            // 4. Try adding to parent MultipleProcessStep (only if step is ProcessStep)
            var parentMultiple = parentTransform.GetComponent<MultipleProcessStep>();
            if (parentMultiple != null && step is ProcessStep processStep)
            {
                if (!parentMultiple.Processes.Contains(processStep))
                {
                    parentMultiple.Processes.Add(processStep);
                }
                return;
            }
        }

        // 5. Fallback: Add to main StepRunner if no parent container found
        if (_stepRunner != null)
        {
             var executionSteps = GetPrivateField<List<StepBehaviour>>(_stepRunner, "executionSteps");
             if (executionSteps == null) 
             {
                 executionSteps = new List<StepBehaviour>();
                 SetPrivateField(_stepRunner, "executionSteps", executionSteps);
             }
             if (!executionSteps.Contains(step)) executionSteps.Add(step);
        }
    }

    /// <summary>
    /// Creates a logical group of steps that execute sequentially. Useful for organizing small actions under a Process Step.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="steps">Optional list of pre-created steps to execution order.</param>
    /// <param name="executionFilter">Filters when this group runs (Guided/Unguided).</param>
    /// <param name="handlers">Optional list of handlers to attach.</param>
    /// <returns>The created step group GameObject.</returns>
    public static GameObject AddGroupSteps(
        string stepId, 
        string stepName,
        Transform parentTransform,
        List<StepBehaviour> steps = null,
        ExecutionModeFilter executionFilter = ExecutionModeFilter.Guided | ExecutionModeFilter.Unguided,
        List<ExecutableHandlerBase> handlers = null)
    {
		GameObject exercise = GameObject.Find(title);

        GameObject groupStepObj = new GameObject($"{stepName}");
        
        if (parentTransform == exercise.transform)
        {
            groupStepObj.transform.SetParent(_stepRunner.transform);
        }
         else 
        {
            groupStepObj.transform.SetParent(parentTransform);
        }

        var stepGroupComponent = groupStepObj.AddComponent<StepGroup>();
        stepGroupComponent.Id = stepId;

        // Assign fields
        SetPrivateField(stepGroupComponent, "executionFilter", executionFilter);

        if (steps != null)
        {
            SetPrivateField(stepGroupComponent, "groupSteps", steps);
            
            for (int i = 0; i < steps.Count; i++)
            {
                AddExecutionStep(steps[i]);
            }
        }

        if (handlers != null)
        {
            SetPrivateField(stepGroupComponent, "handlers", handlers);
        }
        
        AddExecutionStep(stepGroupComponent);
        return groupStepObj;
    }

	/// <summary>
    /// Creates a new multiple step in the sequence. Subsequent AddObjective/AddInstruction calls apply to this step.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddMultipleProcessStep(string stepId, string stepName, Transform parentTransform)
    {
        GameObject exercise = GameObject.Find(title);

        GameObject multipleStepObj = new GameObject($"{stepName}");
        
        // Parent to the main process
        multipleStepObj.transform.SetParent(parentTransform);
        
        var multipleStepComponent = multipleStepObj.AddComponent<MultipleProcessStep>();
        multipleStepComponent.Id = stepId;

        AddExecutionStep(multipleStepComponent);
        
        return multipleStepObj;
    }

	/// <summary>
    /// Creates a high-level "Process" step. A process usually represents a distinct phase of the training (e.g., "Phase 1: Preparation"). It can contain child steps.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="description">Description string for internal documentation/display.</param>
    /// <param name="showInformationAtStart">Show info popup on start.</param>
    /// <param name="showResultsAtEnd">Show results popup on end.</param>
    /// <param name="resultsVisualization">How results are aggregated (Individual/Group).</param>
    /// <param name="steps">Optional list of child steps.</param>
    /// <returns>The created process step GameObject.</returns>
    public static GameObject AddProcessStep(
        string stepId, 
        string stepName,
        Transform parentTransform,
        string description,
        //GameObject multipleProcessStep = null,
        bool showInformationAtStart = true,
        bool showResultsAtEnd = true,
        ResultsVisualization resultsVisualization = ResultsVisualization.Individual,
        
        List<StepBehaviour> steps = null)
    {
        GameObject stepObj = new GameObject($"{stepName}");
        stepObj.SetActive(false);
                
        // if (multipleProcessStep != null)
        // {
        //     stepObj.transform.SetParent(multipleProcessStep.transform);
        // }
        // else
        // {
        //      GameObject exercise = GameObject.Find(ExerciseBuilder.title);
        //      if (exercise != null) stepObj.transform.SetParent(exercise.transform);
        // }
        
        stepObj.transform.SetParent(parentTransform);

        var stepComponent = stepObj.AddComponent<ProcessStep>();
        stepComponent.Id = stepId;

        // Assign fields
        SetPrivateField(stepComponent, "showInformationAtStart", showInformationAtStart);
        SetPrivateField(stepComponent, "showResultsAtEnd", showResultsAtEnd);
        SetPrivateField(stepComponent, "resultsVisualization", resultsVisualization);

        if (steps != null)
        {
            SetPrivateField(stepComponent, "processSteps", steps);
        }        else
        {
            SetPrivateField(stepComponent, "processSteps", new List<StepBehaviour>());
        }
        if (!string.IsNullOrEmpty(stepName) || !string.IsNullOrEmpty(description))
        {
             var processData = new ExecutionProcessData();
             if (stepName != null) processData.Title = stepName;
             if (description != null) processData.Description = description;
             
             var localizableData = GetPrivateField<LocalizableExecutionProcessData>(stepComponent, "processData");
             AddLocalizableItem(localizableData, "en-US", processData);
        }

        stepObj.SetActive(true);
        AddExecutionStep(stepComponent);

        Debug.Log($"[ExerciseBuilder] Created ProcessStep '{stepId}' with {stepComponent.Steps?.Count ?? 0} child steps");

        return stepObj;
    }

    /// <summary>
    /// Adds a generic wait step that halts execution until an external generic trigger is fired.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="executionFilter">Filters when this step runs (Guided/Unguided).</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddWaitForTriggerStep(string stepId, string stepName, Transform parentTransform, ExecutionModeFilter executionFilter = ExecutionModeFilter.Guided | ExecutionModeFilter.Unguided)
    {
        GameObject stepObj = CreateStepGameObject<WaitForTriggerStep>(stepName, parentTransform);
        var _waitForTriggerStepComponent = stepObj.AddComponent<WaitForTriggerStep>();

        _waitForTriggerStepComponent.Id = stepId;
        SetPrivateField(_waitForTriggerStepComponent, "executionFilter", executionFilter);
        AddExecutionStep(_waitForTriggerStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a menu step for the user to choose between Guided or Unguided execution mode.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddExecutionModeSelectionStep(string stepId, string stepName, Transform parentTransform)
    {
        GameObject stepObj = CreateStepGameObject<ExecutionModeSelectionStep>(stepName, parentTransform);
        var _executionModeSelectionStepComponent = stepObj.AddComponent<ExecutionModeSelectionStep>();
        _executionModeSelectionStepComponent.Id = stepId;
        AddExecutionStep(_executionModeSelectionStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a step that marks the end of the exercise.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddFinalStep(string stepId, string stepName, Transform parentTransform)
    {
        GameObject stepObj = CreateStepGameObject<FinalStep>(stepName, parentTransform);
        var _finalStepComponent = stepObj.AddComponent<FinalStep>();
        _finalStepComponent.Id = stepId;
        AddExecutionStep(_finalStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a step that displays an instruction panel to the user.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddInstructionsStep(string stepId, string stepName, Transform parentTransform)
    {
        GameObject stepObj = CreateStepGameObject<InstructionsStep>(stepName, parentTransform);
        var _instructionsStepComponent = stepObj.AddComponent<InstructionsStep>();
        _instructionsStepComponent.Id = stepId;
        AddExecutionStep(_instructionsStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a menu step for language selection.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddLanguageSelectionStep(string stepId, string stepName, Transform parentTransform)
    {
        GameObject stepObj = CreateStepGameObject<LanguageSelectionStep>(stepName, parentTransform);
        var _languageSelectionStepComponent = stepObj.AddComponent<LanguageSelectionStep>();
        _languageSelectionStepComponent.Id = stepId;
        AddExecutionStep(_languageSelectionStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a branching step that executes a different child step depending on whether the user is in VR or Desktop mode.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="desktopStep">Step to run if on PC/Desktop.</param>
    /// <param name="vrStep">Step to run if in VR.</param>
    /// <returns>The created step GameObject container.</returns>
    public static GameObject AddPlatformConditionalStep(string stepId, string stepName, Transform parentTransform, StepBehaviour desktopStep, StepBehaviour vrStep)
    {
        var stepObj = CreateStepGameObject<PlatformConditionalStep>(stepName, parentTransform);
        var _platformConditionalStepComponent = stepObj.AddComponent<PlatformConditionalStep>();
        _platformConditionalStepComponent.Id = stepId;
        SetPrivateField(_platformConditionalStepComponent, "desktopStep", desktopStep);
        SetPrivateField(_platformConditionalStepComponent, "vrStep", vrStep);
        AddExecutionStep(_platformConditionalStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a step that halts progress until the user teleports to the specified target.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="teleportTarget">The location (position/rotation) where the user must go.</param>
    /// <param name="executionFilter">Filters when this step runs (Guided/Unguided).</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddTeleportStep(string stepId, string stepName, Transform parentTransform, Transform teleportTarget, ExecutionModeFilter executionFilter = ExecutionModeFilter.Guided | ExecutionModeFilter.Unguided)
    {
        var stepObj = CreateStepGameObject<TeleportStep>(stepName, parentTransform);
        var _teleportStepComponent = stepObj.AddComponent<TeleportStep>();
        _teleportStepComponent.Id = stepId;
        SetPrivateField(_teleportStepComponent, "executionFilter", executionFilter);
        
        GameObject targetObj = teleportTarget != null ? teleportTarget.gameObject : new GameObject($"{stepName}_Target");
        var targetPoint = targetObj.GetOrAddComponent<InternalTeleportPoint>();        
        SetPrivateField(_teleportStepComponent, "teleportPoint", targetPoint);
        
        var handler = GetOrAddHandler<StepEvaluationHandler>(_teleportStepComponent);
        var descLoc = GetPrivateField<LocalizableText>(handler, "description");
        AddLocalizableItem(descLoc, "en-US", stepName);

        AddExecutionStep(_teleportStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a utility step to bulk enable XR interactions on lists of Interactables or Interactors.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="interactables">Optional list of objects to enable interaction for.</param>
    /// <param name="interactors">Optional list of hands/controllers to enable interaction for.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddEnableInteractionsStep(string stepId, string stepName, Transform parentTransform, List<XRBaseInteractable> interactables = null, List<XRBaseInteractor> interactors = null)
    {
        var stepObj = CreateStepGameObject<EnableInteractionsStep>(stepName, parentTransform);
        var _enableInteractionsStepComponent = stepObj.AddComponent<EnableInteractionsStep>();
        _enableInteractionsStepComponent.Id = stepId;
        SetPrivateField(_enableInteractionsStepComponent, "interactables", interactables ?? new List<XRBaseInteractable>());
        SetPrivateField(_enableInteractionsStepComponent, "interactors", interactors ?? new List<XRBaseInteractor>());
        AddExecutionStep(_enableInteractionsStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a utility step to bulk disable XR interactions on lists of Interactables or Interactors.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="interactables">List of objects to disable interaction for.</param>
    /// <param name="interactors">List of hands/controllers to disable interaction for.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddDisableInteractionsStep(string stepId, string stepName, Transform parentTransform, List<XRBaseInteractable> interactables, List<XRBaseInteractor> interactors)
    {
        var stepObj = CreateStepGameObject<DisableInteractionsStep>(stepName, parentTransform);
        var _disableInteractionsStepComponent = stepObj.AddComponent<DisableInteractionsStep>();
        _disableInteractionsStepComponent.Id = stepId;
        SetPrivateField(_disableInteractionsStepComponent, "interactables", interactables ?? new List<XRBaseInteractable>());
        SetPrivateField(_disableInteractionsStepComponent, "interactors", interactors ?? new List<XRBaseInteractor>());
        AddExecutionStep(_disableInteractionsStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a step that requires the user to grab an object and place it into a specific socket/snap zone.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="objectToPlace">The specific interactable object.</param>
    /// <param name="targetZone">The socket where it must be placed.</param>
    /// <param name="forceUngrab">If true, the object is released from hand upon placing.</param>
    /// <param name="executionFilter">Filters when this step runs (Guided/Unguided).</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddPlaceObjectStep(string stepId, string stepName, Transform parentTransform, VirooXRGrabInteractable objectToPlace, VirooXRSocketInteractor targetZone, bool forceUngrab = true, ExecutionModeFilter executionFilter = ExecutionModeFilter.Guided | ExecutionModeFilter.Unguided)
    {
        var stepObj = CreateStepGameObject<PlaceObjectStep>(stepName, parentTransform);
        var _placeObjectStepComponent = stepObj.AddComponent<PlaceObjectStep>();
        _placeObjectStepComponent.Id = stepId;
        SetPrivateField(_placeObjectStepComponent, "virooGrabInteractable", objectToPlace);
        SetPrivateField(_placeObjectStepComponent, "virooSocketInteractor", targetZone);
        SetPrivateField(_placeObjectStepComponent, "forceUngrab", forceUngrab);
        SetPrivateField(_placeObjectStepComponent, "executionFilter", executionFilter);

        var handler = GetOrAddHandler<StepEvaluationHandler>(_placeObjectStepComponent);
        var descLoc = GetPrivateField<LocalizableText>(handler, "description");
        AddLocalizableItem(descLoc, "en-US", stepName);

        AddExecutionStep(_placeObjectStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a step that updates the persistent help/info screen text without stopping execution flow.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="position">Position of the help screen.</param>
    /// <param name="title">New title text.</param>
    /// <param name="description">New description text.</param>
    /// <param name="updateTitle">Whether to update the title.</param>
    /// <param name="updateDescription">Whether to update the description.</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddUpdateHelpScreenStep(string stepId, string stepName, Transform parentTransform, Transform position, string title = null, string description = null, bool updateTitle = true, bool updateDescription = true)
    {
        var stepObj = CreateStepGameObject<UpdateHelpScreenStep>(stepName, parentTransform);
        var _updateHelpScreenStepComponent = stepObj.AddComponent<UpdateHelpScreenStep>();
        _updateHelpScreenStepComponent.Id = stepId;
        
        SetPrivateField(_updateHelpScreenStepComponent, "updateTitle", updateTitle);
        if (updateTitle && title != null)
        {
            var titleLoc = GetPrivateField<LocalizableText>(_updateHelpScreenStepComponent, "title");
            AddLocalizableItem(titleLoc, "en-US", title);
        }

        SetPrivateField(_updateHelpScreenStepComponent, "updateDescription", updateDescription);
        if (updateDescription && description != null)
        {
            var descLoc = GetPrivateField<LocalizableInstruction>(_updateHelpScreenStepComponent, "description");
            var instructionData = new InstructionData { Text = description };
            AddLocalizableItem(descLoc, "en-US", instructionData);
        }

        SetPrivateField(_updateHelpScreenStepComponent, "position", position);

        
        AddExecutionStep(_updateHelpScreenStepComponent);
        return stepObj;
    }

    /// <summary>
    /// Adds a step that waits until specific objects are interacted with (e.g., touched, grabbed, used).
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="interactableObjects">List of GameObjects to monitor.</param>
    /// <param name="completionMode">Wait for 'All' or 'Any' object interaction.</param>
    /// <param name="executionFilter">Filters when this step runs (Guided/Unguided).</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddWaitForObjectInteractionStep(string stepId, string stepName, Transform parentTransform, List<GameObject> interactableObjects, ObjectInteractionCompletionMode completionMode = ObjectInteractionCompletionMode.AllObjectsInteracted, ExecutionModeFilter executionFilter = ExecutionModeFilter.Guided | ExecutionModeFilter.Unguided)
    {
        var stepObj = CreateStepGameObject<WaitForObjectInteractionStep>(stepName, parentTransform);
        var _waitForObjectInteractionStepComponent = stepObj.AddComponent<WaitForObjectInteractionStep>();
        _waitForObjectInteractionStepComponent.Id = stepId;

        var interactables = interactableObjects.Select(go => GetOrAddComponent<InteractableObject>(go)).ToList();

        SetPrivateField(_waitForObjectInteractionStepComponent, "interactableObjects", interactables ?? new List<InteractableObject>());
        SetPrivateField(_waitForObjectInteractionStepComponent, "completionMode", completionMode);
        SetPrivateField(_waitForObjectInteractionStepComponent, "executionFilter", executionFilter);

        var handler = GetOrAddHandler<StepEvaluationHandler>(_waitForObjectInteractionStepComponent);
        var descLoc = GetPrivateField<LocalizableText>(handler, "description");
        AddLocalizableItem(descLoc, "en-US", stepName);

        AddExecutionStep(_waitForObjectInteractionStepComponent);
        
        Debug.Log($"[ExerciseBuilder] WaitForObjectInteractionStep '{stepId}' has {_waitForObjectInteractionStepComponent.Handlers.Count} handlers");
        
        return stepObj;
    }

    /// <summary>
    /// Adds a step that waits until the required number of players enter a specific trigger area.
    /// </summary>
    /// <param name="stepId">Semantic ID for the step.</param>
    /// <param name="stepName">Name of the GameObject.</param>
    /// <param name="parentTransform">Parent step or Exercise Root.</param>
    /// <param name="detectionArea">The component defining the zone.</param>
    /// <param name="executionFilter">Filters when this step runs (Guided/Unguided).</param>
    /// <returns>The created step GameObject.</returns>
    public static GameObject AddWaitForPlayersInAreaStep(string stepId, string stepName, Transform parentTransform, PlayerDetectionArea detectionArea, ExecutionModeFilter executionFilter = ExecutionModeFilter.Guided | ExecutionModeFilter.Unguided)
    {
        var stepObj = CreateStepGameObject<WaitForPlayersInAreaStep>(stepName, parentTransform);
        var _waitForPlayersInAreaStepComponent = stepObj.AddComponent<WaitForPlayersInAreaStep>();
        _waitForPlayersInAreaStepComponent.Id = stepId;
        SetPrivateField(_waitForPlayersInAreaStepComponent, "detectionArea", detectionArea);
        SetPrivateField(_waitForPlayersInAreaStepComponent, "executionFilter", executionFilter);

        var handler = GetOrAddHandler<StepEvaluationHandler>(_waitForPlayersInAreaStepComponent);
        var descLoc = GetPrivateField<LocalizableText>(handler, "description");
        AddLocalizableItem(descLoc, "en-US", stepName);

        AddExecutionStep(_waitForPlayersInAreaStepComponent);
        return stepObj;
    }

    private static GameObject CreateStepGameObject<T>(string stepName, Transform parentTransform) where T : StepBehaviour
    {
        GameObject stepObj = new GameObject($"{stepName}");
        
        if (parentTransform != null)
        {
            stepObj.transform.SetParent(parentTransform);
        }
        else
        {
             GameObject exercise = GameObject.Find(title);
             if (exercise != null) stepObj.transform.SetParent(exercise.transform);
        }
        
        return stepObj;
    }

    // =================================================================================================
    // REFLECTION HELPERS
    // =================================================================================================

    private static T GetOrAddComponent<T>(GameObject obj) where T : Component
    {
        if (obj == null) return null;
        var comp = obj.GetComponent<T>();
        if (comp == null) comp = obj.AddComponent<T>();
        return comp;
    }

    private static T GetOrAddHandler<T>(StepBehaviour step) where T : ExecutableHandlerBase
    {
        // Use the public Handlers property directly
        var handlersList = step.Handlers;
        if (handlersList == null)
        {
            // If Handlers property returns null, try setting via reflection
            handlersList = new List<ExecutableHandlerBase>();
            SetPrivateField(step, "handlers", handlersList);
        }

        var handler = handlersList.OfType<T>().FirstOrDefault();
        if (handler == null)
        {
            // Create new handler component on the same GameObject
            handler = step.gameObject.AddComponent<T>();
            handlersList.Add(handler);
            Debug.Log($"[ExerciseBuilder] Added {typeof(T).Name} to {step.Id}, Handlers count: {handlersList.Count}");
        }
        return handler;
    }

    private static void AddLocalizableItem<T>(object localizable, string locale, T value) where T : class
    {
        if (localizable == null) return;

        // Get the 'items' field from the base class LocalizableValueOfT<T>
        var baseType = localizable.GetType();
        while (baseType != null && (!baseType.IsGenericType || baseType.GetGenericTypeDefinition() != typeof(LocalizableValueOfT<>)))
        {
            baseType = baseType.BaseType;
        }

        if (baseType != null)
        {
            var itemsField = baseType.GetField("items", BindingFlags.NonPublic | BindingFlags.Instance);
            if (itemsField != null)
            {
                var list = itemsField.GetValue(localizable) as System.Collections.IList;
                if (list != null)
                {
                    // Create LocalizableItem instance using the list generic argument
                    var listType = list.GetType();
                    if (listType.IsGenericType)
                    {
                        var itemType = listType.GetGenericArguments()[0];
                        if (itemType != null)
                        {
                            var item = Activator.CreateInstance(itemType, locale, value);
                            list.Add(item);
                        }
                    }
                }
            }
        }
    }

    private static void SetPrivateField(object target, string fieldName, object value)
    {
        var field = target.GetType().GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Public);
        if (field != null)
        {
            field.SetValue(target, value);
        }
        else
        {
            Debug.LogWarning($"[ExerciseBuilder] Field '{fieldName}' not found on {target.GetType().Name}");
        }
    }

    private static T GetPrivateField<T>(object target, string fieldName) where T : class
    {
        var field = target.GetType().GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Public);
        if (field != null)
        {
            return field.GetValue(target) as T;
        }
        return null;
    }

    private static Transform FindDeepChild(Transform parent, string name)
    {
        Transform result = parent.Find(name);
        if (result != null) return result;

        foreach (Transform child in parent)
        {
            result = FindDeepChild(child, name);
            if (result != null) return result;
        }
        return null;
    }
}
