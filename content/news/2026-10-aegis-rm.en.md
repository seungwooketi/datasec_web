---
title: AEGIS-RM agreement signed: securing the intelligence inside factory robots
date: 2026-10-18
summary: A four-year project to protect the models of manufacturing robots, and the process know-how they learn, with a four-layer defence from the TEE up to zero-trust monitoring.
---

Generative AI is moving into robots, and the output is no longer text but motion. Security for this kind of physical AI is still thin. We have now signed the agreement for AEGIS-RM, a project in Korea's 2026 Robot Industry Technology Development Programme, managed by the Korea Evaluation Institute of Industrial Technology (KEIT). It runs for four years, from August 2026 to December 2029, with KETI as the lead institute.

AEGIS-RM stands for Action-aware Edge-Guarded Intelligence and Secure-execution for Robots and Manufacturing. The aim is to protect robot intelligence, and the manufacturing knowledge it carries, across training, inference and control.

# Why robot intelligence needs protecting

A robot on a factory floor learns the craft of its operators: trajectories, grasp poses, alignment rules, press parameters. If the model is stolen or inverted, that know-how walks out with it. And unlike a chatbot, a vision-language-action model (VLA) or robot foundation model (RFM) turns a bad output straight into motor motion, which can mean a defective part or an injury.

That is why neither conventional IT security (DLP, prompt filters) nor functional safety (ISO 10218, ISO 13849) transfers cleanly. Work such as RoboPAIR, which steered deployed robots into dangerous actions with crafted prompts alone, suggests that defence has to operate at execution time.

![Diagram moving from the current shop floor (manual sorting, tacit know-how at risk) through the AEGIS-RM security architecture stack to a protected smart factory. The stack has five layers: policy observability and agentic AI, industrial knowledge and model protection, intelligence-control separation, trusted execution environment, and edge hardware. Labels are in Korean and English](/assets/news/2026-10-aegis-rm/architecture-stack.jpg "The AEGIS-RM security architecture stack, from today's manual, know-how-dependent line (AS-IS) to a smart factory whose process knowledge is protected (TO-BE). Labels partly in Korean")

# A four-layer defence

The robot's on-edge intelligence sits at the centre, wrapped in four rings. The inner two protect; the outer two defend.

1. **Trusted execution on a TEE**: confidential inference in hardware-isolated memory, and signed containers to stop lateral movement
2. **Protecting learned knowledge**: guarding training data against poisoning and backdoors, with irreversible learning and watermarking to keep know-how inside the model
3. **Separating intelligence from control, with anomaly detection**: catching direct, indirect and visual prompt injection, tampered control parameters and abnormal behaviour
4. **Zero-trust policy and unified monitoring**: ZTA monitoring, emergency stop, and preventing leaks of in-house knowledge (KB/ERP)

![Concentric rings around the edge AI RFM: TEE trusted execution, model and training-data protection, prompt-injection and behaviour-anomaly detection, and ZTA monitoring with in-house knowledge protection, each tagged with the logo of the partner responsible. Labels are in Korean](/assets/news/2026-10-aegis-rm/four-layer-defense.png "The four-layer defence: 1 trusted execution, 2 model and data protection, 3 intelligence-control separation and anomaly detection, 4 zero-trust monitoring. Labels in Korean")

# Core technologies

The work is organised into six security modules.

- **Hardware trusted execution (M1)**: TEE runtime on ARM TrustZone/OP-TEE, Secure Boot and remote attestation, Confidential Containers
- **Intelligence-control separation (M2)**: splitting decision from control and checking every command at a real-time semantic and physical safety gate, with layered prompt-injection defence
- **Behaviour-based anomaly detection (M3)**: hybrid detection on physical residuals, combining statistics, inverse dynamics and deep learning to tell cyber-induced anomalies from mechanical faults, with explanations
- **AI model protection (M4)**: model-extraction detection, action-space watermarking, safe inference inside the TEE
- **Secure training pipeline (M5)**: irreversible learning that abstracts features while keeping task performance, plus security for the RFM training pipeline and KB/ERP connectors
- **Security operations and autonomous response (M6)**: SIEM correlation, a ZTA (OPA) policy engine, an explainable dashboard, and autonomous response with a human in the loop

The targets are a model-inversion success rate of 30% or less and at least 90% detection and blocking of abnormal access, while showing that process quality and task performance hold up with security switched on.

# Consortium

The consortium stands on two pillars, security and robotics.

- **KETI (lead)**: the AI Data and Security Research Center covers anomaly detection, secure training, monitoring and autonomous response; KETI's Intelligent Robotics Research Center covers intelligence-control separation and platform integration
- **Seoul National University**: hardware TEE, TEE inference, Confidential Containers, irreversible learning
- **ENKI WhiteHat**: red teaming and penetration testing, model-protection validation, security monitoring
- **Roboworks**: robot platform, testbed and connector security
- **Kyoungwoo Precision**: the end user, providing a brake-drum press line, its data, and on-site validation

![Programme structure under a 'Secure Physical AI' roof: KETI as lead, Seoul National University and ENKI WhiteHat on the AI security pillar, Roboworks and Kyoungwoo Precision on the AI robotics pillar, and a brake-drum pick-and-place testbed as the validation base. Labels are in Korean](/assets/news/2026-10-aegis-rm/consortium.png "Two pillars, security and robotics. Validation runs on a brake-drum pick-and-place testbed (Franka FR3, NVIDIA Jetson Thor, ROS2, K3s). Labels in Korean")

Validation starts on a real press line, picking and aligning ring-shaped parts and starting the press through a two-hand control, and then extends to inspection, stacking and mobile platforms.

How far can we trust an AI whose output is motion on a factory floor? We will spend the next four years looking for that answer on a real production line. If you work in adjacent fields such as physical security or humanoids, we would be glad to hear from you on the [Collaborate](/en/collaborate/) page. Our other projects are listed on the [Research](/en/research/) page.
