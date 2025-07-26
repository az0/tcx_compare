#!/usr/bin/env python3
"""
TCX Heart Rate Analysis Tool
Analyzes heart rate data from two TCX files recorded simultaneously by different devices.
"""

# standard import
from pathlib import Path
import sys

# third-party import
import pandas as pd
import matplotlib.pyplot as plt
from tcxreader.tcxreader import TCXReader


class TCXHeartRateAnalyzer:
    """TCX Heart Rate Analyzer"""

    def __init__(self):
        """Initialize the analyzer."""
        self.tcx_reader = TCXReader()
        self.device1_name = None
        self.device2_name = None
        self.device1_data = None
        self.device2_data = None

    def read_tcx_file(self, file_path):
        """Read a TCX file and extract heart rate data with timestamps."""
        try:
            # Read TCX file with only_gps=False to include all trackpoints with heart rate data
            # even if they don't have GPS coordinates
            tcx_data = self.tcx_reader.read(file_path, only_gps=False)

            # Extract trackpoints with heart rate data
            heart_rate_data = []

            # tcxreader returns a TCXExercise object with laps attribute
            for lap in tcx_data.laps:
                for trackpoint in lap.trackpoints:
                    if hasattr(trackpoint, 'hr_value') and trackpoint.hr_value is not None:
                        heart_rate_data.append({
                            'timestamp': trackpoint.time,
                            'heart_rate': trackpoint.hr_value,
                            'latitude': getattr(trackpoint, 'latitude', None),
                            'longitude': getattr(trackpoint, 'longitude', None),
                            'altitude': getattr(trackpoint, 'altitude', None),
                            'distance': getattr(trackpoint, 'distance', None)
                        })

            # Convert to DataFrame and handle duplicate timestamps
            df = pd.DataFrame(heart_rate_data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')

                # Handle duplicate timestamps by averaging heart rate
                df = df.groupby('timestamp').agg({
                    'heart_rate': 'mean',
                    'latitude': 'first',
                    'longitude': 'first',
                    'altitude': 'first',
                    'distance': 'first'
                }).reset_index()

            return df

        except Exception as e:
            print(f"Error reading TCX file {file_path}: {e}")
            return pd.DataFrame()

    def load_files(self, file1_path, file2_path):
        """Load and process both TCX files."""
        self.device1_name = Path(file1_path).stem
        self.device2_name = Path(file2_path).stem

        print("Loading TCX files...")
        self.device1_data = self.read_tcx_file(file1_path)
        self.device2_data = self.read_tcx_file(file2_path)

        print(f"{self.device1_name}: {len(self.device1_data)} heart rate records")
        print(f"{self.device2_name}: {len(self.device2_data)} heart rate records")

    def plot_heart_rates(self):
        """Plot heart rate data from both devices and their difference."""
        if self.device1_data.empty or self.device2_data.empty:
            print("No data to plot")
            return

        # Create subplots for heart rates and difference with 16:9 aspect ratio
        _, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

        # Plot 1: Heart rate comparison
        if not self.device1_data.empty:
            ax1.plot(self.device1_data['timestamp'],
                     self.device1_data['heart_rate'],
                     label=self.device1_name, alpha=0.8)
        if not self.device2_data.empty:
            ax1.plot(self.device2_data['timestamp'],
                     self.device2_data['heart_rate'],
                     label=self.device2_name, alpha=0.8)
        ax1.set_ylabel('Heart Rate (bpm)')
        ax1.set_title('Heart Rate Comparison')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=0)

        # Plot 2: Heart rate difference over time
        diff_data = self.calculate_differences()
        if not diff_data.empty:
            ax2.plot(diff_data['timestamp'],
                     diff_data['heart_rate_difference'],
                     color='red', alpha=0.7, linewidth=1)
            ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax2.set_ylabel('Difference (bpm)')
            ax2.set_xlabel('Time')
            ax2.set_title(f'Heart Rate Difference ({self.device1_name} - {self.device2_name})')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig('heart_rate_analysis.png', dpi=300)

    def calculate_differences(self):
        """Calculate heart rate differences between devices at matching timestamps."""
        if self.device1_data.empty or self.device2_data.empty:
            return pd.DataFrame()

        # Merge dataframes on timestamp
        merged = pd.merge(
            self.device1_data[['timestamp', 'heart_rate']],
            self.device2_data[['timestamp', 'heart_rate']],
            on='timestamp',
            suffixes=('_device1', '_device2')
        )

        if merged.empty:
            print("No matching timestamps found between devices")
            return pd.DataFrame()

        # Calculate difference
        merged['heart_rate_difference'] = (
            merged['heart_rate_device1'] - merged['heart_rate_device2']
        )

        return merged

    def calculate_summary_statistics(self):
        """Calculate summary statistics for each device and their differences."""
        stats = {}

        # Device 1 stats
        if not self.device1_data.empty:
            stats['device1'] = {
                'min_hr': float(self.device1_data['heart_rate'].min()),
                'avg_hr': float(self.device1_data['heart_rate'].mean()),
                'max_hr': float(self.device1_data['heart_rate'].max()),
                'count': int(len(self.device1_data))
            }

        # Device 2 stats
        if not self.device2_data.empty:
            stats['device2'] = {
                'min_hr': float(self.device2_data['heart_rate'].min()),
                'avg_hr': float(self.device2_data['heart_rate'].mean()),
                'max_hr': float(self.device2_data['heart_rate'].max()),
                'count': int(len(self.device2_data))
            }

        # Difference stats
        diff_data = self.calculate_differences()
        if not diff_data.empty:
            stats['difference'] = {
                'min_diff': float(diff_data['heart_rate_difference'].min()),
                'avg_diff': float(diff_data['heart_rate_difference'].mean()),
                'max_diff': float(diff_data['heart_rate_difference'].max()),
                'abs_avg_diff': float(diff_data['heart_rate_difference'].abs().mean()),
                'count': int(len(diff_data))
            }

        return stats

    def print_summary(self):
        """Print summary statistics."""
        stats = self.calculate_summary_statistics()

        if not stats:
            print("No data available for summary")
            return

        print("\n" + "="*50)
        print("SUMMARY STATISTICS")
        print("="*50)

        if 'device1' in stats:
            print(f"\n{self.device1_name}:")
            print(f"  Min HR: {stats['device1']['min_hr']:.1f} bpm")
            print(f"  Avg HR: {stats['device1']['avg_hr']:.1f} bpm")
            print(f"  Max HR: {stats['device1']['max_hr']:.1f} bpm")
            print(f"  Records: {stats['device1']['count']}")

        if 'device2' in stats:
            print(f"\n{self.device2_name}:")
            print(f"  Min HR: {stats['device2']['min_hr']:.1f} bpm")
            print(f"  Avg HR: {stats['device2']['avg_hr']:.1f} bpm")
            print(f"  Max HR: {stats['device2']['max_hr']:.1f} bpm")
            print(f"  Records: {stats['device2']['count']}")

        if 'difference' in stats:
            print(f"\nDifference ({self.device1_name} - {self.device2_name}):")
            print(f"  Min Difference: {stats['difference']['min_diff']:.1f} bpm")
            print(f"  Avg Difference: {stats['difference']['avg_diff']:.1f} bpm")
            print(f"  Max Difference: {stats['difference']['max_diff']:.1f} bpm")
            print(f"  Avg Absolute Difference: {stats['difference']['abs_avg_diff']:.1f} bpm")
            print(f"  Matching timestamps: {stats['difference']['count']}")


def main():
    """Main function to run the analysis."""
    if len(sys.argv) != 3:
        print("Usage: python analyze.py <tcx_file1> <tcx_file2>")
        return

    tcx_files = [Path(sys.argv[1]), Path(sys.argv[2])]
    print(f"Using TCX files: {tcx_files}")

    # Initialize analyzer
    analyzer = TCXHeartRateAnalyzer()

    # Load and analyze files
    analyzer.load_files(str(tcx_files[0]), str(tcx_files[1]))

    # Plot heart rates
    analyzer.plot_heart_rates()

    # Print summary
    analyzer.print_summary()


if __name__ == "__main__":
    main()
