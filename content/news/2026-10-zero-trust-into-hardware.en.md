---
title: Zero Trust - From the System Down into the Hardware
date: 2026-10-16
source: https://seungwoo.datasec.work/blog/2026/zero-trust-into-hardware/
summary: Zero trust stops at the boundary of the device. Using a pick-and-place robot as the example, this looks at what changes in access, decision cycles, component identity, enforcement and safety when it is pushed down to the commands a controller sends to each joint.
---

"Never trust, always verify" has become close to common sense in security, but follow the principle downward and it stops at the boundary of the device. A robot cell has firewalls and certificates at its edge and a login on the teach pendant, yet every command from the controller to a joint still runs on the assumption that "it's on the same bus, so it's fine." The [TEE and PCC post](/en/news/2026-10-confidential-computing-tee-pcc/) was about building systems on top of hardware isolation; this one goes the other way and asks what happens when zero trust is pushed all the way down to a robot's joints. The example is the most ordinary cell there is: parts arrive on a conveyor, a camera finds them, and a robot picks them and places them on a tray.

# Where zero trust stops

NIST SP 800-207, the reference document for zero trust architecture (ZTA), counts even IoT actuators as resources in principle. But the CISA maturity model, the US DoD guidance on zero trust for operational technology and KISA's OT zero trust guide do not spell out identity, authorization or enforcement between components inside a device. A recent survey of chip-level security found that none of 45 SoC and NoC security studies met all zero-trust principles.

Inside a robot this gets concrete. In EtherCAT, widely used in cobots and servo systems, ordinary frames are protected only by a CRC, which catches accidental bit errors but does nothing against a frame someone crafted on purpose.

# Building blocks that already exist

Components inside one machine already verify each other in other domains; it just isn't called zero trust.

- **In-vehicle networks**: message authentication and segmentation with AUTOSAR SecOC, MACsec and gateway ECUs
- **Servers and chips**: component identity and firmware attestation with DMTF SPDM, TCG DICE and OCP Caliptra
- **Servo drives**: per-drive identity and channel protection in products from Siemens, Rockwell and B&R
- **Fieldbuses**: EtherCAT symmetric-key pairing, the ETG.1800 security profile draft (September 2026) and CANsec

Seen this way, zero trust inside a robot is less about inventing new security technology than about re-placing ZTA's policy decision point (PDP), policy enforcement point (PEP) and policy information point (PIP) inside a single composite device. The EtherCAT community argues that hardware-enforced rules are enough at field level, so a phased approach that starts with the most critical commands looks more persuasive than changing everything at once.

# How it differs from IT zero trust

The principle is the same, but inside the robot the words change meaning.

- **Access**: not read, write and execute, but whether to move, how far (position, speed, force) and when
- **Decision cycle**: not per session, but split into a per-job loop (minutes) and a per-control-cycle loop (sub-millisecond)
- **Denial**: not a failed request, but a transition to a safe state such as slowing down or a protective stop
- **Identity**: not accounts and certificates, but unique component identity, mounting position (axis) and firmware measurements
- **Availability**: tied directly to production and safety, which makes dependence on an external PDP hard

Two changes stand out: access now means physical motion rather than data, and denial is not free. In IT a denied request shows an error. When a robot rejects a command and stops hard, the part it was holding can fly off or an unbraked gravity axis can drop.

# What to check on every command

There are roughly six things a joint should check when it receives a command.

- **Origin**: a session-key MAC shows that the command came from the registered controller
- **Freshness**: a counter or timestamp blocks replayed or delayed commands
- **Sender state**: measured boot and DICE or SPDM attestation confirm the controller's firmware and configuration
- **Authorization**: a capability token issued by the PDP says whether this subject may request this motion on this axis
- **Physical envelope**: the command value is compared against per-axis position, speed and torque bounds
- **Safety context**: operating mode, enabling device and safety controller state

The envelope check is there because several published attacks get past authentication. Steal an SROS2 keystore and you can inject control commands as a legitimate participant; in an analysis of an industrial robot controller, changing the PID gain on a single axis produced trajectory errors under 2 mm. Authentication answers "who sent this," not "does what they sent make sense," so the joint should compare each command against the envelope in its token, and both commands and status replies should be authenticated.

# Six joints that look alike

A six-axis arm often uses the same drive model on several joints, and today's bus-level identifiers are plaintext, easy to clone, and blind to two identical drives having their cables swapped. Three questions need separate answers: is the part genuine, is its firmware intact, and is it really mounted at J3?

- **Device identity**: issued by the component maker at manufacturing (IDevID, DICE DeviceID) to prove genuineness
- **State identity**: derived by the component itself at every boot (DICE Alias certificate, SPDM measurements) to show firmware integrity
- **Role identity**: issued by the integrator or owner at commissioning or replacement (LDevID) to give policies a name such as R01/J3

Because policies refer to roles ("allow MOVE on J3"), replacing a joint only means issuing a new role identity, not editing the policy. Attestation for the whole robot fits the composite-device model in the IETF RATS architecture, with the controller collecting evidence from joints, gripper and camera and checking it against reference values.

# Decide up high, enforce down low

A joint MCU cannot evaluate a full policy every 1 kHz control cycle, so a two-speed structure makes more sense.

- **Slow path (per job or event)**: on job start, mode change or entering maintenance, the PDP in the controller's secure area evaluates policy and issues a signed capability token to each joint
- **Fast path (per control cycle)**: the joint PEP checks the MAC, the freshness and the token's envelope, nothing more

One published per-command MAC study averaged 7.9 ms per command, too slow for a 1 kHz loop, so hardware crypto acceleration and measurements on a prototype are needed. Policy itself can be split into four layers (component maker, integrator, owner and the current job from the MES), with only the intersection granted.

# Security only narrows

The most delicate part is the relationship with functional safety. The principle can be put simply: the security layer may narrow the motion envelope, never widen it.

- **Independent safety**: STO, SS1, SLS and the safety configuration stay separate from security policy, and the functional-safety certification scope does not change
- **Staged stopping**: instead of triggering STO on a single bad frame, hold the last valid command, decelerate, then SS1
- **Disconnection as a design condition**: while the link is down, no new grants are issued, the robot moves only within the envelope and validity window of tokens it already has, and it stops at the end of the cycle when they expire

If the controller hosting the PDP is itself compromised, putting the PDP in a TEE or a separate secure MCU and storing integrator-signed upper bounds directly in each joint keeps the upper-layer limits and the safety limits in place even when one point falls.

# What is still missing

Current implementations protect the controller and the drive, but the layer that checks whether each command between them is permitted, per-axis and per-motion authorization, and runtime re-attestation are hard to find in any public implementation. Standards and regulation are moving: the EtherCAT security profile (ETG.1800) reached a member-review draft in September 2026, the EU Machinery Regulation applies from January 2027 and the Cyber Resilience Act from December 2027, and ISO 10218-1:2025 now includes cybersecurity requirements insofar as they affect robot safety.

The principles of zero trust stay the same; what changes is the unit they apply to, from user to device, from device to component, from request to a single command. For zero trust to reach from the system into the hardware, security, safety and real-time control need to be designed together.

---

The center's related work is listed on the [Projects](/en/research/) page.
