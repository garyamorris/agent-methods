# 🧠 Agent Methods

> **An interactive educational testbed of 15 multi-agent architectures, communication topologies, and orchestration patterns powered by DeepSeek via the OpenAI Agents SDK.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Model: DeepSeek](https://img.shields.io/badge/Model-DeepSeek--V3%20%28deepseek--chat%29-blueviolet.svg)](https://deepseek.com)
[![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI%20Agents%20SDK-0.24+-black.svg)](https://github.com/openai/openai-agents-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

`agent-methods` provides concrete, production-grade implementations of the foundational communication topologies used by autonomous multi-agent systems. All model calls are powered by **DeepSeek** (`deepseek-chat` / DeepSeek-V3) routed through the official **OpenAI Agents SDK**, demonstrating how modern agent frameworks cleanly decouple orchestration logic from model backends.

---

## ⚡ Quickstart

### 1. Clone & Set Up
```bash
git clone https://github.com/garyamorris/agent-methods.git
cd agent-methods

# Using uv (recommended)
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using standard pip
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure Your DeepSeek API Key
```bash
cp .env.example .env
# Set in .env:
# DEEPSEEK_API_KEY=sk-...
```

*(Note: You can also export `DEEPSEEK_API_KEY="sk-..."` in your shell or set `OPENAI_API_KEY` as a fallback).*

### 3. Launch the Interactive CLI or Visualizer
```bash
# Launch interactive terminal menu
python main.py

# Launch interactive browser topology visualizer
python main.py visualizer

# Run performance benchmark suite
python main.py benchmark
```

---

## 🗺️ The 15 Agent Communication Topologies

```mermaid
graph TD
    subgraph "1. Single Agent Loops"
        P01["01. Single Agent ReAct<br/>(Point-to-Point Tool Loop)"]
        P11["11. Plan-and-Solve<br/>(Dynamic Re-planning Loop)"]
        P12["12. Memory-Augmented<br/>(Episodic + Semantic Memory)"]
        P15["15. Tree-of-Thought<br/>(Reflection with Rollback)"]
    end

    subgraph "2. Delegation & Routing"
        P02["02. Router / Triage<br/>(Star / Hub-and-Spoke)"]
        P03["03. Peer Swarm<br/>(Decentralized Mesh)"]
        P04["04. Supervisor & Sub-Agents<br/>(Hierarchical Tree)"]
        P13["13. Federated Teams<br/>(Swarm of Swarms)"]
    end

    subgraph "3. Dataflow & Concurrency"
        P05["05. Sequential Pipeline<br/>(Linear Assembly Line)"]
        P06["06. Parallel Fan-Out/In<br/>(Fork-Join / Map-Reduce)"]
        P07["07. Evaluator-Optimizer<br/>(Generator-Critic Loop)"]
    end

    subgraph "4. Governance & Deliberation"
        P08["08. Multi-Agent Debate<br/>(Adversarial Arena)"]
        P09["09. Human-in-the-Loop<br/>(Guarded Intercept Gate)"]
        P10["10. Shared Blackboard<br/>(Event-Driven Pub-Sub)"]
        P14["14. Consensus Voting<br/>(Ensemble Calibration)"]
    end
```

| # | Pattern Name | Communication Topology | OpenAI Agents SDK Primitive | Primary Use Case |
| :-: | :--- | :--- | :--- | :--- |
| **01** | [**Single Agent ReAct**](src/agent_methods/patterns/p01_single_agent_react.py) | Point-to-Point Tool Loop | `Agent`, `@function_tool`, `Runner.run` | Single-domain data lookup & computation |
| **02** | [**Router / Triage Dispatcher**](src/agent_methods/patterns/p02_router_triage.py) | Star (Hub & Spoke) | `Agent(handoffs=[...])` | Enterprise helpdesk & intent routing |
| **03** | [**Peer-to-Peer Swarm**](src/agent_methods/patterns/p03_peer_handoffs.py) | Mesh Network | Bidirectional `handoffs` | Fluid, multi-step customer journeys |
| **04** | [**Supervisor & Sub-Agents**](src/agent_methods/patterns/p04_supervisor_subagents.py) | Hierarchical Tree | `subagent.as_tool(...)` | Multidisciplinary executive planning |
| **05** | [**Sequential Pipeline**](src/agent_methods/patterns/p05_pipeline_sequential.py) | Linear Assembly Line | Chained `Runner.run(...)` | Publishing, code generation, ETL |
| **06** | [**Parallel Fan-Out / Fan-In**](src/agent_methods/patterns/p06_parallel_fanout_fanin.py) | Fork-Join (Scatter-Gather)| `asyncio.gather(*runners)` | High-speed multi-perspective risk audits |
| **07** | [**Evaluator-Optimizer**](src/agent_methods/patterns/p07_evaluator_optimizer.py) | Cyclic Feedback Loop | Pydantic Schemas + Iteration Gate | Algorithmic code synthesis & contract review |
| **08** | [**Multi-Agent Debate**](src/agent_methods/patterns/p08_debate_consensus.py) | Conversational Arena | Cross-rebuttal turn orchestration | High-stakes architectural decision analysis |
| **09** | [**Human-in-the-Loop & Guardrails**](src/agent_methods/patterns/p09_human_in_the_loop.py) | Guarded Intercept Gate | `@input_guardrail`, `needs_approval=True` | Destructive mutations & sensitive commands |
| **10** | [**Event-Driven Blackboard**](src/agent_methods/patterns/p10_shared_blackboard.py) | Shared Memory Pub-Sub | Central state model + reactive agents | Complex SOC cyber-incident triage |
| **11** | [**Dynamic Plan-and-Solve**](src/agent_methods/patterns/p11_plan_and_solve.py) | Closed-Loop Plan Controller| Dynamic State Machine + Tools | Multi-step software refactoring & migration |
| **12** | [**Memory-Augmented Architecture**](src/agent_methods/patterns/p12_memory_augmented.py) | Multi-Tier Cognitive Memory| Episodic + Semantic Query Tools | Persistent personal companions & CRM agents |
| **13** | [**Federated Multi-Team Swarm**](src/agent_methods/patterns/p13_federated_teams.py) | Swarm of Swarms | Two-Level Nested `as_tool()` | Conway's Law enterprise organizations |
| **14** | [**Consensus Voting & Calibration**](src/agent_methods/patterns/p14_consensus_voting.py) | Ensemble Electoral College | Blind `asyncio.gather` + Weighting | High-stakes zero-day CVE scoring & triage |
| **15** | [**Tree-of-Thought with Rollback**](src/agent_methods/patterns/p15_reflection_tree_search.py) | Branching Search Tree | Heuristic Branch Evaluator + Pruning | High-assurance global optimization |

---

## ⚖️ Trade-off Decision Matrix

| Pattern | Topology | Latency | Token Cost | State Isolation | Blast Radius | Best Suited For |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **01. Single ReAct** | Tool Loop | Low | Low | Low | Contained | Straightforward calculations, single APIs |
| **02. Router / Triage** | Star Hub | Low | Low | Moderate | Low | Multichannel Customer Support, Helpdesks |
| **03. Peer Swarm** | Mesh Network | Moderate | Moderate | Low | Moderate | Fluid exploratory journeys (Travel, Brainstorming) |
| **04. Supervisor** | Tree Hierarchy | Moderate | Moderate | High | Low | Complex strategy, multi-domain planning |
| **05. Sequential Pipeline**| Linear Chain | Moderate | Moderate | High | Low | Publishing, ETL, Code migration |
| **06. Parallel Fan-Out** | Fork-Join | Fast (Concurrent)| High | Absolute | Isolated | Risk audits, comprehensive multi-angle reviews |
| **07. Evaluator-Optimizer**| Cyclic Loop | High (Multi-turn)| High | Moderate | Low | High-assurance code, SQL synthesis, contracts |
| **08. Multi-Agent Debate** | Roundtable Arena| High | High | Low | Low | Ambiguous architectural decisions, policy |
| **09. Human-in-the-Loop** | Intercept Gate | Variable (Human)| Low | High | Minimal | Database wipes, financial operations, compliance |
| **10. Shared Blackboard** | Pub-Sub Store | Moderate | Moderate | Decoupled | Low | SOC incident response, multi-sensor autonomy |
| **11. Plan-and-Solve** | Closed-Loop Plan| High (Adaptive) | High | High | Low | Multi-step software refactoring, scientific search |
| **12. Memory-Augmented** | Cognitive Tiers | Low | Low | High | Low | Persistent executive assistants, CRM profiles |
| **13. Federated Teams** | Swarm of Swarms| Moderate | Moderate | High | Isolated | Enterprise organizations mirroring Conway's Law |
| **14. Consensus Voting** | Blind Ensemble | Fast (Concurrent)| High | Absolute | Minimal | High-stakes zero-day CVE scoring, fraud triage |
| **15. Tree-of-Thought** | Branching Search| High (Search) | High | High | Resilient | Heuristic path planning, combinatorial optimization |

---

## 🌐 Interactive Browser Visualizer

Launch the interactive visual topology lab:
```bash
python main.py visualizer
```
Opens an interactive dashboard on `http://localhost:8000` with:
- Live SVG message-passing topologies and animated packet routing.
- Metric comparison cards (Latency, Token Cost, Isolation, Blast Radius).
- Step-by-step playback simulation and code inspection.

---

## 📚 Deep-Dive Educational Guides

- 📖 [**Multi-Agent Architecture Guide**](docs/ARCHITECTURE_GUIDE.md): Deep-dive analysis of communication mechanics, context hygiene, and common anti-patterns.
- 🛠️ [**OpenAI Agents SDK Primer**](docs/OPENAI_AGENTS_SDK_PRIMER.md): Complete guide to `Agent`, `Runner`, `handoff`, `as_tool`, and `guardrails`.
- 📁 [**Pattern Writeups Directory**](docs/patterns/): Dedicated markdown guides and Mermaid diagrams for every pattern.

---

## 🧪 Automated Testing

```bash
# Run complete test suite (32 tests verifying imports, structures, models)
pytest tests/
```

---

## 📄 License

MIT License. Created by [Gary Morris](https://github.com/garyamorris).
Contributions and architectural discussions are welcome!
