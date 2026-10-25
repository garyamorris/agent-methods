"""Verify structural contracts of agent patterns (tools, handoffs, agents)."""

import pytest
from agents import Agent
from agent_methods.patterns import (
    p01_single_agent_react,
    p02_router_triage,
    p03_peer_handoffs,
    p04_supervisor_subagents,
    p05_pipeline_sequential,
    p06_parallel_fanout_fanin,
    p07_evaluator_optimizer,
    p08_debate_consensus,
    p09_human_in_the_loop,
    p10_shared_blackboard,
)

def test_pattern_01_structure():
    agent = p01_single_agent_react.create_react_agent()
    assert isinstance(agent, Agent)
    assert len(agent.tools) == 2


def test_pattern_02_structure():
    assert len(p02_router_triage.triage_agent.handoffs) == 3


def test_pattern_03_mesh_structure():
    assert len(p03_peer_handoffs.flight_agent.handoffs) == 2
    assert len(p03_peer_handoffs.hotel_agent.handoffs) == 2
    assert len(p03_peer_handoffs.activity_agent.handoffs) == 2


def test_pattern_04_supervisor_structure():
    assert len(p04_supervisor_subagents.lead_strategist.tools) == 3


def test_pattern_05_pipeline_agents():
    assert p05_pipeline_sequential.spec_extractor.name == "SpecExtractor"
    assert p05_pipeline_sequential.editorial_reviewer.name == "EditorialReviewer"


def test_pattern_06_parallel_agents():
    assert p06_parallel_fanout_fanin.cybersecurity_agent.name == "CybersecurityAuditor"
    assert p06_parallel_fanout_fanin.chief_risk_officer.name == "ChiefRiskOfficer"


def test_pattern_07_optimizer_agents():
    assert p07_evaluator_optimizer.generator_agent.name == "CodeGenerator"
    assert p07_evaluator_optimizer.evaluator_agent.name == "SeniorCodeReviewer"


def test_pattern_08_debate_agents():
    assert p08_debate_consensus.advocate_monolith.name == "AdvocateModularMonolith"
    assert p08_debate_consensus.judge_moderator.name == "JudicialModerator"


def test_pattern_09_guardrail_wiring():
    agent = p09_human_in_the_loop.devops_agent
    assert len(agent.input_guardrails) == 1
    assert len(agent.output_guardrails) == 1
    assert any(getattr(tool, "needs_approval", False) for tool in agent.tools)


def test_pattern_10_blackboard():
    bb = p10_shared_blackboard.Blackboard(incident_id="INC-TEST")
    bb.log_event("Test", "Sample log")
    assert len(bb.timeline) == 1
    assert bb.status == "INVESTIGATING"


def test_pattern_11_plan_state():
    from agent_methods.patterns import p11_plan_and_solve
    plan = p11_plan_and_solve.ExecutionPlan(
        objective="Test",
        steps=[p11_plan_and_solve.PlanStep(step_id=1, description="Step 1")]
    )
    assert len(plan.steps) == 1
    assert plan.steps[0].status == "PENDING"


def test_pattern_12_memory_tools():
    from agent_methods.patterns import p12_memory_augmented
    assert len(p12_memory_augmented.memory_agent.tools) == 3


def test_pattern_13_federated_teams():
    from agent_methods.patterns import p13_federated_teams
    assert len(p13_federated_teams.executive_ceo.tools) == 2


def test_pattern_14_voting_models():
    from agent_methods.patterns import p14_consensus_voting
    ballot = p14_consensus_voting.JurorBallot(
        juror_name="Juror1",
        vote="APPROVE",
        confidence_score=90,
        primary_rationale="Solid architecture."
    )
    assert ballot.vote == "APPROVE"


def test_pattern_15_search_tree():
    from agent_methods.patterns import p15_reflection_tree_search
    branch = p15_reflection_tree_search.CandidateBranch(
        branch_id=1,
        title="Branch 1",
        description="Redis CRDT",
        feasibility_score=85
    )
    assert branch.feasibility_score == 85
