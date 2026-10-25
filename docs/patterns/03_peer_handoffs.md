# Pattern 03: Peer-to-Peer Swarm (Decentralized Mesh)

## Concept Overview
In a Peer-to-Peer Swarm, agents interact as equals in a decentralized mesh network. There is no central supervisor or router controlling delegation. Any agent can converse with the user, execute domain tools, and dynamically hand off the entire conversation thread to any other peer when the topic shifts.

```mermaid
flowchart LR
    Flight[Flight Specialist] <-->|handoff| Hotel[Hotel Specialist]
    Hotel <-->|handoff| Activity[Activity Specialist]
    Activity <-->|handoff| Flight
```

## How Communication Works
- Agents define mutual `handoffs=[peer_a, peer_b]` lists.
- When an agent senses that a request belongs to a peer, it executes a handoff tool call.
- The conversation history travels with the handoff, giving the receiving peer full situational context without losing past turns.

## Differences between Router (Star) and Swarm (Mesh)
- In a **Router (Star)**, delegation is strictly one-way from the hub outward.
- In a **Swarm (Mesh)**, handoffs can occur multi-directionally over many turns as user requirements evolve (e.g. Flight $\to$ Hotel $\to$ Activity $\to$ Flight).
