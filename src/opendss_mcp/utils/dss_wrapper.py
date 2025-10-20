"""
OpenDSS circuit wrapper module.

This module provides a high-level interface to OpenDSS functionality through the
opendssdirect.py package, with proper error handling and type hints.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union

import opendssdirect as dss

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DSSCircuit:
    """A wrapper class for OpenDSS circuit operations with error handling.

    This class provides a more Pythonic interface to OpenDSS functionality,
    with proper error handling and type hints. It maintains state about the
    currently loaded circuit and provides methods for common operations.
    """

    def __init__(self) -> None:
        """Initialize the DSSCircuit wrapper."""
        self.current_feeder: Optional[str] = None
        self.dss_file_path: Optional[str] = None
        self._initialized = False
        try:
            # Initialize OpenDSS
            if not dss.Basic.NumCircuits() > 0:
                dss.Text.Command("Clear")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize OpenDSS: {e}")
            self._initialized = False

    def reset(self) -> bool:
        """Reset the circuit by clearing the current circuit.

        Returns:
            bool: True if reset was successful, False otherwise.
        """
        try:
            dss.run_command("Clear")
            self.current_feeder = None
            self.dss_file_path = None
            return True
        except Exception as e:
            logger.error(f"Failed to reset circuit: {e}")
            return False

    def load_dss_file(self, file_path: str) -> bool:
        """Load a DSS script file.

        Args:
            file_path: Path to the DSS script file to load.

        Returns:
            bool: True if file was loaded successfully, False otherwise.
        """
        try:
            dss.Text.Command(f"compile {file_path}")
            self.dss_file_path = file_path
            self.current_feeder = (
                file_path.stem
                if hasattr(file_path, "stem")
                else file_path.split("/")[-1].split(".")[0]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load DSS file {file_path}: {e}")
            return False

    def solve_power_flow(self) -> bool:
        """Solve the power flow for the current circuit.

        Returns:
            bool: True if solution converged, False otherwise.
        """
        try:
            dss.Solution.Solve()
            if dss.Solution.Converged():
                return True
            logger.warning("Power flow solution did not converge")
            return False
        except Exception as e:
            logger.error(f"Error solving power flow: {e}")
            return False

    def get_all_bus_voltages(self) -> Dict[str, float]:
        """Get voltage magnitudes in per-unit for all buses.

        Returns:
            dict: Dictionary mapping bus names to their voltage magnitudes (p.u.)
        """
        voltages = {}
        try:
            dss.Circuit.SetActiveElement("Vsource.source")
            dss.Circuit.Solution.Solve()

            dss.Circuit.SetActiveBus("*")
            bus_names = dss.Bus.AllBusNames()

            for bus in bus_names:
                dss.Circuit.SetActiveBus(bus)
                pu_voltages = dss.Bus.puVmagAngle()
                # Take the maximum phase voltage as the bus voltage
                if pu_voltages:
                    voltages[bus] = max(pu_voltages[0::2])

            return voltages
        except Exception as e:
            logger.error(f"Error getting bus voltages: {e}")
            return {}

    def get_all_line_flows(self) -> Dict[str, Dict[str, float]]:
        """Get power flows for all lines in the circuit.

        Returns:
            dict: Dictionary mapping line names to their power flow information
                with keys: 'P' (kW), 'Q' (kvar), 'loading' (%)
        """
        line_flows = {}
        try:
            dss.Circuit.SetActiveClass("Line")
            dss.ActiveClass.First()

            for _ in range(dss.ActiveClass.Count()):
                line_name = dss.Circuit.ActiveCktElement.Name()
                powers = dss.CktElement.Powers()

                # Sum P and Q for all phases
                p_total = sum(abs(p) for p in powers[::2])  # Real power (kW)
                q_total = sum(abs(q) for q in powers[1::2])  # Reactive power (kvar)

                # Get line loading percentage
                dss.Circuit.SetActiveElement(line_name)
                loading = dss.CktElement.NormalAmps()
                current = max(dss.CktElement.CurrentsMagAng()[::2])
                loading_pct = (current / loading * 100) if loading > 0 else 0

                line_flows[line_name] = {
                    "P": p_total,
                    "Q": q_total,
                    "loading": loading_pct,
                }

                dss.ActiveClass.Next()

            return line_flows
        except Exception as e:
            logger.error(f"Error getting line flows: {e}")
            return {}

    def get_total_losses(self) -> Tuple[float, float]:
        """Get total losses in the circuit.

        Returns:
            tuple: (total_losses_kw, total_losses_kvar)
        """
        try:
            return dss.Circuit.Losses()
        except Exception as e:
            logger.error(f"Error getting total losses: {e}")
            return 0.0, 0.0

    def get_bus_names(self) -> List[str]:
        """Get all bus names in the circuit.

        Returns:
            list: List of bus names
        """
        try:
            dss.Circuit.SetActiveBus("*")
            return dss.Bus.AllBusNames()
        except Exception as e:
            logger.error(f"Error getting bus names: {e}")
            return []

    def get_line_names(self) -> List[str]:
        """Get all line names in the circuit.

        Returns:
            list: List of line names
        """
        try:
            line_names = []
            dss.Circuit.SetActiveClass("Line")
            dss.ActiveClass.First()

            for _ in range(dss.ActiveClass.Count()):
                line_names.append(dss.Circuit.ActiveCktElement.Name())
                dss.ActiveClass.Next()

            return line_names
        except Exception as e:
            logger.error(f"Error getting line names: {e}")
            return []

    def is_initialized(self) -> bool:
        """Check if the circuit is properly initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized
