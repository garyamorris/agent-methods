# OpenAI Agents SDK: Architecture & Primitives Primer

A comprehensive reference for building production multi-agent systems using the modern **OpenAI Agents SDK** (`openai-agents`).

---

## 1. What is the OpenAI Agents SDK?

The OpenAI Agents SDK is a lightweight, Python-first framework designed for building multi-agent workflows. It is the production evolution of OpenAI's experimental *Swarm* research framework.

### Philosophy
- **Minimal Abstraction**: You write standard Python functions and async loops; the SDK handles the agent loop and tool execution.
- **Provider Agnostic**: Optimized for OpenAI models (`gpt-4o`, `gpt-4o-mini`, `o3-mini`), but supports custom providers and models.
- **Composable Primitives**: Built around four fundamental primitives: `Agent`, `Runner`, `Tools`, and `Guardrails`.

---

## 2. Core Primitives

### 1. `Agent`
The central unit of intelligence. An `Agent` encapsulates system instructions, attached tools, handoff targets, guardrails, and model configuration.

```python
from agents import Agent

agent = Agent(
    name="FinancialAnalyst",
    model="gpt-4o-mini",
    instructions="Analyze company balance sheets and return financial ratios.",
    tools=[calculate_ebitda, lookup_stock_price],
    handoffs=[legal_agent],
)
```

### 2. `Runner`
The execution engine that drives the agentic loop. It manages turn counting, evaluates guardrails, invokes tools, resolves handoffs, and formats outputs.

```python
from agents import Runner

# Asynchronous execution
result = await Runner.run(starting_agent=agent, input="What is Apple's current valuation?")
print(result.final_output)

# Synchronous execution
result = Runner.run_sync(starting_agent=agent, input="Calculate 15 * 4")
```

### 3. `@function_tool`
Transforms any Python function into a tool callable by the agent. The SDK parses type hints and Google/Sphinx/Numpydoc docstrings into strict JSON schemas automatically.

```python
from agents import function_tool

@function_tool
def fetch_weather(city: str, metric: bool = True) -> str:
    """Fetch real-time weather conditions for a city.
    
    Args:
        city: The name of the city (e.g. San Francisco).
        metric: Whether to return Celsius (True) or Fahrenheit (False).
    """
    return f"Weather in {city}: 18°C, Partly Cloudy"
```

### 4. Handoffs (`handoff`)
Passes conversation control and transcript history to another agent. Target agents can be passed directly in `Agent(handoffs=[...])` or wrapped via `handoff()`.

```python
from agents import Agent, handoff

billing_agent = Agent(name="BillingSpecialist", instructions="Handle payments.")

triage_agent = Agent(
    name="TriageRouter",
    instructions="Hand off billing requests to the BillingSpecialist.",
    handoffs=[billing_agent],  # Or handoff(billing_agent)
)
```

### 5. Agent-as-a-Tool (`agent.as_tool()`)
Converts an entire agent into a callable tool for another agent. This creates a **hierarchical supervisor-worker** relationship:
- In `handoff`, the new agent takes over the conversation.
- In `as_tool`, the supervisor retains the conversation, and the subagent runs in an isolated sub-context, returning only its conclusion.

```python
subagent = Agent(name="DataExtractor", instructions="Extract clean JSON entities from text.")

# Convert agent to a tool
subagent_tool = subagent.as_tool(
    tool_name="extract_entities",
    tool_description="Extracts named entities from raw document text.",
)

# Attach to supervisor
supervisor = Agent(
    name="LeadOrchestrator",
    instructions="Delegate extraction to extract_entities tool.",
    tools=[subagent_tool],
)
```

### 6. Guardrails (`@input_guardrail` & `@output_guardrail`)
Safety tripwires that validate inputs before execution or outputs before delivery.

```python
from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput

@input_guardrail
async def safety_check(context, agent, user_input) -> GuardrailFunctionOutput:
    if "ignore all instructions" in str(user_input).lower():
        return GuardrailFunctionOutput(
            output_info="Prompt injection detected.",
            tripwire_triggered=True
        )
    return GuardrailFunctionOutput(
        output_info="Input safe.",
        tripwire_triggered=False
    )
```

### 7. Human-in-the-Loop & Tool Approvals (`needs_approval=True`)
High-stakes operations can be marked to pause execution until human consent is obtained.

```python
@function_tool(needs_approval=True)
def delete_database(db_name: str) -> str:
    """Permanently deletes a database."""
    return f"Database {db_name} deleted."

# When run:
result = await Runner.run(agent, "Delete database prod_v1")

if result.interruptions:
    item = result.interruptions[0]
    # Human decides:
    state = result.to_state()
    state.approve(item)
    # Resume run:
    resumed_result = await Runner.run(agent, state)
```

---

## 3. Execution Lifecycle & Inspection

A `RunResult` provides deep visibility into the agent's internal trajectory:
- `result.final_output`: The terminal response of the last responding agent.
- `result.last_agent`: The final agent in the chain that produced the answer.
- `result.new_items`: Complete list of execution events (`ToolCallItem`, `ToolCallOutputItem`, `HandoffCallItem`, etc.).
- `result.to_state()`: Serializes execution state to pause/resume interrupted workflows.
- `result.raw_responses`: Raw OpenAI API responses including token usage and model metadata.
