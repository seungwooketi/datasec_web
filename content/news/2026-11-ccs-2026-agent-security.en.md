---
title: CCS 2026 in numbers - AI agent security research is growing fast
date: 2026-11-23
category: center
summary: At ACM CCS 2026 in The Hague, main-conference papers on the security of AI agents went from one last year to thirteen. A side-by-side count of the 2025 and 2026 papers.
---

Last week I was at ACM CCS 2026, the ACM SIGSAC conference, held this year in The Hague. One thing was clear: the security of agentic AI has become a topic in its own right. The idea of agentic AI is still young, but a run of hacks and security incidents involving agents has drawn attention to it quickly, and several papers this year dealt specifically with how agents call tools.

Here is how this year's main-conference papers compare with last year's.

| Measure | CCS 2025 | CCS 2026 |
|---|---:|---:|
| Main-conference papers | 316 | 479 |
| AI-focused papers | 86 (27.2%) | 124 (25.9%) |
| of which LLM-focused | 36 (11.4%) | 72 (15.0%) |
| of which other ML (adversarial examples, federated learning, etc.) | 50 (15.8%) | 52 (10.9%) |
| Security of AI agents (the agent is the target) | 1 | 13 |
| Agents used as attack or analysis tools | 0 | 3 |
| Papers mentioning MCP | 0 | 2 |
| ML-track sessions | 10 of 60 | 14 of 74 |

I could not sit in on every session, and there were far too many papers to read every abstract. So I collected the titles and abstracts of the main-conference papers from OpenAlex and applied the same keyword rules to both years, then checked the agent candidates by hand. Posters, demos and workshops are left out. These are my own counts; a different rule would move the numbers a little.

Papers on the security of agents themselves went from one to thirteen, and papers that use agents to attack or analyse systems went from none to three. Growth is expected for a concept this new. Still, agent security incidents have been in the news for less than a year, and the 16 agent papers already make up 3.3% of the main program, up from 0.3% last year. Research is widening fast from the security of the models, such as LLMs, to the security of the agents built on them.

Two papers deal with the Model Context Protocol (MCP), which is fast becoming the standard interface between agents and external tools:

- [ContractGuard: Auditing Semantic Contracts of MCP Tools for Security Violations](https://dl.acm.org/doi/10.1145/3830454.3846789) checks whether what an MCP tool says it does matches what its code does, combining static analysis with LLM reasoning. Run on 3,586 tools from 1,000 real MCP servers, it found 116 security issues.
- [Governing AI Agent with Capability and Delegation Chain](https://dl.acm.org/doi/10.1145/3830454.3846604) presents CapAgent, which keeps least privilege intact when agents hand authority to one another over several hops, using cryptographic credentials scoped to specific APIs and parameters. It integrates with MCP.

At our center we are working on safe tool integration for AI agents in operation: how to manage the information assets an agent can be given as tools (including under Korea's National Network Security Framework, N2SF), how to check that an MCP tool is safe, and how to detect tampering and forgery attacks. If this overlaps with your work, we would be glad to [hear from you](/en/collaborate/).

My field notes from the conference are in [Notes from ACM CCS 2026](/en/news/2026-11-ccs-2026-notes/).
