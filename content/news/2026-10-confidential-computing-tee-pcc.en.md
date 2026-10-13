---
title: Confidential Computing - TEE and PCC
date: 2026-10-13
summary: Does running inside a TEE make an AI service trustworthy? A comparison of what cloud confidential computing protects and what Apple's Private Cloud Compute (PCC) adds on top of the TEE, seen as component versus system.
---

If you have a TEE (Trusted Execution Environment), do you have an AI service users can trust? Apple's Private Cloud Compute (PCC) is often described as "Apple's confidential computing," but it does not sit at the same layer as a TEE. A TEE is an isolated region the processor provides; PCC is a service design that uses that region as its foundation and builds a good deal on top. Comparing the two is less about which is better than about seeing what is missing between a component and a system, and how PCC fills the gap.

# How confidential computing works

The Confidential Computing Consortium defines confidential computing as protecting data in use by computing inside a hardware-based, *attested* TEE. The CPU isolates a region and encrypts its memory, measures the software loaded into it, and signs a report with a key fused into the chip. The data owner verifies the report before releasing any decryption key. Isolation and encryption keep others from *seeing*; attestation tells you whether you can *trust*.

The flow hides an assumption: **who verifies the attestation**, and **what reference they use to decide a measurement is "good."** Most of the difference between PCC and ordinary cloud confidential computing comes down to that.

# What cloud confidential computing protects

All three major clouds offer CPU-TEE confidential VMs, and Azure and Google Cloud also offer GPU TEEs on H100 and Blackwell-class hardware. These services distrust the cloud operator, the hypervisor and other tenants, and trust the CPU and GPU vendors' hardware. Physical attacks are mostly out of scope.

The key point is that **the party verifying attestation and releasing keys is the tenant, the customer running the workload.** That fits well when the data owner is also the verifier, as when a bank processes its own data in the cloud. In a personal AI service, though, the data owner is the user and the service operator sits in the tenant's seat. Cloud confidential computing protects the operator from the cloud provider; **it does not protect the user's data from the operator.** A TEE guarantees "code with this hash runs on this hardware." Whether that code keeps data, or whether the operator can get in, is left to system design.

# What PCC adds on top of the TEE

Apple announced PCC in June 2024 with five requirements. For each, what a TEE gives alone and what PCC adds:

- **Stateless computation**: a TEE gives memory encryption and key destruction at teardown; PCC removes general-purpose logging, lets only audited logs leave the node, and re-randomizes the data-volume key on every reboot
- **Enforceable guarantees**: a TEE gives hardware isolation; PCC avoids relying on external components such as TLS-terminating load balancers for core protections
- **No privileged runtime access**: a TEE shuts out the hypervisor and host OS; PCC also removes remote shells, debugging and Developer Mode, and runs only signed code
- **Non-targetability**: not a TEE concept at all; PCC adds a third-party OHTTP relay, blind-signature credentials and encryption to only a subset of nodes
- **Verifiable transparency**: a TEE gives signed measurements; PCC publishes every production image measurement in a transparency log, ships a Virtual Research Environment (VRE) and runs a bounty

The central move is **making the user's device the verifier.** The device encrypts requests only to nodes whose attested measurements match a release in the public transparency log. If the operator quietly deploys different code, it isn't in the log and the device won't send it data: the operator takes itself out of the trust boundary. By publishing images and offering the VRE and up to $1M in bounties, Apple also lets outsiders check what those measurements actually mean.

# June 2026: PCC on commodity cloud TEEs

This June Apple extended PCC to Google Cloud, combining Intel TDX, NVIDIA Blackwell confidential GPUs and Google Titan chips. The principles it set out show how it views the TEE:

- **Multiple roots of trust**: any component that could exfiltrate user data must attest from at least two independent roots of trust from different vendors
- **Hardware ledger**: all hardware in PCC is tracked in a verifiable append-only ledger
- **Not relying on confidential computing alone**: everything from firmware to applications is treated as TCB, and side-channel and privileged-access defenses are not left to confidential computing alone

With physical attacks such as TEE.fail, which pulled attestation keys out of server TEEs with a memory-bus interposer, this reads as a decision not to bet everything on one vendor's TEE and to cover the rest with system design. Personal AI services from Meta, Google and OpenAI are converging on the same shape: TEEs, remote attestation, a third-party relay and a public log.

# What it means for industrial AI

On a factory floor, the party with the model (an equipment vendor) and the party with the data (the plant) are often different. If the data owner can't verify for themselves, "it runs in a TEE, so it's safe" collapses into "trust the operator." Principles worth borrowing from PCC:

- **Design the flow**: attest the environment, provision keys and data, execute in isolation, release only permitted results
- **Place the verifier**: put attestation verification close to the data owner
- **Publish what measurements mean**: transparency logs or reproducible builds
- **Several roots of trust**: layer defenses rather than staking everything on a single vendor's TEE

Public sources show no Korean cloud provider yet offering a TEE product on its own infrastructure. For data collaboration that never releases raw data, and for public-sector AI, domestic attestation-verification and transparency infrastructure will need to be built alongside the hardware.

If a TEE is the technology that keeps others from *seeing*, PCC is the system that lets users *check*.

---

The full article, with figures, comparison tables and references, is on the [blog](https://seungwoo.datasec.work/blog/2026/confidential-computing-tee-vs-pcc/). The center's related work is listed on the [Research](/en/research/) page.
