# ShopAssist — LLM Cost Optimization

**Engineering Assignment | LLM Agent Engineering Internship**

ShopAssist is an e-commerce customer support resolution agent designed to process support tickets, determine appropriate resolutions, and identify the relevant help-center articles while minimizing LLM token consumption.

This project implements two optimization approaches:

- **Question 1:** Cost-optimized single-call support agent.
- **Question 2:** Four-stage support pipeline with deterministic processing and minimal LLM usage.

The objective is to reduce inference costs without compromising the expected ticket-resolution outputs.

---

## 1. Problem Overview

ShopAssist handles customer support requests involving refunds, replacements, digital products, subscriptions, and product damage.

For each ticket, the system must generate:

| Field | Description |
|---|---|
| `action` | Resolution action |
| `kb_article` | Relevant knowledge-base article |

Supported actions:

- `REFUND`
- `REPLACE`
- `SEND_ARTICLE`
- `ESCALATE_TIER2`

The assignment provides a local LLM simulator and a token-based billing system.

### Billing Model

| Token category | Cost |
|---|---:|
| Uncached input | 3 points/token |
| Cached input | 0.3 points/token |
| Output | 15 points/token |

**Cost formula:**

`Total Points = (Uncached Input × 3) + (Cached Input × 0.3) + (Output × 15)`

The optimization targets are:

- Q1: Maximum 3,000 points per public ticket.
- Q2: Maximum 2,500 points per public ticket.

---

## 2. Solution Architecture

### Question 1 — Single-Call Agent

**Objective:** Resolve each support ticket using one LLM call while keeping the output within the 3,000-point budget.

**Implementation:** `question1/agent.py`

The original implementation included unnecessary prompt content, verbose reasoning instructions, a dynamically generated UUID, few-shot examples, and the complete help-center knowledge base.

The optimized implementation reduces this overhead through:

1. **Compact system prompt:** Retains only the necessary resolution policies and output requirements.
2. **Removal of unnecessary context:** Eliminates the full knowledge-base dump and redundant few-shot examples.
3. **Compact order serialization:** Uses compact JSON instead of indented JSON.
4. **Reduced output generation:** Requests only the two graded fields.
5. **Single LLM invocation:** Preserves the one-call architecture.

**Processing flow:**

`Ticket → Order Retrieval → Compact Prompt → LLM → JSON Parsing → Resolution`

### Question 2 — Four-Stage Pipeline

**Objective:** Preserve the four logical processing stages while keeping each public ticket below 2,500 points.

**Implementation:** `question2/agent.py`

The original implementation used four expensive LLM calls and passed large portions of the expanded help center into multiple stages.

The optimized architecture separates deterministic processing from LLM generation.

#### Node 1: Triage

Extracts the customer's intent using lightweight keyword-based classification.

Identifies:
- Refund requests
- Replacement requests
- Damage-related requests
- General support requests

No LLM call is required.

#### Node 2: Retrieve

Uses the order information and deterministic policy engine to identify the appropriate resolution policy.

Loads the relevant article using `load_article()` rather than passing the entire knowledge base.

Implementation: `shared/policy_engine.py`

#### Node 3: Compose

Makes one compact LLM call using:
- Ticket information
- Extracted intent
- Order snapshot
- Selected policy
- Relevant article evidence

The model generates the required structured JSON response.

#### Node 4: Audit

Validates the generated response against the deterministic policy decision.

Checks:
- Whether the action is supported.
- Whether the action matches the policy.
- Whether the knowledge-base article matches the selected article.
- Whether the response can be parsed successfully.

If parsing or validation fails, the pipeline falls back to the deterministic policy decision.

**Processing flow:**

`Ticket → Triage → Retrieve → Compose (LLM) → Audit → Resolution`

The four logical stages are preserved, but only the composition stage requires an LLM invocation.

---

## 3. Benchmark Results

The following results were measured using the repository's local billing simulator.

### Question 1 — Cost Optimization

| Ticket | Baseline | Optimized | Reduction |
|---|---:|---:|---:|
| T-1001 | 8,907 | 1,722 | 80.66% |
| T-1002 | 8,769 | 1,593 | 81.83% |
| T-1003 | 8,739 | 1,554 | 82.22% |
| T-1004 | 8,949 | 1,515 | 83.07% |
| T-1091 | 8,937 | 1,557 | 82.58% |
| **Average** | **8,916** | **1,588.2** | **82.19%** |

