"""
Test data sets for Borealis Bfiq.
"""

from collections import OrderedDict
from numpy import array, int16, float32, zeros

borealis_bfiq_data = [OrderedDict([(1558583991060, {
	"borealis_git_hash" : 'v0.2-61-gc13ab34', 
	"timestamp_of_write" : 1558583994.245457, 
	"experiment_id" : 100000000,
    "experiment_name" : 'TestScheme9ACFs', 
    "experiment_comment" : '', 
    "num_slices" : 1, 
    "slice_comment" : '', 
    "station" : 'sas',
    "num_sequences" : 29, 
    "pulse_phase_offset" : array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    "range_sep" : 44.96887, 
    "first_range_rtt" : 1200.8307, 
    "first_range" : 180.0, 
    "rx_sample_rate" : 3333.3333333333335,
    "scan_start_marker" : True, 
    "int_time" : 3.000395, 
    "tx_pulse_len" : 300, 
    "tau_spacing" : 2400, 
    "main_antenna_count" : 16, 
    "intf_antenna_count" : 4, 
    "freq" : 10500, 
    "samples_data_type" : 'complex float', 
    "num_samps" : 297,
    "num_ranges" : 75,
    "pulses" : array([0, 9, 12, 20, 22, 26, 27]), 
    "lags" : array([[ 0  0],
					[26, 27],
					[20, 22],
					[9, 12],
					[22, 26],
					[22, 27],
					[20, 26],
					[20, 27],
					[12, 20],
					[0, 9],
					[12, 22],
					[9, 20],
					[0, 12],
					[9, 22],
					[12, 26],
					[12, 27],
					[9, 26],
					[9, 27],
					[0, 20],
					[0, 22],
					[0, 26],
					[0, 27],
					[27, 27]]),
    "blanked_samples" : array([0, 72, 96, 160, 176, 208, 216]), 
    "sqn_timestamps" : array([1.55858399e+09, 1.55858399e+09,
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09]), 
    "beam_nums" : [0], 
    "beam_azms" : [0.0], 
    "data_descriptors" : ['num_antenna_arrays', 'num_sequences', 'num_beams', 'num_samps'], 
    "data_dimensions" : [2, 29, 1, 297], 
    "antenna_arrays_order" : ['main', 'intf'],
    "noise_at_freq" : [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.], 
    "data_normalization_factor" : 9999999.999999996,
    "data" : zeros(17226)
	}), 
    (1558583994062, {
	"borealis_git_hash" : 'v0.2-61-gc13ab34', 
	"timestamp_of_write" : 1558583997.340992, 
	"experiment_id" : 100000000,
    "experiment_name" : 'TestScheme9ACFs', 
    "experiment_comment" : '', 
    "num_slices" : 1, 
    "slice_comment" : '', 
    "station" : 'sas',
    "num_sequences" : 30, 
    "pulse_phase_offset" : array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    "range_sep" : 44.96887, 
    "first_range_rtt" : 1200.8307, 
    "first_range" : 180.0, 
    "rx_sample_rate" : 3333.3333333333335,
    "scan_start_marker" : True, 
    "int_time" : 3.090798, 
    "tx_pulse_len" : 300, 
    "tau_spacing" : 2400, 
    "main_antenna_count" : 16, 
    "intf_antenna_count" : 4, 
    "freq" : 10500, 
    "samples_data_type" : 'complex float', 
    "num_samps" : 297,
    "num_ranges" : 75,
    "pulses" : array([0, 9, 12, 20, 22, 26, 27]), 
    "lags" : array([[ 0  0],
					[26, 27],
					[20, 22],
					[9, 12],
					[22, 26],
					[22, 27],
					[20, 26],
					[20, 27],
					[12, 20],
					[0, 9],
					[12, 22],
					[9, 20],
					[0, 12],
					[9, 22],
					[12, 26],
					[12, 27],
					[9, 26],
					[9, 27],
					[0, 20],
					[0, 22],
					[0, 26],
					[0, 27],
					[27, 27]]),
    "blanked_samples" : array([0, 72, 96, 160, 176, 208, 216]), 
    "sqn_timestamps" : array([1.55858399e+09, 1.55858399e+09,
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 1.55858399e+09, 
    1.55858399e+09, 1.55858399e+09, 1.55858399e+09]), 
    "beam_nums" : [0], 
    "beam_azms" : [0.0], 
    "data_descriptors" : ['num_antenna_arrays', 'num_sequences', 'num_beams', 'num_samps'], 
    "data_dimensions" : [2, 29, 1, 297], 
    "antenna_arrays_order" : ['main', 'intf'],
    "noise_at_freq" : [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.], 
    "data_normalization_factor" : 9999999.999999996,
    "data" : zeros(17820)
	})])]
