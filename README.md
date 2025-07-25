# TCX Heart Rate Analysis Project

This project analyzes heart rate data from two TCX files recorded simultaneously by different devices on the same person.

* Data Processing: Duplicate timestamps are handled by averaging heart rate values
* Missing Data: Records without heart rate data are ignored
* Time Alignment: Data is matched by exact timestamps between devices
* Visualization: Matplotlib is used for plotting heart rates for each device and also a difference between them
* Summary statistics: Shows range and average for each device and also for the difference between them

See the [sample directory/output.md](sample/output.md) for example output.

## Synthetic TCX Files Generation

A separate script `synthetic_tcx_generator.py` generates a pair of synthetic TCX files as a simulation of an imperfect measurement of a true time series with realistic characteristics:

* Realistic exercise progression (warmup, exercise, cooldown)
* Device-specific persistent bias
* Autocorrelated noise (Ornstein–Uhlenbeck process)
* Occasional sensor gaps
* Duplicate timestamps with slight variations (seen in real data, probably because of rounding timestamps)

## How to Run

### Full run

This will generate synthetic .tcx files and analyze them.

```bash
./run_analysis.sh
```

### Custom TCX Analysis

Install dependencies 

```bash
pip install -r requirements.txt
```

Run the analysis script:

```bash
python analyze.py file1.tcx file2.tcx
```

This will output a .png file with a comparison of the heart rate data from the two files.
It also prints summary statistics to the console.


## Dependencies

- [tcxreader](https://github.com/alenrajsp/tcxreader): TCX file parsing
- pandas: Data manipulation and analysis
- matplotlib: Plotting and visualization
- numpy: Numerical computations

# Related tools

* [hrcomparison](https://github.com/andgineer/hrcomparison): Python tool to generate a time series of two heart rates given TCX, GPX, or FIT files
* [The GPS tracks reader](https://mygpsfiles.com/app/): Web app to view view multiple GPX and TCX files together on OpenStreetMap