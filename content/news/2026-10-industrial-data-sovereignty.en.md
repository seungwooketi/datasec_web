---
title: Data Sovereignty - From Data Dams to Data Spaces
date: 2026-10-20
source: https://seungwoo.datasec.work/blog/2026/industrial-data-sovereignty/
summary: How industrial data policy is shifting from pooling data in one place to leaving it with its owners while contracts or models travel, traced through GAIA-X, Catena-X, the IPCEIs and Project Tapestry.
---

Industrial AI usually succeeds or fails on whether it can use the process, equipment and quality data scattered across factories and supply chains. Korea's 2020 "Data Dam" set out to gather good data in one place and open it up. The current push for data sovereignty runs the other way: data stays with its owner and is used only within a contract, or a shared model and training tools travel to the data and only the parameters come back.

# The limits of pooling

Korea's AI training data program spent KRW 1.63 trillion between 2017 and 2024 to build 908 datasets, and audits later pointed to missed quality targets and duplicated work. More fundamentally, the data industrial AI needs most, such as process conditions, equipment histories and defect records, is a trade secret that companies will not pool.

# Three ways to implement data sovereignty

- **Pooling**: raw data is collected in a central store (the Data Dam)
- **Data spaces**: data stays in the owner's systems and moves only within a contract and its usage policies (GAIA-X, Catena-X)
- **Distributed training**: the model goes to the data, trains there, and only the weights come back (Project Tapestry)

# GAIA-X and industrial data spaces

GAIA-X began in Germany in 2019 as a plan for a European cloud and has since become a trust framework that verifies participants' identities and their compliance with shared rules. The data itself moves through the Dataspace Protocol and EDC connectors, and nothing moves without a contract. A Gaia-X Hub opened in Korea in November 2025.

Catena-X brought these principles to the automotive industry. As of September 2026, 1,069 companies exchange data on the network, and one deployment reported finding quality problems four months earlier on average. Manufacturing-X, led by Germany's Plattform Industrie 4.0, has extended the model to ten projects across manufacturing, and Korea is now developing its own standard model for industrial data spaces (2026 to 2029).

# The IPCEIs and Project Tapestry

Europe ties infrastructure and AI investment together through IPCEIs, Important Projects of Common European Interest. IPCEI-CIS, approved in 2023, builds a multi-provider cloud-edge continuum, while IPCEI-AI, designed by 19 member states, targets sector-specific foundation models. Both name data spaces and Manufacturing-X as related initiatives.

The AI Alliance's Project Tapestry does not move data at all. Each participant continues training a shared base model on its own data and shares only the weights, an approach the project calls consortium training. Its first two proofs of concept on 7B models were completed in September 2026.

# What it means for industrial AI

- **Protecting the weights**: shared weights can still leak information or carry poisoning, so secure aggregation, differential privacy and checks before merging are needed
- **Attesting environments**: remote attestation can confirm that each node trained with the agreed code and data
- **Linking lineage**: data usage records and model-level AI-BOMs should be traceable together
- **Clean rooms and distributed training together**: data that can leave a company could be used in a clean room, while process data that cannot leave the factory could be handled by distributed training

If a data dam gathers data in one place, data sovereignty aims to keep data where it is and let its value flow.

---

The center's related work is listed on the [Projects](/en/research/) page.
