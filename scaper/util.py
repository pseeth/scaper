# CREATED: 10/14/16 12:35 PM by Justin Salamon <justin.salamon@nyu.edu>
'''
Utility functions
=================
'''

from contextlib import contextmanager
import logging
import os
import glob
from .scaper_exceptions import ScaperError
import scipy
import numpy as np


@contextmanager
def _close_temp_files(tmpfiles):
    '''
    Utility function for creating a context and closing all temporary files
    once the context is exited. For correct functionality, all temporary file
    handles created inside the context must be appended to the ```tmpfiles```
    list.

    Parameters
    ----------
    tmpfiles : list
        List of temporary file handles

    '''
    yield
    for t in tmpfiles:
        t.close()


@contextmanager
def _set_temp_logging_level(level):
    '''
    Utility function for temporarily changing the logging level using contexts.

    Parameters
    ----------
    level : str or int
        The desired temporary logging level. For allowed values see:
        https://docs.python.org/2/library/logging.html#logging-levels

    '''
    logger = logging.getLogger()
    current_level = logger.level
    logger.setLevel(level)
    yield
    logger.setLevel(current_level)


def _get_sorted_files(folder_path):
    '''
    Return a list of absolute paths to all valid files contained within the
    folder specified by ```folder_path```.

    Parameters
    ----------
    folder_path : str
        Path to the folder to scan for files.

    Returns
    -------
    files : list
        List of absolute paths to all valid files contained within
        ```folder_path```.

    '''
    # Ensure path points to valid folder
    _validate_folder_path(folder_path)

    # Get folder contents and filter for valid files
    # Note, we sort the list to ensure consistent behavior across operating
    # systems.
    files = sorted(glob.glob(os.path.join(folder_path, "*")))
    files = [f for f in files if os.path.isfile(f)]

    return files


def _validate_folder_path(folder_path):
    '''
    Validate that a provided path points to a valid folder.

    Parameters
    ----------
    folder_path : str
        Path to a folder.

    Raises
    ------
    ScaperError
        If ```folder_path``` does not point to a valid folder.

    '''
    if not os.path.isdir(folder_path):
        raise ScaperError(
            'Folder path "{:s}" does not point to a valid folder'.format(
                str(folder_path)))


def _populate_label_list(folder_path, label_list):
    '''
    Given a path to a folder and a list, add the names of all subfolders
    contained in this folder (excluding folders whose name starts with '.') to
    the provided list. This is used in scaper to populate the lists of valid
    foreground and background labels, which are determined by the names of the
    folders contained in ```fg_path`` and ```bg_path``` provided during
    initialization.

    Parameters
    ----------
    folder_path : str
        Path to a folder
    label_list : list
        List to which label (subfolder) names will be added.

    See Also
    --------
    _validate_folder_path : Validate that a provided path points to a valid
    folder.

    '''
    # Make sure folder path is valid
    _validate_folder_path(folder_path)

    folder_names = os.listdir(folder_path)
    for fname in folder_names:
        if (os.path.isdir(os.path.join(folder_path, fname)) and
                fname[0] != '.'):
            label_list.append(fname)


def _trunc_norm(mu, sigma, trunc_min, trunc_max):
    '''
    Return a random value sampled from a truncated normal distribution with
    mean ```mu``` and standard deviation ```sigma``` whose values are limited
    between ```trunc_min``` and ```trunc_max```.

    Parameters
    ----------
    mu : float
        The mean of the truncated normal distribution
    sig : float
        The standard deviation of the truncated normal distribution
    trunc_min : float
        The minimum value allowed for the distribution (lower boundary)
    trunc_max : float
        The maximum value allowed for the distribution (upper boundary)

    Returns
    -------
    value : float
        A random value sampled from the truncated normal distribution defined
        by ```mu```, ```sigma```, ```trunc_min``` and ```trunc_max```.

    '''
    # By default truncnorm expects a (lower boundary) and b (upper boundary)
    # values for a standard normal distribution (mu=0, sigma=1), so we need
    # to recompute a and b given the user specified parameters.
    a, b = (trunc_min - mu) / float(sigma), (trunc_max - mu) / float(sigma)
    return scipy.stats.truncnorm.rvs(a, b, mu, sigma)


def max_polyphony(ann):
    '''
    Given an annotation of sound events, compute the maximum polyphony, i.e.
    the maximum number of simultaneous events at any given point in time. Only
    foreground events are taken into consideration for computing the polyphony.

    Parameters
    ----------
    ann : JAMS.Annotation

    Returns
    -------
    polyphony : int
        Maximum number of simultaneous events at any point in the annotation.
    '''
    # Keep only foreground events
    int_time, int_val = ann.data.to_interval_values()
    int_time_clean = []
    for t, v in zip(int_time, int_val):
        if v['role'] == 'foreground':
            int_time_clean.append(t)
    int_time_clean = np.asarray(int_time_clean)

    # Sort and reshape
    arrivals = np.sort(int_time_clean[:, 0]).reshape(-1, 1)
    departures = np.sort(int_time_clean[:, 1]).reshape(-1, 1)

    # Onsets are +1, offsets are -1
    arrivals = np.concatenate(
        (arrivals, np.ones(arrivals.shape)), axis=1)
    departures = np.concatenate(
        (departures, -np.ones(departures.shape)), axis=1)

    # Merge arrivals and departures and sort
    entry_log = np.concatenate((arrivals, departures), axis=0)
    entry_log_sorted = entry_log[entry_log[:, 0].argsort()]

    # Get maximum number of simultaneously occurring events
    polyphony = np.max(np.cumsum(entry_log_sorted[:, 1]))

    return int(polyphony)


def crop_annotation(ann, crop):
    '''
    Given a ```sound_event ``` JAMS annotation, crop it to the middle
    ```crop``` seconds.

    Parameters
    ----------
    ann : jams.Annotation
        A JAMS ```sound_event``` annotation to crop.
    crop : float
        The duration (in seconds) to crop from the middle of the soundscape.
        Must be a positive real number. If the specified value is greater than
        the current duration of the annotation, then the returned annotation
        will be identical to the input annotation.
    '''
    # Ensure it's a sound event annotation (others not supported)
    if not ann.namespace == 'sound_event':
        raise ScaperError(
            'This function only supports the sound_event annotation '
            'namespace.')

    # Ensure crop is valid
    if not np.isrealobj(crop) or crop <= 0:
        raise ScaperError(
            'Crop duration must be a real positive number.')

    if crop >= ann.duration:
        pass
    else:
        # Compute new start/end times for soundscape
        crop_start = (ann.duration - crop) / 2.0
        crop_end = ann.duration - crop_start

        # Remove all events that end before new start time
        ann.data = ann.data[ann.data.time != 0]