**Result:** The optimized implementation achieves the target of 3,000 points per public ticket.

### Question 2 — Cost Optimization

| Ticket | Baseline | Optimized | Reduction |
|---|---:|---:|---:|
| T-1001 | 73,467 | 1,419 | 98.07% |
| T-1002 | 73,140 | 1,260 | 98.28% |
| T-1003 | 73,320 | 1,233 | 98.32% |
| T-1004 | 73,449 | 1,188 | 98.38% |
| T-1091 | 73,506 | 1,245 | 98.31% |
| **Average** | **73,506** | **1,269** | **98.27%** |

**Result:** The optimized implementation achieves the target of 2,500 points per public ticket.

### Overall Comparison

| Metric | Question 1 | Question 2 |
|---|---:|---:|
| Baseline average | 8,916 | 73,506 |
| Optimized average | 1,588.2 | 1,269 |
| Cost reduction | 82.19% | 98.27% |
| Target | ≤ 3,000 | ≤ 2,500 |
| Status | Achieved | Achieved |

The holdout ticket `T-1091` was also evaluated successfully in both implementations.

---

## 4. Repository Structure

```text
shopassist-llm-cost-optimization/
│
├── question1/
│   ├── agent.py
│   └── run.py
│
├── question2/
│   ├── agent.py
│   └── run.py
│
├── shared/
│   ├── billing.py
│   ├── llm.py
│   ├── kb.py
│   ├── tools.py
│   └── policy_engine.py
│
├── tests/
│   ├── test_question1.py
│   └── test_question2.py
│
├── benchmark.py
├── requirements.txt
└── README.md
```

---

## 5. Installation and Execution

### Prerequisites

- Python 3.10+
- Git

### Clone the repository

```bash
git clone https://github.com/VivekAgrawal2005/shopassist-llm-cost-optimization.git

cd shopassist-llm-cost-optimization
```

### Create a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Run Question 1

```bash
python question1/run.py
```

### Run Question 2

```bash
python question2/run.py
```

### Run the benchmark

```bash
python benchmark.py
```

### Run tests

```bash
python -m pytest -v
```

---

## 6. Testing and Validation

The optimized implementations were evaluated using the supplied public tickets and the holdout subscription ticket.

Latest local test execution:

```text
6 passed in 184.30s
```

Validation covers:

- Correct resolution actions.
- Correct knowledge-base article selection.
- Holdout subscription handling.
- Q1 per-ticket cost budget.
- Q2 per-ticket cost budget.
- Expanded help-center context size.

The benchmark script reports input tokens, cached input tokens, uncached input tokens, output tokens, and total points for each ticket.

---

## 7. Design Decisions and Limitations

### Deterministic processing

The Q2 architecture moves policy selection and validation into lightweight Python functions. This avoids spending LLM tokens on operations that can be performed deterministically using structured order data.

### Local simulator limitation

The assignment's `shared/llm.py` implements a local simulator that derives decisions from the supplied `ORDER_SNAPSHOT` using the reference policy implementation.

Consequently, the reported correctness and cost results demonstrate performance against the supplied simulator. They do not independently establish equivalent accuracy or behavior with a real hosted LLM.

The implementation does not import `eval/reference.py` directly in either agent. The simulator itself uses the reference implementation internally.

### Retrieval limitation

The current Q2 retrieval stage uses deterministic policy selection and article loading rather than embedding-based semantic search or vector-database retrieval.

### Production considerations

A production deployment using a hosted LLM would require additional evaluation for:
- Model-generated decision accuracy.
- Prompt-injection resistance.
- Conflicting or incomplete customer information.
- Policy versioning and updates.
- Retry and timeout handling.
- Human escalation workflows.

---

## 8. Conclusion

This project demonstrates two approaches to reducing LLM inference costs in customer support automation.

Question 1 achieves an average cost reduction of **82.19%** through prompt and context optimization.

Question 2 achieves an average cost reduction of **98.27%** by restructuring the pipeline around deterministic processing and reserving LLM usage for composition.

Both implementations satisfy their respective per-ticket cost targets on the supplied public test cases.

The central engineering principle is to use LLMs where language generation adds value, while handling predictable operations through efficient deterministic logic.

---

**Repository:** [ShopAssist — LLM Cost Optimization](https://github.com/VivekAgrawal2005/shopassist-llm-cost-optimization)

