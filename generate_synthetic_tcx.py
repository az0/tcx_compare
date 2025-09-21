#!/usr/bin/env python3
"""
Synthetic TCX Generator
Generates realistic TCX files with heart rate data for testing TCX analysis tools.
Creates two devices with different characteristics measuring the same underlying heart rate.
"""

import argparse
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


class SyntheticTCXGenerator:
    """Generate synthetic TCX files with realistic heart rate data."""

    def __init__(self, seed=None):
        """Initialize the generator with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)

        # Device characteristics
        self.device_configs = {
            'device1': {
                'bias': random.uniform(-10, 10),  # Persistent bias in bpm
                # Standard deviation of noise
                'noise_std': random.uniform(1, 3),
                # Probability of gap
                'gap_probability': random.uniform(0.01, 0.05),
                'max_gap_seconds': random.randint(3, 30),  # Max gap duration
                # Duplicate timestamps
                'duplicate_probability': random.uniform(0.05, 0.15)
            },
            'device2': {
                'bias': random.uniform(-10, 10),  # Different bias
                'noise_std': random.uniform(1, 3),  # Different noise level
                'gap_probability': random.uniform(0.01, 0.05),
                'max_gap_seconds': random.randint(3, 30),
                'duplicate_probability': random.uniform(0.05, 0.15)
            }
        }

        # True heart rate parameters
        self.true_hr_min = 60
        self.true_hr_max = 180
        self.exercise_duration_minutes = 30
        self.sampling_rate = 1  # Hz

    def generate_true_heart_rate(self, duration_seconds):
        """Generate the underlying true heart rate time series."""
        true_hr = []
        timestamps = []

        start_time = datetime.now()

        for i in range(duration_seconds):
            current_time = start_time + timedelta(seconds=i)
            progress = i / duration_seconds

            # Base heart rate based on exercise phase
            if progress < 0.2:  # Warmup
                base_hr = self.true_hr_min + \
                    (self.true_hr_max - self.true_hr_min) * (progress / 0.2) * 0.5
            elif progress < 0.5:  # First half of exercise
                exercise_progress = (progress - 0.2) / 0.3
                base_hr = self.true_hr_min + \
                    (self.true_hr_max - self.true_hr_min) * \
                    (0.5 + 0.5 * exercise_progress)
            elif progress < 0.8:  # Second half of exercise
                exercise_progress = (progress - 0.5) / 0.3
                base_hr = self.true_hr_max - \
                    (self.true_hr_max - self.true_hr_min) * \
                    0.2 * exercise_progress
            else:  # Cooldown
                cooldown_progress = (progress - 0.8) / 0.2
                base_hr = self.true_hr_max * 0.8 - \
                    (self.true_hr_max * 0.8 - self.true_hr_min) * cooldown_progress

            # Add some natural variability
            variability = math.sin(i * 0.1) * 3 + math.sin(i * 0.05) * 2
            true_hr_value = base_hr + variability
            true_hr.append(max(self.true_hr_min, min(
                self.true_hr_max, true_hr_value)))
            timestamps.append(current_time)

        return timestamps, true_hr

    def generate_autocorrelated_noise(self, length, std_dev, correlation_factor=0.7):
        """Generate autocorrelated noise for realistic device behavior."""
        noise = [random.gauss(0, std_dev)]

        for _ in range(1, length):
            # Autocorrelated noise: current noise depends on previous noise
            new_noise = correlation_factor * \
                noise[-1] + random.gauss(0, std_dev *
                                         math.sqrt(1 - correlation_factor**2))
            noise.append(new_noise)

        return noise

    def generate_device_data(self, true_timestamps, true_hr, device_config):
        """Generate device-specific data with bias, noise, gaps, and duplicates."""
        device_timestamps = []
        device_hr = []

        noise = self.generate_autocorrelated_noise(
            len(true_hr), device_config['noise_std'])

        i = 0
        while i < len(true_timestamps):
            # Check for gap
            if random.random() < device_config['gap_probability']:
                gap_duration = random.randint(
                    1, device_config['max_gap_seconds'])
                i += gap_duration
                continue

            if i < len(true_timestamps):
                # Add device bias and noise
                true_value = true_hr[i]
                device_value = true_value + device_config['bias'] + noise[i]
                # Clamp to reasonable range
                device_value = max(40, min(220, device_value))

                device_timestamps.append(true_timestamps[i])
                device_hr.append(device_value)

                # Check for duplicate timestamp
                if random.random() < device_config['duplicate_probability']:
                    # Add slight variation to duplicate
                    duplicate_value = device_value + random.gauss(0, 1)
                    duplicate_value = max(40, min(220, duplicate_value))
                    device_timestamps.append(true_timestamps[i])
                    device_hr.append(duplicate_value)

                i += 1

        return device_timestamps, device_hr

    def generate_position_data(self, duration_seconds):
        """Generate realistic GPS position data."""
        positions = []
        start_lat = 38.9482
        start_lon = -104.7312

        # Simple running route
        for i in range(duration_seconds):
            # Gradual movement
            lat = start_lat + (i / 1000) * 0.001
            lon = start_lon + (i / 1000) * 0.001
            altitude = 2148 + random.uniform(-5, 5)
            distance = i * 2.5  # Approximate running pace

            positions.append({
                'latitude': lat,
                'longitude': lon,
                'altitude': altitude,
                'distance': distance
            })

        return positions

    def create_tcx_xml(self, device_name, timestamps, heart_rates, positions, start_time):
        """Create TCX XML structure."""
        # Create root TrainingCenterDatabase
        root = ET.Element('TrainingCenterDatabase')
        root.set(
            'xmlns', 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:schemaLocation',
                 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd')

        # Activities
        activities = ET.SubElement(root, 'Activities')
        activity = ET.SubElement(activities, 'Activity')
        activity.set('Sport', 'Running')

        # ID
        id_elem = ET.SubElement(activity, 'Id')
        id_elem.text = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Lap
        lap = ET.SubElement(activity, 'Lap')
        lap.set('StartTime', start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

        # Total Time
        total_time = ET.SubElement(lap, 'TotalTimeSeconds')
        total_time.text = str(len(timestamps))

        # Distance
        distance = ET.SubElement(lap, 'DistanceMeters')
        distance.text = str(positions[-1]['distance'] if positions else '0')

        # Calories (placeholder)
        calories = ET.SubElement(lap, 'Calories')
        calories.text = str(int(sum(heart_rates) / 10))

        # Track
        track = ET.SubElement(lap, 'Track')

        for i, (timestamp, hr) in enumerate(zip(timestamps, heart_rates)):
            trackpoint = ET.SubElement(track, 'Trackpoint')

            # Time
            time_elem = ET.SubElement(trackpoint, 'Time')
            time_elem.text = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

            # Position
            if i < len(positions):
                position = ET.SubElement(trackpoint, 'Position')
                lat = ET.SubElement(position, 'LatitudeDegrees')
                lat.text = str(positions[i]['latitude'])
                lon = ET.SubElement(position, 'LongitudeDegrees')
                lon.text = str(positions[i]['longitude'])

                # Altitude
                altitude = ET.SubElement(trackpoint, 'AltitudeMeters')
                altitude.text = str(positions[i]['altitude'])

                # Distance
                dist = ET.SubElement(trackpoint, 'DistanceMeters')
                dist.text = str(positions[i]['distance'])

            # Heart Rate
            hr_elem = ET.SubElement(trackpoint, 'HeartRateBpm')
            hr_value = ET.SubElement(hr_elem, 'Value')
            hr_value.text = str(int(round(hr)))

        # Creator
        creator = ET.SubElement(activity, 'Creator')
        creator.set('xsi:type', 'Device_t')
        name = ET.SubElement(creator, 'Name')
        name.text = device_name

        return root

    def save_tcx_file(self, xml_root, filename):
        """Save the TCX XML to a file."""
        # Pretty print the XML
        xml_str = minidom.parseString(
            ET.tostring(xml_root)).toprettyxml(indent="  ")

        # Remove empty lines
        lines = [line for line in xml_str.split('\n') if line.strip()]
        xml_str = '\n'.join(lines)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_str)

    def generate_files(self, output_dir="."):
        """Generate synthetic TCX files for two devices."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Generate true heart rate
        duration_seconds = self.exercise_duration_minutes * 60
        true_timestamps, true_hr = self.generate_true_heart_rate(
            duration_seconds)

        # Generate position data
        positions = self.generate_position_data(duration_seconds)

        # Generate device data
        device1_timestamps, device1_hr = self.generate_device_data(
            true_timestamps, true_hr, self.device_configs['device1'])

        device2_timestamps, device2_hr = self.generate_device_data(
            true_timestamps, true_hr, self.device_configs['device2'])

        # Create TCX files
        start_time = true_timestamps[0]

        # Device 1
        device1_xml = self.create_tcx_xml(
            "Synthetic Device 1", device1_timestamps, device1_hr, positions, start_time)
        self.save_tcx_file(device1_xml, output_dir / "synthetic_device1.tcx")

        # Device 2
        device2_xml = self.create_tcx_xml(
            "Synthetic Device 2", device2_timestamps, device2_hr, positions, start_time)
        self.save_tcx_file(device2_xml, output_dir / "synthetic_device2.tcx")

        # Print generation summary
        print("Generated synthetic TCX files:")
        print(
            f"  Device 1: {len(device1_hr)} records, bias: {self.device_configs['device1']['bias']:.1f} bpm")
        print(
            f"  Device 2: {len(device2_hr)} records, bias: {self.device_configs['device2']['bias']:.1f} bpm")
        print(
            f"  Average absolute difference: {sum(abs(a - b) for a, b in zip(device1_hr, device2_hr[:len(device1_hr)])) / min(len(device1_hr), len(device2_hr)):.1f} bpm")


def main():
    """Main function to generate synthetic TCX files."""

    parser = argparse.ArgumentParser(
        description='Generate synthetic TCX files with heart rate data')
    parser.add_argument('--seed', type=int,
                        help='Random seed for reproducibility')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='Output directory for generated files')
    args = parser.parse_args()

    generator = SyntheticTCXGenerator(seed=args.seed)
    generator.generate_files(output_dir=args.output_dir)


if __name__ == "__main__":
    main()
