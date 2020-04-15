#!/bin/env python
# -*coding: UTF-8 -*-
#
# Disclaimer:
# Functions get_sys_info, netcdf_and_hdf5_versions and show_versions are from:
# xarray/util/print_versions.py
#

import os
import sys
import warnings
import requests
import io
from IPython.core.display import display, HTML

import importlib
import locale
import platform
import struct
import subprocess

import pickle
import pkg_resources
path2pkl = pkg_resources.resource_filename('argopy', 'assets/')

def urlopen(url):
    """ Load content from url or raise alarm on status with explicit information on the error

    Parameters
    ----------
    url: str

    Returns
    -------
    io.BytesIO

    """
    # https://github.com/ioos/erddapy/blob/3828a4f479e7f7653fb5fd78cbce8f3b51bd0661/erddapy/utilities.py#L37
    r = requests.get(url)
    data = io.BytesIO(r.content)

    if r.status_code == 200:  # OK
        return data

    # 4XX client error response
    elif r.status_code == 404:  # Empty response
        error = ["Error %i " % r.status_code]
        error.append(data.read().decode("utf-8").replace("Error", ""))
        error.append("%s" % url)
        raise requests.HTTPError("\n".join(error))

    # 5XX server error response
    elif r.status_code == 500:  # 500 Internal Server Error
        if "text/html" in r.headers.get('content-type'):
            display(HTML(data.read().decode("utf-8")))
        error = ["Error %i " % r.status_code]
        error.append(data.read().decode("utf-8"))
        error.append("%s" % url)
        raise requests.HTTPError("\n".join(error))
    else:
        error = ["Error %i " % r.status_code]
        error.append(data.read().decode("utf-8"))
        error.append("%s" % url)
        print("\n".join(error))
        r.raise_for_status()

def load_dict(ptype):
    if ptype=='profilers':        
        with open(os.path.join(path2pkl, 'dict_profilers.pickle'), 'rb') as f:
            loaded_dict = pickle.load(f)
        return loaded_dict
    elif ptype=='institutions':
        with open(os.path.join(path2pkl, 'dict_institutions.pickle'), 'rb') as f:
            loaded_dict = pickle.load(f)
        return loaded_dict      
    else:
        raise ValueError("Invalid dictionnary pickle file")

def mapp_dict(Adictionnary,Avalue):
    try:        
        return Adictionnary[Avalue] 
    except KeyError:
        return "Unknown"        

