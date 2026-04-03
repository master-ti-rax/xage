# Module 4 Create Plan

*Source JSON:* `artifacts/planner/2026-03-21T09:50:20.027991/module_4_create_plan.json`

## kind

"planner_create_plan"

## orchestrator module

```json
{
  "module_id": "4",
  "description": {
    "module_id": 4,
    "module_title": "Supervised Risk-Based Inspection Scenarios (75 minutes)",
    "module_description": "This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.",
    "learning_outcomes": [
      "select inspection sequences based on observed battery risk conditions;",
      "validate robot-generated inspection results under partial guidance;",
      "route batteries to the correct physical handling containers;",
      "choose and communicate appropriate post-inspection handling actions;",
      "explain the safety and operational consequences of incorrect decisions."
    ],
    "module_data": {
      "module_id": 4,
      "title": "Supervised Risk-Based Inspection Scenarios (75 minutes)",
      "duration_minutes": 75,
      "pedagogical_rationale": "This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.",
      "learning_outcomes": [
        "select inspection sequences based on observed battery risk conditions;",
        "validate robot-generated inspection results under partial guidance;",
        "route batteries to the correct physical handling containers;",
        "choose and communicate appropriate post-inspection handling actions;",
        "explain the safety and operational consequences of incorrect decisions."
      ],
      "learning_flow": {
        "description": "Implementation flow extracted from module body.",
        "steps": [
          {
            "step_id": "1",
            "step_number": 1,
            "title": "Case 1 – Intact Battery (Guided). A visually intact battery is placed inside the robot cell. The console",
            "description": "highlights the recommended inspection sequence and the approval handling option. The learner selects the highlighted inspection mode, supervises the robot, reviews the results, and confirms approval. The system then highlights the green approval bin. The learner must physically route the battery to this container. A feedback panel explains why this handling path is safe and compliant."
          },
          {
            "step_id": "2",
            "step_number": 2,
            "title": "Case 2 – Deformed Battery (Partially Guided). A battery with visible deformation is placed inside",
            "description": "the robot cell. Two inspection sequences are shown without highlighting. The learner chooses one, supervises execution, and validates the robot’s result. A timer appears on the console. The system highlights the yellow re-routing crate. The learner must physically move the battery to this container. A comparison panel explains the optimal choice and the potential risks of incorrect routing."
          },
          {
            "step_id": "3",
            "step_number": 3,
            "title": "Case 3 – Leaking Battery (Critical Condition). A battery with visible leakage is placed inside the robot",
            "description": "cell. A warning symbol and low-volume alarm are activated. The learner must select the emergency inspection mode, supervise the robot, and choose isolation as the handling decision. The system highlights the red isolation container. The learner must route the battery to the isolation container. If the wrong decision is made, a consequence panel explains the real-world impact."
          },
          {
            "step_id": "4",
            "step_number": 4,
            "title": "Micro-Reflection. A short panel asks: “Which routing decision most reduced the risk in the previous",
            "description": "case?” The learner selects an answer before continuing."
          },
          {
            "step_id": "5",
            "step_number": 5,
            "title": "Progressive Challenge",
            "description": "A random case (intact, deformed, or leaking) is presented without hints. The learner completes the full workflow independently while background factory noise and a countdown timer are active. The learner must select the inspection sequence, validate the result, and route the battery to the correct container. This step prepares the learner for autonomous operation."
          }
        ]
      },
      "learner_monitoring": [
        "The system records into a log file: case selection accuracy, routing correctness,",
        "response time, number of hints used, and critical risk errors."
      ]
    },
    "plan_summary": {
      "plan_title": "Robot-Assisted Inspection of Wasted Automotive Batteries",
      "training_domain": "XR vocational training",
      "high_level_goal": "Understand the main safety, environmental, and operational risks associated with robot-assisted inspection of wasted automotive batteries.",
      "module_sequence": [
        {
          "module_id": "1",
          "title": "Introduction and Basic Environment Understanding (25 minutes)",
          "focus": "This module serves as a low-pressure onboarding phase that allows learners to become familiar with the XR environment, basic controls, and spatial layout before engaging in safety-"
        },
        {
          "module_id": "2",
          "title": "Safety Boundaries Understanding (50 minutes)",
          "focus": "This module trains learners to behave safely when a robot is operating in a shared workspace. Unlike Module 1, which introduced static areas and basic robot motion, this module foc"
        },
        {
          "module_id": "3",
          "title": "Human Decisions and Robotic Actions Coordination (60 minutes)",
          "focus": "This module introduces the complete human–robot inspection cycle and trains learners to coordinate their decisions with robotic execution. Unlike previous modules, this phase expli"
        },
        {
          "module_id": "4",
          "title": "Supervised Risk-Based Inspection Scenarios (75 minutes)",
          "focus": "This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate "
        },
        {
          "module_id": "5",
          "title": "Autonomous Risk-Based Decision-Making (60 minutes)",
          "focus": "This module simulates realistic industrial operating conditions in which learners must act independently while respecting production throughput constraints. In addition to safety a"
        },
        {
          "module_id": "6",
          "title": "Assessment, Reflection, and Readiness Validation (30 minutes)",
          "focus": "This module consolidates learning by transforming performance data into reflective awareness. Learners are evaluated on their ability to act safely, make risk-informed decisions, a"
        }
      ],
      "global_constraints": [
        "Preserve module order from educational plan.",
        "Implement one module at a time with validation loop."
      ],
      "asset_themes": [
        "3D models",
        "process console",
        "safety interactions"
      ],
      "agent_context": "This summary is deterministic fallback output because LLM summarization was unavailable."
    }
  }
}
```

## module description

