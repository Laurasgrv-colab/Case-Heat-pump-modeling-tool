CONFIG = {
    # Refrigerant
    "fluid": "R134a",

    # Compressor
    "compressor_efficiency": 0.85,

    # Pressure drops
    "evaporator_pr": 0.98,
    "condenser_pr": 0.98,

    # Design conditions
    "heat_source_T_in": 40,
    "heat_source_T_out": 10,

    "heat_sink_T_in": 40,
    "heat_sink_T_out": 90,

    "heat_source_power": 1000e3,
    "heat_sink_power": 1012e3,

    # Initial refrigerant guesses
    "evap_pressure": 5,
    "cond_pressure": 18,

    # Save folder
    "design_path": "design_case.yaml",
}
