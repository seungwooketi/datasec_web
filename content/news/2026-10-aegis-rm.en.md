---
title: AEGIS-RM awarded: securing the intelligence inside factory robots
date: 2026-10-18
category: project
summary: A joint proposal with Seoul National University, ENKI WhiteHat, Roboworks and Kyoungwoo Precision has been selected for MoTIR funding. Over four years we will build technology that protects the models of manufacturing robots and the process know-how they learn.
---

A government R&D proposal that the AI Data and Security Research Center at KETI prepared together with Seoul National University, ENKI WhiteHat, Roboworks and Kyoungwoo Precision has been selected for funding. The agreement has now been signed and the work is under way.

The project, AEGIS-RM (Action-aware Edge-Guarded Intelligence and Secure-execution for Robots and Manufacturing), is part of the 2026 Robot Industry Technology Development Programme of Korea's Ministry of Trade, Industry and Resources (MoTIR), managed by the Korea Evaluation Institute of Industrial Technology (KEIT). It runs for four years, from August 2026 to December 2029, with KETI as the lead institute.

# What the project sets out to do

Generative AI is moving into robots, and the output is no longer text but motion. A robot on a factory floor learns the craft of its operators: trajectories, grasp poses, alignment rules, press parameters. If the model is stolen or inverted, that know-how walks out with it. And a bad output from a vision-language-action model (VLA) or robot foundation model (RFM) turns straight into motor motion, which conventional IT security and functional safety were not designed to handle on their own.

AEGIS-RM aims to build a security platform that protects robot intelligence, and the manufacturing knowledge it carries, across training, inference and control.

![Diagram moving from the current shop floor (manual sorting, operator know-how at risk) through the AEGIS-RM security architecture stack to a protected smart factory. The stack has five layers: policy observability and agentic AI, industrial knowledge and model protection, intelligence-control separation, trusted execution environment, and edge hardware](/assets/news/2026-10-aegis-rm/architecture-stack-en.jpg "The AEGIS-RM security architecture, from today's know-how-dependent line (AS-IS) to a smart factory whose process knowledge is protected (TO-BE)")

# Key capabilities

The robot's on-edge intelligence sits at the centre, wrapped in four layers. The inner two protect; the outer two defend.

1. **Trusted execution on a TEE**: confidential inference in hardware-isolated memory, and signed containers to stop lateral movement
2. **Protecting learned knowledge**: guarding training data against poisoning and backdoors, with irreversible learning and watermarking to keep know-how inside the model
3. **Separating intelligence from control, with anomaly detection**: catching direct, indirect and visual prompt injection, tampered control parameters and abnormal behaviour
4. **Zero-trust policy and unified monitoring**: ZTA monitoring, emergency stop, and preventing leaks of in-house knowledge (KB/ERP)

![Concentric rings around the edge AI RFM: TEE trusted execution, model and training-data protection, prompt-injection and behaviour-anomaly detection, and ZTA monitoring with in-house knowledge protection, each tagged with the logo of the partner responsible](/assets/news/2026-10-aegis-rm/four-layer-defense-en.png "The four-layer defence: 1 trusted execution, 2 model and data protection, 3 intelligence-control separation and anomaly detection, 4 zero-trust monitoring"){width=60%}

The work is organised into six security modules.

- **Hardware trusted execution (M1)**: TEE runtime on ARM TrustZone/OP-TEE, Secure Boot and remote attestation, Confidential Containers
- **Intelligence-control separation (M2)**: splitting decision from control and checking every command at a real-time semantic and physical safety gate, with layered prompt-injection defence
- **Behaviour-based anomaly detection (M3)**: hybrid detection on physical residuals, combining statistics, inverse dynamics and deep learning to tell cyber-induced anomalies from mechanical faults
- **AI model protection (M4)**: model-extraction detection, action-space watermarking, safe inference inside the TEE
- **Secure training pipeline (M5)**: irreversible learning that keeps task performance, plus security for the RFM training pipeline and KB/ERP connectors
- **Security operations and autonomous response (M6)**: SIEM correlation, a ZTA (OPA) policy engine, an explainable dashboard, and autonomous response with a human in the loop

The targets are a model-inversion success rate of 30% or less and at least 90% detection and blocking of abnormal access, while showing that process quality and task performance hold up with security switched on.

# Partners and roles

The consortium stands on two pillars, security and robotics.

- **KETI (lead)**: the AI Data and Security Research Center covers anomaly detection, secure training, monitoring and autonomous response; KETI's Intelligent Robotics Research Center covers intelligence-control separation and platform integration
- **Seoul National University**: hardware TEE, TEE inference, Confidential Containers, irreversible learning
- **ENKI WhiteHat**: red teaming and penetration testing, model-protection validation, security monitoring
- **Roboworks**: robot platform, testbed and connector security
- **Kyoungwoo Precision**: the end user, providing a brake-drum press line, its data, and on-site validation

![Programme structure under a 'Secure Physical AI' roof: KETI as lead, Seoul National University and ENKI WhiteHat on the AI security pillar, Roboworks and Kyoungwoo Precision on the AI robotics pillar, and a brake-drum pick-and-place testbed as the validation base](/assets/news/2026-10-aegis-rm/consortium-en.png "Two pillars, security and robotics. Validation runs on a brake-drum pick-and-place testbed (Franka FR3, NVIDIA Jetson Thor, ROS2, K3s)")

Validation starts on a real press line, picking and aligning ring-shaped parts and starting the press through a two-hand control, and then extends to inspection, stacking and mobile platforms.

# Looking ahead

We thank our partners for preparing this proposal with us. Over the next four years we will work closely with them to deliver robot security technology that manufacturers can rely on, and we will report progress here as the project moves forward.

If you work in adjacent fields such as physical security or humanoids and are interested in working with us, please get in touch on the [Collaborate](/en/collaborate/) page. Our other projects are listed on the [Research](/en/research/) page.