```
{
  "module_id": 4,
  "module_title": "Supervised Risk-Based Inspection Scenarios (75 minutes)",
  "module_description": "This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.",
  "learning_outcomes": [
    "select inspection sequences based on observed battery risk conditions;",
    "validate robot-generated inspection results under partial guidance;",
    "route batteries to the correct physical handling containers;",
    "choose and communicate appropriate post-inspection handling actions;",
    "explain the safety and operational consequences of incorrect decisions."
  ],
  "module_data": {
    "module_id": 4,
    "title": "Supervised Risk-Based Inspection Scenarios (75 minutes)",
    "duration_minutes": 75,
    "pedagogical_rationale": "This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.",
    "learning_outcomes": [
      "select inspection sequences based on observed battery risk conditions;",
      "validate robot-generated inspection results under partial guidance;",
      "route batteries to the correct physical handling containers;",
      "choose and communicate appropriate post-inspection handling actions;",
      "explain the safety and operational consequences of incorrect decisions."
    ],
    "learning_flow": {
      "description": "Implementation flow extracted from module body.",
      "steps": [
        {
          "step_id": "1",
          "step_number": 1,
          "title": "Case 1 \u2013 Intact Battery (Guided). A visually intact battery is placed inside the robot cell. The console",
          "description": "highlights the recommended inspection sequence and the approval handling option. The learner selects the highlighted inspection mode, supervises the robot, reviews the results, and confirms approval. The system then highlights the green approval bin. The learner must physically route the battery to this container. A feedback panel explains why this handling path is safe and compliant."
        },
        {
          "step_id": "2",
          "step_number": 2,
          "title": "Case 2 \u2013 Deformed Battery (Partially Guided). A battery with visible deformation is placed inside",
          "description": "the robot cell. Two inspection sequences are shown without highlighting. The learner chooses one, supervises execution, and validates the robot\u2019s result. A timer appears on the console. The system highlights the yellow re-routing crate. The learner must physically move the battery to this container. A comparison panel explains the optimal choice and the potential risks of incorrect routing."
        },
        {
          "step_id": "3",
          "step_number": 3,
          "title": "Case 3 \u2013 Leaking Battery (Critical Condition). A battery with visible leakage is placed inside the robot",
          "description": "cell. A warning symbol and low-volume alarm are activated. The learner must select the emergency inspection mode, supervise the robot, and choose isolation as the handling decision. The system highlights the red isolation container. The learner must route the battery to the isolation container. If the wrong decision is made, a consequence panel explains the real-world impact."
        },
        {
          "step_id": "4",
          "step_number": 4,
          "title": "Micro-Reflection. A short panel asks: \u201cWhich routing decision most reduced the risk in the previous",
          "description": "case?\u201d The learner selects an answer before continuing."
        },
        {
          "step_id": "5",
          "step_number": 5,
          "title": "Progressive Challenge",
          "description": "A random case (intact, deformed, or leaking) is presented without hints. The learner completes the full workflow independently while background factory noise and a countdown timer are active. The learner must select the inspection sequence, validate the result, and route the battery to the correct container. This step prepares the learner for autonomous operation."
        }
      ]
    },
    "learner_monitoring": [
      "The system records into a log file: case selection accuracy, routing correctness,",
      "response time, number of hints used, and critical risk errors."
    ]
  },
  "plan_summary": {
    "plan_title": "Robot-Assisted Inspection of Wasted Automotive Batteries",
    "training_domain": "XR vocational training",
    "high_level_goal": "Understand the main safety, environmental, and operational risks associated with robot-assisted inspection of wasted automotive batteries.",
    "module_sequence": [
      {
        "module_id": "1",
        "title": "Introduction and Basic Environment Understanding (25 minutes)",
        "focus": "This module serves as a low-pressure onboarding phase that allows learners to become familiar with the XR environment, basic controls, and spatial layout before engaging in safety-"
      },
      {
        "module_id": "2",
        "title": "Safety Boundaries Understanding (50 minutes)",
        "focus": "This module trains learners to behave safely when a robot is operating in a shared workspace. Unlike Module 1, which introduced static areas and basic robot motion, this module foc"
      },
      {
        "module_id": "3",
        "title": "Human Decisions and Robotic Actions Coordination (60 minutes)",
        "focus": "This module introduces the complete human\u2013robot inspection cycle and trains learners to coordinate their decisions with robotic execution. Unlike previous modules, this phase expli"
      },
      {
        "module_id": "4",
        "title": "Supervised Risk-Based Inspection Scenarios (75 minutes)",
        "focus": "This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate "
      },
      {
        "module_id": "5",
        "title": "Autonomous Risk-Based Decision-Making (60 minutes)",
        "focus": "This module simulates realistic industrial operating conditions in which learners must act independently while respecting production throughput constraints. In addition to safety a"
      },
      {
        "module_id": "6",
        "title": "Assessment, Reflection, and Readiness Validation (30 minutes)",
        "focus": "This module consolidates learning by transforming performance data into reflective awareness. Learners are evaluated on their ability to act safely, make risk-informed decisions, a"
      }
    ],
    "global_constraints": [
      "Preserve module order from educational plan.",
      "Implement one module at a time with validation loop."
    ],
    "asset_themes": [
      "3D models",
      "process console",
      "safety interactions"
    ],
    "agent_context": "This summary is deterministic fallback output because LLM summarization was unavailable."
  }
}
```

## running context

null

## planner environment

```json
{
  "unity_version": "2022.3",
  "xr_framework": "XR Interaction Toolkit (XRIT)"
}
```

## duties

