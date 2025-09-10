import unittest
from pathlib import Path

from src.phase1_data import load_phase1_inputs
from src.abm_anchor import (
    AnchorClientAgent,
    AnchorClientAgentState,
    build_anchor_agent_factory_for_sector,
)


QUARTER = 0.25


class TestPhase5Agents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))

    def test_factory_builds_agent(self):
        # Pick any sector present in both anchor params and primary map
        sector = next(iter(self.bundle.anchor.by_sector.columns))
        factory = build_anchor_agent_factory_for_sector(self.bundle, sector)
        agent = factory()
        self.assertIsInstance(agent, AnchorClientAgent)
        self.assertEqual(agent.state, AnchorClientAgentState.POTENTIAL)
        self.assertGreaterEqual(len(agent.requirements), 1)

    def test_lifecycle_to_active_and_requirements(self):
        # Choose a sector where activation is feasible: threshold <= max projects
        sector = None
        for s in self.bundle.anchor.by_sector.columns:
            max_p = self.bundle.anchor.by_sector.at["max_projects_per_pc", s]
            thr = self.bundle.anchor.by_sector.at["projects_to_client_conversion", s]
            if thr <= max_p:
                sector = s
                break
        self.assertIsNotNone(sector, "No feasible sector found for activation test")
        factory = build_anchor_agent_factory_for_sector(self.bundle, sector)
        agent = factory()

        # Simulate steps until activation and verify non-zero requirements after activation
        # Use a bounded horizon to avoid infinite loops if inputs are pathological
        t = self.bundle.anchor.by_sector.at["anchor_start_year", sector]
        steps = 0
        saw_active = False
        nonzero_after_active = False
        while steps < 200:  # 50 years of quarters
            reqs = agent.act(t, round_no=0, step_no=steps, dt_years=QUARTER)
            if agent.state is AnchorClientAgentState.ACTIVE:
                saw_active = True
                if any(v > 0 for v in reqs.values()):
                    nonzero_after_active = True
                    break
            t += QUARTER
            steps += 1
        self.assertTrue(saw_active, "Agent never became ACTIVE within the test horizon")
        self.assertTrue(nonzero_after_active, "No requirements generated after activation")

    def test_determinism(self):
        # Same feasible sector for determinism check
        sector = None
        for s in self.bundle.anchor.by_sector.columns:
            max_p = self.bundle.anchor.by_sector.at["max_projects_per_pc", s]
            thr = self.bundle.anchor.by_sector.at["projects_to_client_conversion", s]
            if thr <= max_p:
                sector = s
                break
        self.assertIsNotNone(sector, "No feasible sector found for determinism test")
        factory = build_anchor_agent_factory_for_sector(self.bundle, sector)

        # Run two identical agents and compare per-step outputs
        a1 = factory()
        a2 = factory()

        t1 = t2 = self.bundle.anchor.by_sector.at["anchor_start_year", sector]
        for step in range(40):  # 10 years
            r1 = a1.act(t1, 0, step, dt_years=QUARTER)
            r2 = a2.act(t2, 0, step, dt_years=QUARTER)
            self.assertEqual(r1, r2)
            self.assertEqual(a1.state, a2.state)
            t1 += QUARTER
            t2 += QUARTER


if __name__ == "__main__":
    unittest.main()
