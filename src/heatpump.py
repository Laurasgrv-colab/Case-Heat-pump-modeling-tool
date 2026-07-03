from pathlib import Path

from tespy.networks import Network
from tespy.components import (
    Source,
    Sink,
    Compressor,
    Condenser,
    HeatExchanger,
    Valve,
    CycleCloser,
)
from tespy.connections import Connection


class HeatPumpModel:
    def __init__(self, config: dict):
        self.config = config
        self.working_fluid = config.get("working_fluid", config.get("fluid", "R134a"))
        self.network = Network(fluids=[self.working_fluid, "water"])
        self.network.units.set_defaults(
            temperature="°C",
            pressure="bar",
            enthalpy="kJ/kg",
            mass_flow="kg/s",
        )
        self.components = {}
        self.connections = {}
        self.design_path = Path(config.get("design_path", "design_case.yaml"))

    def build(self):
        cc = CycleCloser("Cycle Closer")
        comp = Compressor("Compressor")
        cond = Condenser("Condenser")
        valve = Valve("Expansion Valve")
        evap = HeatExchanger("Evaporator")

        source_in = Source("Heat Source In")
        source_out = Sink("Heat Source Out")
        sink_in = Source("Heat Sink In")
        sink_out = Sink("Heat Sink Out")

        self.components = {
            "cc": cc,
            "compressor": comp,
            "condenser": cond,
            "valve": valve,
            "evaporator": evap,
            "source_in": source_in,
            "source_out": source_out,
            "sink_in": sink_in,
            "sink_out": sink_out,
        }

        c1 = Connection(cc, "out1", evap, "in2", label="ref_evap_in")
        c2 = Connection(evap, "out2", comp, "in1", label="ref_comp_in")
        c3 = Connection(comp, "out1", cond, "in1", label="ref_cond_in")
        c4 = Connection(cond, "out1", valve, "in1", label="ref_valve_in")
        c5 = Connection(valve, "out1", cc, "in1", label="ref_valve_out")

        c6 = Connection(source_in, "out1", evap, "in1", label="source_in")
        c7 = Connection(evap, "out1", source_out, "in1", label="source_out")
        c8 = Connection(sink_in, "out1", cond, "in2", label="sink_in")
        c9 = Connection(cond, "out2", sink_out, "in1", label="sink_out")

        self.network.add_conns(c1, c2, c3, c4, c5, c6, c7, c8, c9)

        self.connections = {
            "ref_evap_in": c1,
            "ref_comp_in": c2,
            "ref_cond_in": c3,
            "ref_valve_in": c4,
            "source_in": c6,
            "source_out": c7,
            "sink_in": c8,
            "sink_out": c9,
        }

    def design(self):
        cfg = self.config
        comp = self.components["compressor"]
        cond = self.components["condenser"]
        evap = self.components["evaporator"]

        comp.set_attr(eta_s=cfg.get("compressor_efficiency", 0.85))
        cond.set_attr(pr1=1, pr2=1, ttd_u=5)
        evap.set_attr(pr1=1, pr2=1, ttd_l=5)

        self.connections["ref_evap_in"].set_attr(fluid={self.working_fluid: 1})
        self.connections["ref_comp_in"].set_attr(p0=cfg.get("evap_pressure", 5), T0=cfg.get("heat_source_T_in", 40))
        self.connections["ref_cond_in"].set_attr(p0=cfg.get("cond_pressure", 18), T0=cfg.get("heat_sink_T_out", 90))

        self.connections["source_in"].set_attr(
            T=cfg.get("heat_source_T_in", 40),
            p=1.5,
            m=8.0,
            fluid={"water": 1},
        )
        self.connections["source_out"].set_attr(T=cfg.get("heat_source_T_out", 10))
        self.connections["sink_in"].set_attr(
            T=cfg.get("heat_sink_T_in", 40),
            p=2.0,
            m=4.8,
            fluid={"water": 1},
        )
        self.connections["sink_out"].set_attr(T=cfg.get("heat_sink_T_out", 90))

        self.network.solve("design")
        self.design_path.parent.mkdir(parents=True, exist_ok=True)
        self.network.save(self.design_path)

    def offdesign(self):
        try:
            self.network.solve("offdesign", design_path=self.design_path)
        except Exception:
            self.network.solve("offdesign", init_previous=True)

    def update_boundary_conditions(self, source_T=None, source_m=None, sink_T=None, sink_m=None, row=None):
        if row is not None:
            if isinstance(row, dict):
                row = row
            else:
                row = row.to_dict()
            source_T = row.get("T_source_in", row.get("heat_source_T_in", source_T))
            sink_T = row.get("T_sink_in", row.get("heat_sink_T_in", sink_T))
            source_m = row.get("flow_source", row.get("source_massflow", source_m))
            sink_m = row.get("flow_sink", row.get("sink_massflow", sink_m))

        if source_T is not None:
            self.connections["source_in"].set_attr(T=source_T)
        if source_m is not None:
            self.connections["source_in"].set_attr(m=source_m)
        if sink_T is not None:
            self.connections["sink_in"].set_attr(T=sink_T)
        if sink_m is not None:
            self.connections["sink_in"].set_attr(m=sink_m)

    def get_results(self):
        comp = self.components["compressor"]
        evap = self.components["evaporator"]
        cond = self.components["condenser"]

        power = abs(comp.P.val)
        q_evap = abs(evap.Q.val)
        q_cond = abs(cond.Q.val)
        cop = q_cond / power if power > 0 else None

        return {
            "COP": cop,
            "Power": power,
            "Q_evap": q_evap,
            "Q_cond": q_cond,
        }
