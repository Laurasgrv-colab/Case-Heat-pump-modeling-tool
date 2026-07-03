from pathlib import Path

from tespy.networks import Network
from tespy.components import (
    CycleCloser,
    Compressor,
    Condenser,
    Valve,
    HeatExchanger,
)
from tespy.connections import Connection


class HeatPumpModel:

    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            Dictionary containing all model parameters.
        """

        self.config = config

        self.network = None
        self.design_path = Path(
            config.get("design_path", "design_case")
        )

        self.components = {}
        self.connections = {}


    def build(self):

        self.network = Network(fluids=["R134a", "water"])

        self.network.units.set_defaults(
            temperature="°C",
            pressure="bar",
            enthalpy="kJ / kg",
            mass_flow="kg / s"
        )

        # Refrigerant cycle
        self.components["cc"] = CycleCloser("cycle closer")
        self.components["comp"] = Compressor("compressor")
        self.components["cond"] = Condenser("condenser")
        self.components["valve"] = Valve("expansion valve")
        self.components["evap"] = HeatExchanger("evaporator")

        # Refrigerant loop

        self.connections["c1"] = Connection(
            self.components["cc"],
            "out1",
            self.components["comp"],
            "in1"
        )

        self.connections["c2"] = Connection(
            self.components["comp"],
            "out1",
            self.components["cond"],
            "in1"
        )

        self.connections["c3"] = Connection(
            self.components["cond"],
            "out1",
            self.components["valve"],
            "in1"
        )

        self.connections["c4"] = Connection(
            self.components["valve"],
            "out1",
            self.components["evap"],
            "in1"
        )

        self.connections["c5"] = Connection(
            self.components["evap"],
            "out1",
            self.components["cc"],
            "in1"
        )

        self.network.add_conns(*self.connections.values())



    def design(self):

        cfg = self.config

        # Compressor efficiency
        self.components["comp"].set_attr(
            eta_s=cfg["compressor_efficiency"]
        )

        # Pressure ratios
        self.components["cond"].set_attr(pr1=0.98, pr2=0.98)
        self.components["evap"].set_attr(pr1=0.98, pr2=0.98)

        # Refrigerant state specification
        self.connections["c1"].set_attr(
            p=cfg["evap_pressure"],
            x=1
        )

        self.connections["c3"].set_attr(
            p=cfg["cond_pressure"],
            x=0
        )

        self.network.solve("design")

        self.network.save(self.design_path)


    def update_boundary_conditions(self, row):
        """
        Update TESPy boundary conditions from a dataframe row.
        """

        # Heat source
        self.connections["source_in"].set_attr(
            T=row["source_T_in"],
            p=row["source_P"],
            m=row["source_flow"]
        )

        self.connections["source_out"].set_attr(
            T=row["source_T_out"]
        )

        # Heat sink
        self.connections["sink_in"].set_attr(
            T=row["sink_T_in"],
            p=row["sink_P"],
            m=row["sink_flow"]
        )

        self.connections["sink_out"].set_attr(
            T=row["sink_T_out"]
        )

    def offdesign(self):

        self.network.solve(
            "offdesign",
            design_path=self.design_path
        )

    def get_results(self):

        comp = self.components["comp"]
        evap = self.components["evap"]
        cond = self.components["cond"]

        power = comp.P.val

        q_evap = abs(evap.Q.val)

        q_cond = abs(cond.Q.val)

        cop = q_cond / power

        return {
            "COP": cop,
            "Power": power,
            "Q_evap": q_evap,
            "Q_cond": q_cond,
        }