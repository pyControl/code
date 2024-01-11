# Class for converting timestamps between recording systems using sync pulses with
# random inter-pulse intervals.
# https://pycontrol.readthedocs.io/en/latest/user-guide/synchronisation
# Dependencies:  Python 3, Numpy, Matplotlib, Scikit-learn.
# (c) Thomas Akam 2018-2023. Released under the GPL-3 open source licence.

import numpy as np
import pylab as plt
from sklearn.mixture import GaussianMixture


class RsyncError(Exception):
    pass


class Rsync_aligner:
    def __init__(
        self,
        pulse_times_A,
        pulse_times_B,
        units_A="auto",
        units_B="auto",
        chunk_size=5,
        plot=False,
        raise_exception=True,
    ):
        """Class for converting timestamps between two recording systems
        (e.g  pyControl and an ephys) using sync pulses with random inter-pulse
        intervals recorded on both systems.  Typically these sync pulses are generated
        by pyControl using the Rsync hardware object and sent to other systems. To use the
        Rsync_aligner,instantiate it by providing the sync pulse times recorded by each
        system. Timestamps from either system can then be converted into the reference frame
        of the other using the A_to_B and B_to_A methods.  If the hardware systems use
        different units to measure time this can either be specified manually using the units
        arguments when the aligner is instantiated, or estimated automatically by setting
        the units arguments to 'auto'. When the aligner is instantiated it works out
        which pulses in each reference frame correspond to each other by by aligning
        short chunks of pulse sequence A with B by minimising the mean squared error
        between inter-pulse intervals.

        Arguments:

        pulse_times_A: The times when sync pulses occured recorded by hardware system A.

        pulse_times_B: The times when sync pulses occured recorded by hardware system B.

        units_A: The time units used by system A expressed in milliseconds.  E.g. if
                 system A uses units of seconds the *units_A* argument is 1000. If either
                 of the units_A or units_B arguments is set to 'auto' the units of B
                 relative to A are estimated automatically.

        units_B: The time units used by system B expressed in milliseconds.

        plot: Whether to plot information about the alignment.

        raise_exception: If *True* an RsyncError exception is raised if no match is found
                         between the sync pulse sequences.

        """
        if units_A == "auto" or units_B == "auto":
            # Estimate the units of B relative to A automatically.
            raw_intervals_A = np.diff(pulse_times_A)
            raw_intervals_B = np.diff(pulse_times_B)
            # Exclude very long intervals as likely due to missing pulses.
            good_intervals_A = raw_intervals_A[raw_intervals_A < 3 * np.median(raw_intervals_A)]
            good_intervals_B = raw_intervals_B[raw_intervals_B < 3 * np.median(raw_intervals_B)]
            # Estimate units of B relative to A using the mean of the good intervals.
            units_A = 1
            units_B = np.mean(good_intervals_A) / np.mean(good_intervals_B)
        # Evalute inter-pulse intervals in common units.
        intervals_A = np.diff(pulse_times_A) * units_A  # Inter-pulse intervals for sequence A
        intervals_B = np.diff(pulse_times_B) * units_B  # Inter-pulse intervals for sequence B
        intervals_B2 = intervals_B**2
        # Find alignments of chunks which minimise sum of squared errors.
        chunk_starts_A = np.arange(
            0, len(pulse_times_A) - chunk_size, chunk_size
        )  # Start indices of each chunk of sequence A.
        chunk_starts_B = np.zeros(chunk_starts_A.shape, int)  # Start indicies of corresponding chunks in B.
        chunk_min_mse = np.zeros(chunk_starts_A.shape)  # Mean squared error for each chunks best alignment.
        chunk_2nd_mse = np.zeros(chunk_starts_A.shape)  # Mean sqared error for each chunks 2nd best alignment.
        ones_chunk = np.ones(chunk_size)
        for i, csA in enumerate(chunk_starts_A):
            chunk_A = intervals_A[csA : csA + chunk_size]
            mse = (
                np.correlate(intervals_B2, ones_chunk, mode="valid")
                + np.sum(chunk_A**2)
                - 2 * np.correlate(intervals_B, chunk_A, mode="valid")
            ) / chunk_size
            chunk_starts_B[i] = np.argmin(mse)
            sorted_chunk_min_mse = np.sort(mse)
            chunk_min_mse[i] = sorted_chunk_min_mse[0]
            chunk_2nd_mse[i] = sorted_chunk_min_mse[1]
        # Assign chunks to matched and non-matched groups by fitting 2 component Gaussian mixture model
        # to log mse distribition of best + second best alignments.
        chunk_mse = np.hstack([chunk_min_mse, chunk_2nd_mse])
        chunk_mse[chunk_mse == 0] = np.min(chunk_mse[chunk_mse != 0])  # Replace zeros with smallest non zero value.
        log_mse = np.log(chunk_mse)
        log_mse = log_mse[np.isfinite(log_mse)].reshape(-1, 1)
        gmm = GaussianMixture(n_components=2, covariance_type="spherical")
        gmm.fit(log_mse)
        valid_matches = gmm.predict(log_mse) == np.argmin(gmm.means_)  # True for chunks which are valid matches.
        # Make arrays of corresponding times.
        cor_times_A = np.full(pulse_times_B.shape, np.nan)  # A pulse times corresponding to each B pulse.
        cor_times_B = np.full(pulse_times_A.shape, np.nan)  # B pulse times corresponding to each A pulse.
        for csA, csB, valid in zip(chunk_starts_A, chunk_starts_B, valid_matches):
            if valid:
                cor_times_A[csB : csB + chunk_size] = pulse_times_A[csA : csA + chunk_size]
                cor_times_B[csA : csA + chunk_size] = pulse_times_B[csB : csB + chunk_size]
        # Store pulse times, their correspondences and units.
        self.pulse_times_A = pulse_times_A
        self.pulse_times_B = pulse_times_B
        self.cor_times_A = cor_times_A
        self.cor_times_B = cor_times_B
        self.units_A = units_A
        self.units_B = units_B
        # Compute variables used for extrapolating beyond first/last matching pulse.
        diff_cor_times_B = np.diff(cor_times_B)
        self.dAdB = np.sum(np.diff(pulse_times_A)[~np.isnan(diff_cor_times_B)]) / np.sum(
            diff_cor_times_B[~np.isnan(diff_cor_times_B)]
        )  # Empirical units_A/units_B from matched inter-pulse intervals.
        matched_pulse_times_A = cor_times_A[~np.isnan(cor_times_A)]
        matched_pulse_times_B = cor_times_B[~np.isnan(cor_times_B)]
        self.first_matched_time_A = matched_pulse_times_A[0]
        self.last_matched_time_A = matched_pulse_times_A[-1]
        self.first_matched_time_B = matched_pulse_times_B[0]
        self.last_matched_time_B = matched_pulse_times_B[-1]
        # Check quality of alignment.
        separation_OK = np.abs(gmm.means_[0] - gmm.means_[1])[0] > 3 * np.sum(
            np.sqrt(gmm.covariances_)
        )  # Difference in GMM means > 3 x sum of standard deviations.
        order_OK = (np.nanmin(np.diff(cor_times_A)) > 0) and (
            np.nanmin(np.diff(cor_times_A)) > 0
        )  # Corresponding times are monotonically increacing.
        if not (separation_OK and order_OK):
            if raise_exception:
                raise RsyncError("No match found between inter-pulse interval sequences.")
            else:
                print("Rsync warning: No match found between inter-pulse interval sequences.")
        # Plotting
        if plot:
            plt.figure(plot if isinstance(plot, int) else 1, figsize=[7, 9]).clf()
            plt.subplot2grid((3, 3), (0, 0), rowspan=1, colspan=2)
            plt.hist(log_mse[valid_matches], 20, color="b", label="Match")
            plt.hist(log_mse[~valid_matches], 20, color="r", label="Non-match")
            plt.legend(loc="upper center")
            plt.xlabel("Log mean squared error")
            plt.ylabel("# chunks")
            plt.subplot2grid((3, 3), (0, 2), rowspan=1, colspan=1)
            timing_errors = np.diff(cor_times_A) - np.diff(pulse_times_B)
            plt.hist(timing_errors[~np.isnan(timing_errors)], 100)
            plt.yscale("log", nonpositive="clip")
            plt.xlabel("Inter-pulse interval\ndiscrepancy (ms)")
            plt.ylabel("# pulses")
            plt.subplot2grid((3, 1), (1, 0), rowspan=2, colspan=1)
            plt.plot(pulse_times_A, cor_times_B, ".", markersize=2)
            plt.xlim(pulse_times_A[0], pulse_times_A[-1])
            plt.xlabel("pulse times A")
            plt.ylabel("pulse times B")
            plt.tight_layout()

    def A_to_B(self, times_A, extrapolate=True):
        """Convert times in A reference frame to B reference frame.  If extrapolate=True, times
        before the first matched sync pulse and after the last matched sync pulse will be
        extrapolated, if False they will be nans.
        """
        times_B = np.interp(times_A, self.pulse_times_A, self.cor_times_B, left=np.nan, right=np.nan)
        if extrapolate:
            pf = times_A < self.first_matched_time_A  # Mask indicating times pre first matched pulse.
            times_B[pf] = (times_A[pf] - self.first_matched_time_A) / self.dAdB + self.first_matched_time_B
            pl = times_A > self.last_matched_time_A  # Mask indicating times post last matched pulse.
            times_B[pl] = (times_A[pl] - self.last_matched_time_A) / self.dAdB + self.last_matched_time_B
        return times_B

    def B_to_A(self, times_B, extrapolate=True):
        """Convert times in B reference frame to A reference frame. If extrapolate=True, times
        before the first matched sync pulse and after the last matched sync pulse will be
        extrapolated, if False they will be nans.
        """
        times_A = np.interp(times_B, self.pulse_times_B, self.cor_times_A, left=np.nan, right=np.nan)
        if extrapolate:
            pf = times_B < self.first_matched_time_B  # Mask indicating times pre first matched pulse.
            times_A[pf] = (times_B[pf] - self.first_matched_time_B) * self.dAdB + self.first_matched_time_A
            pl = times_B > self.last_matched_time_B  # Mask indicating times post last matched pulse.
            times_A[pl] = (times_B[pl] - self.last_matched_time_B) * self.dAdB + self.last_matched_time_A
        return times_A


# --------------------------------------------------------------------------


def simulate_pulses(n_pulse=1000, interval=[100, 1900], units_B=2, noise_SD=2, missing_pulses=False):
    """Simulate a pair of pulse trains timestamps with drift between their timings."""
    pulse_times_A = np.cumsum(np.random.randint(*interval, size=n_pulse)).astype(float)
    pulse_times_B = units_B * (pulse_times_A + np.cumsum(np.random.normal(scale=noise_SD, size=n_pulse)))
    if missing_pulses:
        pulse_times_A = np.hstack(
            [
                pulse_times_A[int(n_pulse * 0.05) : int(n_pulse * 0.21)],
                pulse_times_A[int(n_pulse * 0.33) :] + 2e5,
            ]
        )
        pulse_times_B = np.hstack(
            [
                pulse_times_B[: int(n_pulse * 0.74)],
                pulse_times_B[int(n_pulse * 0.85) : int(n_pulse * 0.95)],
            ]
        )
    return pulse_times_A, pulse_times_B