```json
{
  "duty1_define_scene_hierarchy": {
    "inputs": {
      "module_brief": "{\n  \"module_id\": 4,\n  \"module_title\": \"Supervised Risk-Based Inspection Scenarios (75 minutes)\",\n  \"module_description\": \"This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.\",\n  \"learning_outcomes\": [\n    \"select inspection sequences based on observed battery risk conditions;\",\n    \"validate robot-generated inspection results under partial guidance;\",\n    \"route batteries to the correct physical handling containers;\",\n    \"choose and communicate appropriate post-inspection handling actions;\",\n    \"explain the safety and operational consequences of incorrect decisions.\"\n  ],\n  \"module_data\": {\n    \"module_id\": 4,\n    \"title\": \"Supervised Risk-Based Inspection Scenarios (75 minutes)\",\n    \"duration_minutes\": 75,\n    \"pedagogical_rationale\": \"This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.\",\n    \"learning_outcomes\": [\n      \"select inspection sequences based on observed battery risk conditions;\",\n      \"validate robot-generated inspection results under partial guidance;\",\n      \"route batteries to the correct physical handling containers;\",\n      \"choose and communicate appropriate post-inspection handling actions;\",\n      \"explain the safety and operational consequences of incorrect decisions.\"\n    ],\n    \"learning_flow\": {\n      \"description\": \"Implementation flow extracted from module body.\",\n      \"steps\": [\n        {\n          \"step_id\": \"1\",\n          \"step_number\": 1,\n          \"title\": \"Case 1 \\u2013 Intact Battery (Guided). A visually intact battery is placed inside the robot cell. The console\",\n          \"description\": \"highlights the recommended inspection sequence and the approval handling option. The learner selects the highlighted inspection mode, supervises the robot, reviews the results, and confirms approval. The system then highlights the green approval bin. The learner must physically route the battery to this container. A feedback panel explains why this handling path is safe and compliant.\"\n        },\n        {\n          \"step_id\": \"2\",\n          \"step_number\": 2,\n          \"title\": \"Case 2 \\u2013 Deformed Battery (Partially Guided). A battery with visible deformation is placed inside\",\n          \"description\": \"the robot cell. Two inspection sequences are shown without highlighting. The learner chooses one, supervises execution, and validates the robot\\u2019s result. A timer appears on the console. The system highlights the yellow re-routing crate. The learner must physically move the battery to this container. A comparison panel explains the optimal choice and the potential risks of incorrect routing.\"\n        },\n        {\n          \"step_id\": \"3\",\n          \"step_number\": 3,\n          \"title\": \"Case 3 \\u2013 Leaking Battery (Critical Condition). A battery with visible leakage is placed inside the robot\",\n          \"description\": \"cell. A warning symbol and low-volume alarm are activated. The learner must select the emergency inspection mode, supervise the robot, and choose isolation as the handling decision. The system highlights the red isolation container. The learner must route the battery to the isolation container. If the wrong decision is made, a consequence panel explains the real-world impact.\"\n        },\n        {\n          \"step_id\": \"4\",\n          \"step_number\": 4,\n          \"title\": \"Micro-Reflection. A short panel asks: \\u201cWhich routing decision most reduced the risk in the previous\",\n          \"description\": \"case?\\u201d The learner selects an answer before continuing.\"\n        },\n        {\n          \"step_id\": \"5\",\n          \"step_number\": 5,\n          \"title\": \"Progressive Challenge\",\n          \"description\": \"A random case (intact, deformed, or leaking) is presented without hints. The learner completes the full workflow independently while background factory noise and a countdown timer are active. The learner must select the inspection sequence, validate the result, and route the battery to the correct container. This step prepares the learner for autonomous operation.\"\n        }\n      ]\n    },\n    \"learner_monitoring\": [\n      \"The system records into a log file: case selection accuracy, routing correctness,\",\n      \"response time, number of hints used, and critical risk errors.\"\n    ]\n  },\n  \"plan_summary\": {\n    \"plan_title\": \"Robot-Assisted Inspection of Wasted Automotive Batteries\",\n    \"training_domain\": \"XR vocational training\",\n    \"high_level_goal\": \"Understand the main safety, environmental, and operational risks associated with robot-assisted inspection of wasted automotive batteries.\",\n    \"module_sequence\": [\n      {\n        \"module_id\": \"1\",\n        \"title\": \"Introduction and Basic Environment Understanding (25 minutes)\",\n        \"focus\": \"This module serves as a low-pressure onboarding phase that allows learners to become familiar with the XR environment, basic controls, and spatial layout before engaging in safety-\"\n      },\n      {\n        \"module_id\": \"2\",\n        \"title\": \"Safety Boundaries Understanding (50 minutes)\",\n        \"focus\": \"This module trains learners to behave safely when a robot is operating in a shared workspace. Unlike Module 1, which introduced static areas and basic robot motion, this module foc\"\n      },\n      {\n        \"module_id\": \"3\",\n        \"title\": \"Human Decisions and Robotic Actions Coordination (60 minutes)\",\n        \"focus\": \"This module introduces the complete human\\u2013robot inspection cycle and trains learners to coordinate their decisions with robotic execution. Unlike previous modules, this phase expli\"\n      },\n      {\n        \"module_id\": \"4\",\n        \"title\": \"Supervised Risk-Based Inspection Scenarios (75 minutes)\",\n        \"focus\": \"This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate \"\n      },\n      {\n        \"module_id\": \"5\",\n        \"title\": \"Autonomous Risk-Based Decision-Making (60 minutes)\",\n        \"focus\": \"This module simulates realistic industrial operating conditions in which learners must act independently while respecting production throughput constraints. In addition to safety a\"\n      },\n      {\n        \"module_id\": \"6\",\n        \"title\": \"Assessment, Reflection, and Readiness Validation (30 minutes)\",\n        \"focus\": \"This module consolidates learning by transforming performance data into reflective awareness. Learners are evaluated on their ability to act safely, make risk-informed decisions, a\"\n      }\n    ],\n    \"global_constraints\": [\n      \"Preserve module order from educational plan.\",\n      \"Implement one module at a time with validation loop.\"\n    ],\n    \"asset_themes\": [\n      \"3D models\",\n      \"process console\",\n      \"safety interactions\"\n    ],\n    \"agent_context\": \"This summary is deterministic fallback output because LLM summarization was unavailable.\"\n  }\n}",
      "running_context": null
    },
    "raw_llm_response": "{\n  \"scene_root\": \"Root\",\n  \"hierarchy\": [\n    {\n      \"name\": \"Exercise\",\n      \"purpose\": \"Main exercise container\",\n      \"children\": [\n        {\n          \"name\": \"Environment\",\n          \"purpose\": \"Physical environment setup\",\n          \"children\": [\n            {\n              \"name\": \"RobotCell\",\n              \"purpose\": \"Contains the robotic inspection area\",\n              \"prefab_hint\": \"robot_workcell\",\n              \"components\": [\"MeshRenderer\", \"BoxCollider\"]\n            },\n            {\n              \"name\": \"SafetyZones\",\n              \"purpose\": \"Defines restricted areas for safety\",\n              \"children\": [\n                {\n                  \"name\": \"RedZone\",\n                  \"purpose\": \"High-risk interaction zone\",\n                  \"prefab_hint\": \"safety_zone_red\"\n                },\n                {\n                  \"name\": \"YellowZone\",\n                  \"purpose\": \"Cautionary interaction zone\",\n                  \"prefab_hint\": \"safety_zone_yellow\"\n                }\n              ]\n            },\n            {\n              \"name\": \"Floor\",\n              \"purpose\": \"Base surface for the environment\",\n              \"components\": [\"MeshRenderer\", \"MeshFilter\"]\n            }\n          ]\n        },\n        {\n          \"name\": \"InteractableObjects\",\n          \"purpose\": \"Objects learners can interact with\",\n          \"children\": [\n            {\n              \"name\": \"Batteries\",\n              \"purpose\": \"Different battery states for inspection\",\n              \"children\": [\n                {\n                  \"name\": \"IntactBattery\",\n                  \"purpose\": \"Visually intact battery for inspection\",\n                  \"prefab_hint\": \"battery_intact\",\n                  \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRGrabInteractable\"]\n                },\n                {\n                  \"name\": \"DeformedBattery\",\n                  \"purpose\": \"Visibly deformed battery for inspection\",\n                  \"prefab_hint\": \"battery_deformed\",\n                  \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRGrabInteractable\"]\n                },\n                {\n                  \"name\": \"LeakingBattery\",\n                  \"purpose\": \"Battery with visible leakage\",\n                  \"prefab_hint\": \"battery_leaking\",\n                  \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRGrabInteractable\"]\n                }\n              ]\n            },\n            {\n              \"name\": \"HandlingContainers\",\n              \"purpose\": \"Containers for routing batteries\",\n              \"children\": [\n                {\n                  \"name\": \"ApprovalBin\",\n                  \"purpose\": \"Green container for approved batteries\",\n                  \"prefab_hint\": \"container_green\",\n                  \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRGrabInteractable\"]\n                },\n                {\n                  \"name\": \"ReRoutingCrate\",\n                  \"purpose\": \"Yellow container for re-routing batteries\",\n                  \"prefab_hint\": \"container_yellow\",\n                  \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRGrabInteractable\"]\n                },\n                {\n                  \"name\": \"IsolationContainer\",\n                  \"purpose\": \"Red container for isolating critical batteries\",\n                  \"prefab_hint\": \"container_red\",\n                  \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRGrabInteractable\"]\n                }\n              ]\n            },\n            {\n              \"name\": \"InspectionConsole\",\n              \"purpose\": \"Console for interacting with inspection data\",\n              \"prefab_hint\": \"control_console\",\n              \"components\": [\"MeshRenderer\", \"BoxCollider\", \"XRInteractiveComponent\"]\n            }\n          ]\n        },\n        {\n          \"name\": \"UI\",\n          \"purpose\": \"User interface elements\",\n          \"children\": [\n            {\n              \"name\": \"ConsoleDisplay\",\n              \"purpose\": \"Shows inspection results and guidance\",\n              \"prefab_hint\": \"screen_display\"\n            },\n            {\n              \"name\": \"FeedbackPanel\",\n              \"purpose\": \"Provides feedback on learner decisions\",\n              \"prefab_hint\": \"info_panel\"\n            },\n            {\n              \"name\": \"ConsequencePanel\",\n              \"purpose\": \"Shows consequences of incorrect decisions\",\n              \"prefab_hint\": \"warning_panel\"\n            },\n            {\n              \"name\": \"Timer\",\n              \"purpose\": \"Displays time constraints for tasks\",\n              \"prefab_hint\": \"digital_timer\"\n            },\n            {\n              \"name\": \"ComparisonPanel\",\n              \"purpose\": \"Shows optimal vs actual choices comparison\",\n              \"prefab_hint\": \"comparison_screen\"\n            }\n          ]\n        },\n        {\n          \"name\": \"StepContainer\",\n          \"purpose\": \"Parent for all training step GameObjects\"\n        }\n      ]\n    }\n  ]\n}",
    "parsed": {
      "scene_root": "Root",
      "hierarchy": [
        {
          "name": "Exercise",
          "purpose": "Main exercise container",
          "children": [
            {
              "name": "Environment",
              "purpose": "Physical environment setup",
              "children": [
                {
                  "name": "RobotCell",
                  "purpose": "Contains the robotic inspection area",
                  "prefab_hint": "robot_workcell",
                  "components": [
                    "MeshRenderer",
                    "BoxCollider"
                  ]
                },
                {
                  "name": "SafetyZones",
                  "purpose": "Defines restricted areas for safety",
                  "children": [
                    {
                      "name": "RedZone",
                      "purpose": "High-risk interaction zone",
                      "prefab_hint": "safety_zone_red"
                    },
                    {
                      "name": "YellowZone",
                      "purpose": "Cautionary interaction zone",
                      "prefab_hint": "safety_zone_yellow"
                    }
                  ]
                },
                {
                  "name": "Floor",
                  "purpose": "Base surface for the environment",
                  "components": [
                    "MeshRenderer",
                    "MeshFilter"
                  ]
                }
              ]
            },
            {
              "name": "InteractableObjects",
              "purpose": "Objects learners can interact with",
              "children": [
                {
                  "name": "Batteries",
                  "purpose": "Different battery states for inspection",
                  "children": [
                    {
                      "name": "IntactBattery",
                      "purpose": "Visually intact battery for inspection",
                      "prefab_hint": "battery_intact",
                      "components": [
                        "MeshRenderer",
                        "BoxCollider",
                        "XRGrabInteractable"
                      ]
                    },
                    {
                      "name": "DeformedBattery",
                      "purpose": "Visibly deformed battery for inspection",
                      "prefab_hint": "battery_deformed",
                      "components": [
                        "MeshRenderer",
                        "BoxCollider",
                        "XRGrabInteractable"
                      ]
                    },
                    {
                      "name": "LeakingBattery",
                      "purpose": "Battery with visible leakage",
                      "prefab_hint": "battery_leaking",
                      "components": [
                        "MeshRenderer",
                        "BoxCollider",
                        "XRGrabInteractable"
                      ]
                    }
                  ]
                },
                {
                  "name": "HandlingContainers",
                  "purpose": "Containers for routing batteries",
                  "children": [
                    {
                      "name": "ApprovalBin",
                      "purpose": "Green container for approved batteries",
                      "prefab_hint": "container_green",
                      "components": [
                        "MeshRenderer",
                        "BoxCollider",
                        "XRGrabInteractable"
                      ]
                    },
                    {
                      "name": "ReRoutingCrate",
                      "purpose": "Yellow container for re-routing batteries",
                      "prefab_hint": "container_yellow",
                      "components": [
                        "MeshRenderer",
                        "BoxCollider",
                        "XRGrabInteractable"
                      ]
                    },
                    {
                      "name": "IsolationContainer",
                      "purpose": "Red container for isolating critical batteries",
                      "prefab_hint": "container_red",
                      "components": [
                        "MeshRenderer",
                        "BoxCollider",
                        "XRGrabInteractable"
                      ]
                    }
                  ]
                },
                {
                  "name": "InspectionConsole",
                  "purpose": "Console for interacting with inspection data",
                  "prefab_hint": "control_console",
                  "components": [
                    "MeshRenderer",
                    "BoxCollider",
                    "XRInteractiveComponent"
                  ]
                }
              ]
            },
            {
              "name": "UI",
              "purpose": "User interface elements",
              "children": [
                {
                  "name": "ConsoleDisplay",
                  "purpose": "Shows inspection results and guidance",
                  "prefab_hint": "screen_display"
                },
                {
                  "name": "FeedbackPanel",
                  "purpose": "Provides feedback on learner decisions",
                  "prefab_hint": "info_panel"
                },
                {
                  "name": "ConsequencePanel",
                  "purpose": "Shows consequences of incorrect decisions",
                  "prefab_hint": "warning_panel"
                },
                {
                  "name": "Timer",
                  "purpose": "Displays time constraints for tasks",
                  "prefab_hint": "digital_timer"
                },
                {
                  "name": "ComparisonPanel",
                  "purpose": "Shows optimal vs actual choices comparison",
                  "prefab_hint": "comparison_screen"
                }
              ]
            },
            {
              "name": "StepContainer",
              "purpose": "Parent for all training step GameObjects"
            }
          ]
        }
      ]
    },
    "fallback_used": false
  },
  "duty2_decompose_steps": {
    "inputs": {
      "module_brief": "{\n  \"module_id\": 4,\n  \"module_title\": \"Supervised Risk-Based Inspection Scenarios (75 minutes)\",\n  \"module_description\": \"This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.\",\n  \"learning_outcomes\": [\n    \"select inspection sequences based on observed battery risk conditions;\",\n    \"validate robot-generated inspection results under partial guidance;\",\n    \"route batteries to the correct physical handling containers;\",\n    \"choose and communicate appropriate post-inspection handling actions;\",\n    \"explain the safety and operational consequences of incorrect decisions.\"\n  ],\n  \"module_data\": {\n    \"module_id\": 4,\n    \"title\": \"Supervised Risk-Based Inspection Scenarios (75 minutes)\",\n    \"duration_minutes\": 75,\n    \"pedagogical_rationale\": \"This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate inspection outcomes, but also physically route batteries into the correct treatment path. Although system guidance is still available, learners must increasingly interpret inspection evidence, manage uncertainty, and understand the safety and operational consequences of their choices. Small stressors, time constraints, and consequence visualizations are introduced to reflect realistic conditions.\",\n    \"learning_outcomes\": [\n      \"select inspection sequences based on observed battery risk conditions;\",\n      \"validate robot-generated inspection results under partial guidance;\",\n      \"route batteries to the correct physical handling containers;\",\n      \"choose and communicate appropriate post-inspection handling actions;\",\n      \"explain the safety and operational consequences of incorrect decisions.\"\n    ],\n    \"learning_flow\": {\n      \"description\": \"Implementation flow extracted from module body.\",\n      \"steps\": [\n        {\n          \"step_id\": \"1\",\n          \"step_number\": 1,\n          \"title\": \"Case 1 \\u2013 Intact Battery (Guided). A visually intact battery is placed inside the robot cell. The console\",\n          \"description\": \"highlights the recommended inspection sequence and the approval handling option. The learner selects the highlighted inspection mode, supervises the robot, reviews the results, and confirms approval. The system then highlights the green approval bin. The learner must physically route the battery to this container. A feedback panel explains why this handling path is safe and compliant.\"\n        },\n        {\n          \"step_id\": \"2\",\n          \"step_number\": 2,\n          \"title\": \"Case 2 \\u2013 Deformed Battery (Partially Guided). A battery with visible deformation is placed inside\",\n          \"description\": \"the robot cell. Two inspection sequences are shown without highlighting. The learner chooses one, supervises execution, and validates the robot\\u2019s result. A timer appears on the console. The system highlights the yellow re-routing crate. The learner must physically move the battery to this container. A comparison panel explains the optimal choice and the potential risks of incorrect routing.\"\n        },\n        {\n          \"step_id\": \"3\",\n          \"step_number\": 3,\n          \"title\": \"Case 3 \\u2013 Leaking Battery (Critical Condition). A battery with visible leakage is placed inside the robot\",\n          \"description\": \"cell. A warning symbol and low-volume alarm are activated. The learner must select the emergency inspection mode, supervise the robot, and choose isolation as the handling decision. The system highlights the red isolation container. The learner must route the battery to the isolation container. If the wrong decision is made, a consequence panel explains the real-world impact.\"\n        },\n        {\n          \"step_id\": \"4\",\n          \"step_number\": 4,\n          \"title\": \"Micro-Reflection. A short panel asks: \\u201cWhich routing decision most reduced the risk in the previous\",\n          \"description\": \"case?\\u201d The learner selects an answer before continuing.\"\n        },\n        {\n          \"step_id\": \"5\",\n          \"step_number\": 5,\n          \"title\": \"Progressive Challenge\",\n          \"description\": \"A random case (intact, deformed, or leaking) is presented without hints. The learner completes the full workflow independently while background factory noise and a countdown timer are active. The learner must select the inspection sequence, validate the result, and route the battery to the correct container. This step prepares the learner for autonomous operation.\"\n        }\n      ]\n    },\n    \"learner_monitoring\": [\n      \"The system records into a log file: case selection accuracy, routing correctness,\",\n      \"response time, number of hints used, and critical risk errors.\"\n    ]\n  },\n  \"plan_summary\": {\n    \"plan_title\": \"Robot-Assisted Inspection of Wasted Automotive Batteries\",\n    \"training_domain\": \"XR vocational training\",\n    \"high_level_goal\": \"Understand the main safety, environmental, and operational risks associated with robot-assisted inspection of wasted automotive batteries.\",\n    \"module_sequence\": [\n      {\n        \"module_id\": \"1\",\n        \"title\": \"Introduction and Basic Environment Understanding (25 minutes)\",\n        \"focus\": \"This module serves as a low-pressure onboarding phase that allows learners to become familiar with the XR environment, basic controls, and spatial layout before engaging in safety-\"\n      },\n      {\n        \"module_id\": \"2\",\n        \"title\": \"Safety Boundaries Understanding (50 minutes)\",\n        \"focus\": \"This module trains learners to behave safely when a robot is operating in a shared workspace. Unlike Module 1, which introduced static areas and basic robot motion, this module foc\"\n      },\n      {\n        \"module_id\": \"3\",\n        \"title\": \"Human Decisions and Robotic Actions Coordination (60 minutes)\",\n        \"focus\": \"This module introduces the complete human\\u2013robot inspection cycle and trains learners to coordinate their decisions with robotic execution. Unlike previous modules, this phase expli\"\n      },\n      {\n        \"module_id\": \"4\",\n        \"title\": \"Supervised Risk-Based Inspection Scenarios (75 minutes)\",\n        \"focus\": \"This module transitions learners from procedural execution to risk-aware decision- making aligned with real industrial battery treatment practices. Learners must not only validate \"\n      },\n      {\n        \"module_id\": \"5\",\n        \"title\": \"Autonomous Risk-Based Decision-Making (60 minutes)\",\n        \"focus\": \"This module simulates realistic industrial operating conditions in which learners must act independently while respecting production throughput constraints. In addition to safety a\"\n      },\n      {\n        \"module_id\": \"6\",\n        \"title\": \"Assessment, Reflection, and Readiness Validation (30 minutes)\",\n        \"focus\": \"This module consolidates learning by transforming performance data into reflective awareness. Learners are evaluated on their ability to act safely, make risk-informed decisions, a\"\n      }\n    ],\n    \"global_constraints\": [\n      \"Preserve module order from educational plan.\",\n      \"Implement one module at a time with validation loop.\"\n    ],\n    \"asset_themes\": [\n      \"3D models\",\n      \"process console\",\n      \"safety interactions\"\n    ],\n    \"agent_context\": \"This summary is deterministic fallback output because LLM summarization was unavailable.\"\n  }\n}",
      "scene_hierarchy": {
        "scene_root": "Root",
        "hierarchy": [
          {
            "name": "Exercise",
            "purpose": "Main exercise container",
            "children": [
              {
                "name": "Environment",
                "purpose": "Physical environment setup",
                "children": [
                  {
                    "name": "RobotCell",
                    "purpose": "Contains the robotic inspection area",
                    "prefab_hint": "robot_workcell",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider"
                    ]
                  },
                  {
                    "name": "SafetyZones",
                    "purpose": "Defines restricted areas for safety",
                    "children": [
                      {
                        "name": "RedZone",
                        "purpose": "High-risk interaction zone",
                        "prefab_hint": "safety_zone_red"
                      },
                      {
                        "name": "YellowZone",
                        "purpose": "Cautionary interaction zone",
                        "prefab_hint": "safety_zone_yellow"
                      }
                    ]
                  },
                  {
                    "name": "Floor",
                    "purpose": "Base surface for the environment",
                    "components": [
                      "MeshRenderer",
                      "MeshFilter"
                    ]
                  }
                ]
              },
              {
                "name": "InteractableObjects",
                "purpose": "Objects learners can interact with",
                "children": [
                  {
                    "name": "Batteries",
                    "purpose": "Different battery states for inspection",
                    "children": [
                      {
                        "name": "IntactBattery",
                        "purpose": "Visually intact battery for inspection",
                        "prefab_hint": "battery_intact",
                        "components": [
                          "MeshRenderer",
                          "BoxCollider",
                          "XRGrabInteractable"
                        ]
                      },
                      {
                        "name": "DeformedBattery",
                        "purpose": "Visibly deformed battery for inspection",
                        "prefab_hint": "battery_deformed",
                        "components": [
                          "MeshRenderer",
                          "BoxCollider",
                          "XRGrabInteractable"
                        ]
                      },
                      {
                        "name": "LeakingBattery",
                        "purpose": "Battery with visible leakage",
                        "prefab_hint": "battery_leaking",
                        "components": [
                          "MeshRenderer",
                          "BoxCollider",
                          "XRGrabInteractable"
                        ]
                      }
                    ]
                  },
                  {
                    "name": "HandlingContainers",
                    "purpose": "Containers for routing batteries",
                    "children": [
                      {
                        "name": "ApprovalBin",
                        "purpose": "Green container for approved batteries",
                        "prefab_hint": "container_green",
                        "components": [
                          "MeshRenderer",
                          "BoxCollider",
                          "XRGrabInteractable"
                        ]
                      },
                      {
                        "name": "ReRoutingCrate",
                        "purpose": "Yellow container for re-routing batteries",
                        "prefab_hint": "container_yellow",
                        "components": [
                          "MeshRenderer",
                          "BoxCollider",
                          "XRGrabInteractable"
                        ]
                      },
                      {
                        "name": "IsolationContainer",
                        "purpose": "Red container for isolating critical batteries",
                        "prefab_hint": "container_red",
                        "components": [
                          "MeshRenderer",
                          "BoxCollider",
                          "XRGrabInteractable"
                        ]
                      }
                    ]
                  },
                  {
                    "name": "InspectionConsole",
                    "purpose": "Console for interacting with inspection data",
                    "prefab_hint": "control_console",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRInteractiveComponent"
                    ]
                  }
                ]
              },
              {
                "name": "UI",
                "purpose": "User interface elements",
                "children": [
                  {
                    "name": "ConsoleDisplay",
                    "purpose": "Shows inspection results and guidance",
                    "prefab_hint": "screen_display"
                  },
                  {
                    "name": "FeedbackPanel",
                    "purpose": "Provides feedback on learner decisions",
                    "prefab_hint": "info_panel"
                  },
                  {
                    "name": "ConsequencePanel",
                    "purpose": "Shows consequences of incorrect decisions",
                    "prefab_hint": "warning_panel"
                  },
                  {
                    "name": "Timer",
                    "purpose": "Displays time constraints for tasks",
                    "prefab_hint": "digital_timer"
                  },
                  {
                    "name": "ComparisonPanel",
                    "purpose": "Shows optimal vs actual choices comparison",
                    "prefab_hint": "comparison_screen"
                  }
                ]
              },
              {
                "name": "StepContainer",
                "purpose": "Parent for all training step GameObjects"
              }
            ]
          }
        ]
      },
      "available_templates": {
        "text": "No templates available.",
        "truncated": false,
        "original_length": 23
      }
    },
    "raw_llm_response": "```json\n{\n  \"steps\": [\n    {\n      \"step_id\": 0,\n      \"title\": \"Scene and Environment Setup\",\n      \"description\": \"Set up the main exercise container and environment elements.\",\n      \"actions\": [\n        \"Create ExerciseRoot and set up the environment structure.\"\n      ],\n      \"acceptance_criteria\": [\n        \"ExerciseRoot and StepContainer exist in the scene hierarchy.\",\n        \"Environment components are properly initialized.\"\n      ]\n    },\n    {\n      \"step_id\": 1,\n      \"title\": \"Robot Cell and Safety Zones Implementation\",\n      \"description\": \"Implement the robotic inspection area and safety zones.\",\n      \"actions\": [\n        \"Spawn RobotCell prefab with proper collider and renderer components.\",\n        \"Set up SafetyZones including RedZone and YellowZone.\"\n      ],\n      \"acceptance_criteria\": [\n        \"RobotCell is properly placed and functional.\",\n        \"Safety zones are visible and correctly configured.\"\n      ],\n      \"required_assets\": [\n        {\n          \"name\": \"robot_workcell\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"safety_zone_red\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"safety_zone_yellow\",\n          \"type\": \"3D model\"\n        }\n      ],\n      \"required_knowledge\": [\n        {\n          \"topic\": \"Robot Cell Setup\",\n          \"description\": \"Understanding how to configure robotic workcells and safety zones.\"\n        }\n      ]\n    },\n    {\n      \"step_id\": 2,\n      \"title\": \"Inspection Console and UI Elements Implementation\",\n      \"description\": \"Implement the inspection console and user interface elements.\",\n      \"actions\": [\n        \"Spawn InspectionConsole with interactive components.\",\n        \"Set up UI elements including ConsoleDisplay, FeedbackPanel, and Timer.\"\n      ],\n      \"acceptance_criteria\": [\n        \"InspectionConsole is interactive and properly configured.\",\n        \"UI elements are visible and functional.\"\n      ],\n      \"required_assets\": [\n        {\n          \"name\": \"control_console\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"screen_display\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"info_panel\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"digital_timer\",\n          \"type\": \"3D model\"\n        }\n      ],\n      \"required_knowledge\": [\n        {\n          \"topic\": \"UI Implementation\",\n          \"description\": \"Understanding how to set up and configure user interface elements.\"\n        }\n      ]\n    },\n    {\n      \"step_id\": 3,\n      \"title\": \"Battery Handling and Inspection Logic\",\n      \"description\": \"Implement battery spawning and inspection logic.\",\n      \"actions\": [\n        \"Set up Batteries with different states (Intact, Deformed, Leaking).\",\n        \"Implement interaction logic for battery inspection.\"\n      ],\n      \"acceptance_criteria\": [\n        \"Batteries are properly spawned and interactive.\",\n        \"Inspection logic is functional.\"\n      ],\n      \"required_assets\": [\n        {\n          \"name\": \"battery_intact\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"battery_deformed\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"battery_leaking\",\n          \"type\": \"3D model\"\n        }\n      ],\n      \"required_knowledge\": [\n        {\n          \"topic\": \"Battery Inspection Logic\",\n          \"description\": \"Understanding how to implement battery state inspection and interaction.\"\n        }\n      ]\n    },\n    {\n      \"step_id\": 4,\n      \"title\": \"Consequence Visualization and Feedback\",\n      \"description\": \"Implement consequence visualization and feedback mechanisms.\",\n      \"actions\": [\n        \"Set up ConsequencePanel and ComparisonPanel.\",\n        \"Implement timer functionality for task constraints.\"\n      ],\n      \"acceptance_criteria\": [\n        \"Consequence visualization is functional.\",\n        \"Feedback mechanisms are properly configured.\"\n      ],\n      \"required_assets\": [\n        {\n          \"name\": \"warning_panel\",\n          \"type\": \"3D model\"\n        },\n        {\n          \"name\": \"comparison_screen\",\n          \"type\": \"3D model\"\n        }\n      ],\n      \"required_knowledge\": [\n        {\n          \"topic\": \"Consequence Visualization\",\n          \"description\": \"Understanding how to implement consequence visualization and feedback.\"\n        }\n      ]\n    }\n  ]\n}\n```",
    "parsed": {
      "steps": [
        {
          "step_id": 0,
          "title": "Scene and Environment Setup",
          "description": "Set up the main exercise container and environment elements.",
          "actions": [
            "Create ExerciseRoot and set up the environment structure."
          ],
          "acceptance_criteria": [
            "ExerciseRoot and StepContainer exist in the scene hierarchy.",
            "Environment components are properly initialized."
          ]
        },
        {
          "step_id": 1,
          "title": "Robot Cell and Safety Zones Implementation",
          "description": "Implement the robotic inspection area and safety zones.",
          "actions": [
            "Spawn RobotCell prefab with proper collider and renderer components.",
            "Set up SafetyZones including RedZone and YellowZone."
          ],
          "acceptance_criteria": [
            "RobotCell is properly placed and functional.",
            "Safety zones are visible and correctly configured."
          ],
          "required_assets": [
            {
              "name": "robot_workcell",
              "type": "3D model"
            },
            {
              "name": "safety_zone_red",
              "type": "3D model"
            },
            {
              "name": "safety_zone_yellow",
              "type": "3D model"
            }
          ],
          "required_knowledge": [
            {
              "topic": "Robot Cell Setup",
              "description": "Understanding how to configure robotic workcells and safety zones."
            }
          ]
        },
        {
          "step_id": 2,
          "title": "Inspection Console and UI Elements Implementation",
          "description": "Implement the inspection console and user interface elements.",
          "actions": [
            "Spawn InspectionConsole with interactive components.",
            "Set up UI elements including ConsoleDisplay, FeedbackPanel, and Timer."
          ],
          "acceptance_criteria": [
            "InspectionConsole is interactive and properly configured.",
            "UI elements are visible and functional."
          ],
          "required_assets": [
            {
              "name": "control_console",
              "type": "3D model"
            },
            {
              "name": "screen_display",
              "type": "3D model"
            },
            {
              "name": "info_panel",
              "type": "3D model"
            },
            {
              "name": "digital_timer",
              "type": "3D model"
            }
          ],
          "required_knowledge": [
            {
              "topic": "UI Implementation",
              "description": "Understanding how to set up and configure user interface elements."
            }
          ]
        },
        {
          "step_id": 3,
          "title": "Battery Handling and Inspection Logic",
          "description": "Implement battery spawning and inspection logic.",
          "actions": [
            "Set up Batteries with different states (Intact, Deformed, Leaking).",
            "Implement interaction logic for battery inspection."
          ],
          "acceptance_criteria": [
            "Batteries are properly spawned and interactive.",
            "Inspection logic is functional."
          ],
          "required_assets": [
            {
              "name": "battery_intact",
              "type": "3D model"
            },
            {
              "name": "battery_deformed",
              "type": "3D model"
            },
            {
              "name": "battery_leaking",
              "type": "3D model"
            }
          ],
          "required_knowledge": [
            {
              "topic": "Battery Inspection Logic",
              "description": "Understanding how to implement battery state inspection and interaction."
            }
          ]
        },
        {
          "step_id": 4,
          "title": "Consequence Visualization and Feedback",
          "description": "Implement consequence visualization and feedback mechanisms.",
          "actions": [
            "Set up ConsequencePanel and ComparisonPanel.",
            "Implement timer functionality for task constraints."
          ],
          "acceptance_criteria": [
            "Consequence visualization is functional.",
            "Feedback mechanisms are properly configured."
          ],
          "required_assets": [
            {
              "name": "warning_panel",
              "type": "3D model"
            },
            {
              "name": "comparison_screen",
              "type": "3D model"
            }
          ],
          "required_knowledge": [
            {
              "topic": "Consequence Visualization",
              "description": "Understanding how to implement consequence visualization and feedback."
            }
          ]
        }
      ]
    },
    "fallback_used": false
  }
}
```

## final execution plan

```json
{
  "overview": "Execution plan for scene 'Root' with 5 implementation steps.",
  "scene_hierarchy": {
    "scene_root": "Root",
    "hierarchy": [
      {
        "name": "Exercise",
        "purpose": "Main exercise container",
        "children": [
          {
            "name": "Environment",
            "purpose": "Physical environment setup",
            "children": [
              {
                "name": "RobotCell",
                "purpose": "Contains the robotic inspection area",
                "prefab_hint": "robot_workcell",
                "components": [
                  "MeshRenderer",
                  "BoxCollider"
                ]
              },
              {
                "name": "SafetyZones",
                "purpose": "Defines restricted areas for safety",
                "children": [
                  {
                    "name": "RedZone",
                    "purpose": "High-risk interaction zone",
                    "prefab_hint": "safety_zone_red"
                  },
                  {
                    "name": "YellowZone",
                    "purpose": "Cautionary interaction zone",
                    "prefab_hint": "safety_zone_yellow"
                  }
                ]
              },
              {
                "name": "Floor",
                "purpose": "Base surface for the environment",
                "components": [
                  "MeshRenderer",
                  "MeshFilter"
                ]
              }
            ]
          },
          {
            "name": "InteractableObjects",
            "purpose": "Objects learners can interact with",
            "children": [
              {
                "name": "Batteries",
                "purpose": "Different battery states for inspection",
                "children": [
                  {
                    "name": "IntactBattery",
                    "purpose": "Visually intact battery for inspection",
                    "prefab_hint": "battery_intact",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRGrabInteractable"
                    ]
                  },
                  {
                    "name": "DeformedBattery",
                    "purpose": "Visibly deformed battery for inspection",
                    "prefab_hint": "battery_deformed",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRGrabInteractable"
                    ]
                  },
                  {
                    "name": "LeakingBattery",
                    "purpose": "Battery with visible leakage",
                    "prefab_hint": "battery_leaking",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRGrabInteractable"
                    ]
                  }
                ]
              },
              {
                "name": "HandlingContainers",
                "purpose": "Containers for routing batteries",
                "children": [
                  {
                    "name": "ApprovalBin",
                    "purpose": "Green container for approved batteries",
                    "prefab_hint": "container_green",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRGrabInteractable"
                    ]
                  },
                  {
                    "name": "ReRoutingCrate",
                    "purpose": "Yellow container for re-routing batteries",
                    "prefab_hint": "container_yellow",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRGrabInteractable"
                    ]
                  },
                  {
                    "name": "IsolationContainer",
                    "purpose": "Red container for isolating critical batteries",
                    "prefab_hint": "container_red",
                    "components": [
                      "MeshRenderer",
                      "BoxCollider",
                      "XRGrabInteractable"
                    ]
                  }
                ]
              },
              {
                "name": "InspectionConsole",
                "purpose": "Console for interacting with inspection data",
                "prefab_hint": "control_console",
                "components": [
                  "MeshRenderer",
                  "BoxCollider",
                  "XRInteractiveComponent"
                ]
              }
            ]
          },
          {
            "name": "UI",
            "purpose": "User interface elements",
            "children": [
              {
                "name": "ConsoleDisplay",
                "purpose": "Shows inspection results and guidance",
                "prefab_hint": "screen_display"
              },
              {
                "name": "FeedbackPanel",
                "purpose": "Provides feedback on learner decisions",
                "prefab_hint": "info_panel"
              },
              {
                "name": "ConsequencePanel",
                "purpose": "Shows consequences of incorrect decisions",
                "prefab_hint": "warning_panel"
              },
              {
                "name": "Timer",
                "purpose": "Displays time constraints for tasks",
                "prefab_hint": "digital_timer"
              },
              {
                "name": "ComparisonPanel",
                "purpose": "Shows optimal vs actual choices comparison",
                "prefab_hint": "comparison_screen"
              }
            ]
          },
          {
            "name": "StepContainer",
            "purpose": "Parent for all training step GameObjects"
          }
        ]
      }
    ]
  },
  "implementation_steps": [
    {
      "step_id": 0,
      "title": "Scene and Environment Setup",
      "description": "Set up the main exercise container and environment elements.",
      "actions": [
        "Create ExerciseRoot and set up the environment structure."
      ],
      "acceptance_criteria": [
        "ExerciseRoot and StepContainer exist in the scene hierarchy.",
        "Environment components are properly initialized."
      ]
    },
    {
      "step_id": 1,
      "title": "Robot Cell and Safety Zones Implementation",
      "description": "Implement the robotic inspection area and safety zones.",
      "actions": [
        "Spawn RobotCell prefab with proper collider and renderer components.",
        "Set up SafetyZones including RedZone and YellowZone."
      ],
      "acceptance_criteria": [
        "RobotCell is properly placed and functional.",
        "Safety zones are visible and correctly configured."
      ],
      "required_assets": [
        {
          "name": "robot_workcell",
          "type": "3D model"
        },
        {
          "name": "safety_zone_red",
          "type": "3D model"
        },
        {
          "name": "safety_zone_yellow",
          "type": "3D model"
        }
      ],
      "required_knowledge": [
        {
          "topic": "Robot Cell Setup",
          "description": "Understanding how to configure robotic workcells and safety zones."
        }
      ]
    },
    {
      "step_id": 2,
      "title": "Inspection Console and UI Elements Implementation",
      "description": "Implement the inspection console and user interface elements.",
      "actions": [
        "Spawn InspectionConsole with interactive components.",
        "Set up UI elements including ConsoleDisplay, FeedbackPanel, and Timer."
      ],
      "acceptance_criteria": [
        "InspectionConsole is interactive and properly configured.",
        "UI elements are visible and functional."
      ],
      "required_assets": [
        {
          "name": "control_console",
          "type": "3D model"
        },
        {
          "name": "screen_display",
          "type": "3D model"
        },
        {
          "name": "info_panel",
          "type": "3D model"
        },
        {
          "name": "digital_timer",
          "type": "3D model"
        }
      ],
      "required_knowledge": [
        {
          "topic": "UI Implementation",
          "description": "Understanding how to set up and configure user interface elements."
        }
      ]
    },
    {
      "step_id": 3,
      "title": "Battery Handling and Inspection Logic",
      "description": "Implement battery spawning and inspection logic.",
      "actions": [
        "Set up Batteries with different states (Intact, Deformed, Leaking).",
        "Implement interaction logic for battery inspection."
      ],
      "acceptance_criteria": [
        "Batteries are properly spawned and interactive.",
        "Inspection logic is functional."
      ],
      "required_assets": [
        {
          "name": "battery_intact",
          "type": "3D model"
        },
        {
          "name": "battery_deformed",
          "type": "3D model"
        },
        {
          "name": "battery_leaking",
          "type": "3D model"
        }
      ],
      "required_knowledge": [
        {
          "topic": "Battery Inspection Logic",
          "description": "Understanding how to implement battery state inspection and interaction."
        }
      ]
    },
    {
      "step_id": 4,
      "title": "Consequence Visualization and Feedback",
      "description": "Implement consequence visualization and feedback mechanisms.",
      "actions": [
        "Set up ConsequencePanel and ComparisonPanel.",
        "Implement timer functionality for task constraints."
      ],
      "acceptance_criteria": [
        "Consequence visualization is functional.",
        "Feedback mechanisms are properly configured."
      ],
      "required_assets": [
        {
          "name": "warning_panel",
          "type": "3D model"
        },
        {
          "name": "comparison_screen",
          "type": "3D model"
        }
      ],
      "required_knowledge": [
        {
          "topic": "Consequence Visualization",
          "description": "Understanding how to implement consequence visualization and feedback."
        }
      ]
    }
  ],
  "new_template_proposals": []
}
```
