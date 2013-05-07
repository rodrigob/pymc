"""Utility functions for PyMC"""

import numpy as np

def make_indices(dimensions):
    # Generates complete set of indices for given dimensions

    level = len(dimensions)

    if level==1: return range(dimensions[0])

    indices = [[]]

    while level:

        _indices = []

        for j in range(dimensions[level-1]):

            _indices += [[j]+i for i in indices]

        indices = _indices

        level -= 1

    try:
        return [tuple(i) for i in indices]
    except TypeError:
        return indices

def calc_min_interval(x, alpha):
    """Internal method to determine the minimum interval of
    a given width

    Assumes that x is sorted numpy array.
    """

    n = len(x)
    cred_mass = 1.0-alpha

    interval_idx_inc = int(np.floor( cred_mass*n ))
    n_intervals = n - interval_idx_inc
    interval_width = x[interval_idx_inc:] - x[:n_intervals]

    if len(interval_width)==0:
        raise ValueError('Too few elements for interval calculation')

    min_idx = np.argmin(interval_width)
    hdi_min = x[min_idx]
    hdi_max = x[min_idx+interval_idx_inc]
    return hdi_min, hdi_max

def hpd(x, alpha):
    """Calculate highest posterior density (HPD) of array for given alpha. The HPD is the
    minimum width Bayesian credible interval (BCI).

    :Arguments:
      x : Numpy array
          An array containing MCMC samples
      alpha : float
          Desired probability of type I error

    """

    # Make a copy of trace
    x = x.copy()

    # For multivariate node
    if x.ndim>1:

        # Transpose first, then sort
        tx = np.transpose(x, range(x.ndim)[1:]+[0])
        dims = np.shape(tx)

        # Container list for intervals
        intervals = np.resize(0.0, dims[:-1]+(2,))

        for index in make_indices(dims[:-1]):

            try:
                index = tuple(index)
            except TypeError:
                pass

            # Sort trace
            sx = np.sort(tx[index])

            # Append to list
            intervals[index] = calc_min_interval(sx, alpha)

        # Transpose back before returning
        return np.array(intervals)

    else:
        # Sort univariate node
        sx = np.sort(x)

        return np.array(calc_min_interval(sx, alpha))


def batchsd(trace, batches=5):
    """
    Calculates the simulation standard error, accounting for non-independent
    samples. The trace is divided into batches, and the standard deviation of
    the batch means is calculated.
    """

    if len(np.shape(trace)) > 1:

        dims = np.shape(trace)
        #ttrace = np.transpose(np.reshape(trace, (dims[0], sum(dims[1:]))))
        ttrace = np.transpose([t.ravel() for t in trace])

        return np.reshape([batchsd(t, batches) for t in ttrace], dims[1:])

    else:
        if batches == 1: return np.std(trace)/np.sqrt(len(trace))

        try:
            batched_traces = np.resize(trace, (batches, len(trace)/batches))
        except ValueError:
            # If batches do not divide evenly, trim excess samples
            resid = len(trace) % batches
            batched_traces = np.resize(trace[:-resid], (batches, len(trace)/batches))

        means = np.mean(batched_traces, 1)

        return np.std(means)/np.sqrt(batches)

def calc_quantiles(x, qlist=(2.5, 25, 50, 75, 97.5)):
    """Returns a dictionary of requested quantiles from array

    :Arguments:
      x : Numpy array
          An array containing MCMC samples
      qlist : tuple or list
          A list of desired quantiles (defaults to (2.5, 25, 50, 75, 97.5))

    """

    # Make a copy of trace
    x = x.copy()

    # For multivariate node
    if x.ndim>1:
        # Transpose first, then sort, then transpose back
        sx = np.sort(x.T).T
    else:
        # Sort univariate node
        sx = np.sort(x)

    try:
        # Generate specified quantiles
        quants = [sx[int(len(sx)*q/100.0)] for q in qlist]

        return dict(zip(qlist, quants))

    except IndexError:
        print("Too few elements for quantile calculation")