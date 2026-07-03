import matplotlib.pyplot as plt


class HeatPumpPlotter:
    def __init__(self, results):
        self.results = results

    def plot_cop(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.results["COP"])
        plt.title("Coefficient of Performance")
        plt.xlabel("Time step")
        plt.ylabel("COP")
        plt.grid(True)
        plt.tight_layout()

    def plot_power(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.results["Power"] / 1000)
        plt.title("Compressor Power")
        plt.xlabel("Time step")
        plt.ylabel("Power [kW]")
        plt.grid(True)
        plt.tight_layout()

    def plot_heat_transfer(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.results["Q_evap"] / 1000, label="Evaporator")
        plt.plot(self.results["Q_cond"] / 1000, label="Condenser")
        plt.legend()
        plt.xlabel("Time step")
        plt.ylabel("Heat Transfer [kW]")
        plt.grid(True)
        plt.tight_layout()

    def plot_all(self):
        self.plot_cop()
        self.plot_power()
        self.plot_heat_transfer()
        plt.show()