def list_available_data_src():
    """ List all available data sources """
    AVAILABLE_SOURCES = {}
    try:
        from .data_fetchers import erddap as Erddap_Fetchers
        AVAILABLE_SOURCES['erddap'] = Erddap_Fetchers
    except:
        warnings.warn("An error occured while loading the ERDDAP data fetcher, "
                      "it will not be available !\n%s\n%s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass

    try:
        from .data_fetchers import localftp as LocalFTP_Fetchers
        AVAILABLE_SOURCES['localftp'] = LocalFTP_Fetchers
    except:
        warnings.warn("An error occured while loading the local FTP data fetcher, "
                      "it will not be available !\n%s\n%s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass

    return AVAILABLE_SOURCES

def list_standard_variables():
    """ Return the list of variables for standard users
    """
    return ['DATA_MODE', 'LATITUDE', 'LONGITUDE', 'POSITION_QC', 'DIRECTION', 'PLATFORM_NUMBER', 'CYCLE_NUMBER', 'PRES',
     'TEMP', 'PSAL', 'PRES_QC', 'TEMP_QC', 'PSAL_QC', 'PRES_ADJUSTED', 'TEMP_ADJUSTED', 'PSAL_ADJUSTED',
     'PRES_ADJUSTED_QC', 'TEMP_ADJUSTED_QC', 'PSAL_ADJUSTED_QC', 'PRES_ADJUSTED_ERROR', 'TEMP_ADJUSTED_ERROR',
     'PSAL_ADJUSTED_ERROR', 'JULD', 'JULD_QC', 'TIME', 'TIME_QC']

def list_multiprofile_file_variables():
    """ Return the list of variables in a netcdf multiprofile file.

        This is for files created by GDAC under <DAC>/<WMO>/<WMO>_prof.nc
    """
    return [ 'CONFIG_MISSION_NUMBER',
             'CYCLE_NUMBER',
             'DATA_CENTRE',
             'DATA_MODE',
             'DATA_STATE_INDICATOR',
             'DATA_TYPE',
             'DATE_CREATION',
             'DATE_UPDATE',
             'DC_REFERENCE',
             'DIRECTION',
             'FIRMWARE_VERSION',
             'FLOAT_SERIAL_NO',
             'FORMAT_VERSION',
             'HANDBOOK_VERSION',
             'HISTORY_ACTION',
             'HISTORY_DATE',
             'HISTORY_INSTITUTION',
             'HISTORY_PARAMETER',
             'HISTORY_PREVIOUS_VALUE',
             'HISTORY_QCTEST',
             'HISTORY_REFERENCE',
             'HISTORY_SOFTWARE',
             'HISTORY_SOFTWARE_RELEASE',
             'HISTORY_START_PRES',
             'HISTORY_STEP',
             'HISTORY_STOP_PRES',
             'JULD',
             'JULD_LOCATION',
             'JULD_QC',
             'LATITUDE',
             'LONGITUDE',
             'PARAMETER',
             'PI_NAME',
             'PLATFORM_NUMBER',
             'PLATFORM_TYPE',
             'POSITIONING_SYSTEM',
             'POSITION_QC',
             'PRES',
             'PRES_ADJUSTED',
             'PRES_ADJUSTED_ERROR',
             'PRES_ADJUSTED_QC',
             'PRES_QC',
             'PROFILE_PRES_QC',
             'PROFILE_PSAL_QC',
             'PROFILE_TEMP_QC',
             'PROJECT_NAME',
             'PSAL',
             'PSAL_ADJUSTED',
             'PSAL_ADJUSTED_ERROR',
             'PSAL_ADJUSTED_QC',
             'PSAL_QC',
             'REFERENCE_DATE_TIME',
             'SCIENTIFIC_CALIB_COEFFICIENT',
             'SCIENTIFIC_CALIB_COMMENT',
             'SCIENTIFIC_CALIB_DATE',
             'SCIENTIFIC_CALIB_EQUATION',
             'STATION_PARAMETERS',
             'TEMP',
             'TEMP_ADJUSTED',
             'TEMP_ADJUSTED_ERROR',
             'TEMP_ADJUSTED_QC',
             'TEMP_QC',
             'VERTICAL_SAMPLING_SCHEME',
             'WMO_INST_TYPE']

def get_sys_info():
    "Returns system information as a dict"

    blob = []

    # get full commit hash
    commit = None
    if os.path.isdir(".git") and os.path.isdir("argopy"):
        try:
            pipe = subprocess.Popen(
                'git log --format="%H" -n 1'.split(" "),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            so, serr = pipe.communicate()
        except Exception:
            pass
        else:
            if pipe.returncode == 0:
                commit = so
                try:
                    commit = so.decode("utf-8")
                except ValueError:
                    pass
                commit = commit.strip().strip('"')

    blob.append(("commit", commit))

    try:
        (sysname, nodename, release, version, machine, processor) = platform.uname()
        blob.extend(
            [
                ("python", sys.version),
                ("python-bits", struct.calcsize("P") * 8),
                ("OS", "%s" % (sysname)),
                ("OS-release", "%s" % (release)),
                ("machine", "%s" % (machine)),
                ("processor", "%s" % (processor)),
                ("byteorder", "%s" % sys.byteorder),
                ("LC_ALL", "%s" % os.environ.get("LC_ALL", "None")),
                ("LANG", "%s" % os.environ.get("LANG", "None")),
                ("LOCALE", "%s.%s" % locale.getlocale()),
            ]
        )
    except Exception:
        pass

    return blob

def netcdf_and_hdf5_versions():
    libhdf5_version = None
    libnetcdf_version = None
    try:
        import netCDF4

        libhdf5_version = netCDF4.__hdf5libversion__
        libnetcdf_version = netCDF4.__netcdf4libversion__
    except ImportError:
        try:
            import h5py

            libhdf5_version = h5py.version.hdf5_version
        except ImportError:
            pass
    return [("libhdf5", libhdf5_version), ("libnetcdf", libnetcdf_version)]

def show_versions(file=sys.stdout):
    """ Print the versions of argopy and its dependencies

    Parameters
    ----------
    file : file-like, optional
        print to the given file-like object. Defaults to sys.stdout.
    """
    sys_info = get_sys_info()

    try:
        sys_info.extend(netcdf_and_hdf5_versions())
    except Exception as e:
        print(f"Error collecting netcdf / hdf5 version: {e}")

    deps = [
        # (MODULE_NAME, f(mod) -> mod version)
        ("argopy", lambda mod: mod.__version__),
        ("xarray", lambda mod: mod.__version__),
        ("pandas", lambda mod: mod.__version__),
        ("numpy", lambda mod: mod.__version__),
        ("scipy", lambda mod: mod.__version__),
        # argopy optionals
        ("netCDF4", lambda mod: mod.__version__),
        ("pydap", lambda mod: mod.__version__),
        ("h5netcdf", lambda mod: mod.__version__),
        ("h5py", lambda mod: mod.__version__),
        ("Nio", lambda mod: mod.__version__),
        ("zarr", lambda mod: mod.__version__),
        ("cftime", lambda mod: mod.__version__),
        ("nc_time_axis", lambda mod: mod.__version__),
        ("PseudoNetCDF", lambda mod: mod.__version__),
        ("rasterio", lambda mod: mod.__version__),
        ("cfgrib", lambda mod: mod.__version__),
        ("iris", lambda mod: mod.__version__),
        ("bottleneck", lambda mod: mod.__version__),
        ("dask", lambda mod: mod.__version__),
        ("distributed", lambda mod: mod.__version__),
        ("matplotlib", lambda mod: mod.__version__),
        ("cartopy", lambda mod: mod.__version__),
        ("seaborn", lambda mod: mod.__version__),
        ("numbagg", lambda mod: mod.__version__),
        # argopy setup/test
        ("setuptools", lambda mod: mod.__version__),
        ("pip", lambda mod: mod.__version__),
        ("conda", lambda mod: mod.__version__),
        ("pytest", lambda mod: mod.__version__),
        # Misc.
        ("IPython", lambda mod: mod.__version__),
        ("sphinx", lambda mod: mod.__version__),
    ]

    deps_blob = list()
    for (modname, ver_f) in deps:
        try:
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                mod = importlib.import_module(modname)
        except Exception:
            deps_blob.append((modname, None))
        else:
            try:
                ver = ver_f(mod)
                deps_blob.append((modname, ver))
            except Exception:
                deps_blob.append((modname, "installed"))

    print("\nINSTALLED VERSIONS", file=file)
    print("------------------", file=file)

    for k, stat in sys_info:
        print(f"{k}: {stat}", file=file)

    print("", file=file)
    for k, stat in deps_blob:
        print(f"{k}: {stat}", file=file)