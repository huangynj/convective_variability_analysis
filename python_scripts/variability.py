"""
Filename:     variability.py
Author:       Stephan Rasp, s.rasp@lmu.de
Description:  Compute variance and mean of coarse grained fields

"""

import argparse
from netCDF4 import Dataset
from helpers import pp_exists, get_pp_fn, load_raw_data, make_datelist, \
                    identify_clouds, get_config, create_log_str, \
                    read_netcdf_dataset
import matplotlib.pyplot as plt
import numpy as np

################################################################################
# PREPROCESSING FUNCTIONS
################################################################################


def compute_variance(inargs):
    """
    Main analysis routine to coarse grain fields and compute variances.
    
    Parameters
    ----------
    inargs

    Returns
    -------

    """

    # Some preliminaries
    dx = float(get_config(inargs, 'domain', 'dx'))

    # Make the pp NetCDF file
    rootgroup = create_netcdf(inargs)

    # Load the raw_data
    if inargs.var == 'm':   # Load data for mass flux calculation
        raw_data = load_raw_data(inargs, ['W', 'QC', 'QI', 'QS', 'RHO',
                                          'TTENS_MPHY'], 'ens', lvl=inargs.lvl)
    elif inargs.var == 'prec':   # Load data for precipitation calculation
        raw_data = load_raw_data(inargs, ['PREC_ACCUM'], 'ens')
    else:
        raise Exception('Wrong var! ' + inargs.var)

    # Loop over each time
    for idate, date in enumerate(make_datelist(inargs)):
        print('Computing variance for ' + date)
        for it in range(rootgroup.dimensions['time'].size):
            # Loop over ensemble members
            # Temporarily save the centers of mass and sums
            com_ens_list = []
            sum_ens_list = []
            for ie in range(raw_data.dimensions['ens_no'].size):
                # Identify the clouds
                if inargs.var is 'm':
                    field = raw_data.variables['W'][idate, it, ie]
                    opt_field = (raw_data.variables['QC'][idate, it, ie] +
                                 raw_data.variables['QI'][idate, it, ie] +
                                 raw_data.variables['QS'][idate, it, ie])
                    rho = raw_data.variables['RHO'][idate, it, ie]
                    opt_thresh = 0.

                else:
                    field = raw_data.variables['PREC_ACCUM'][idate, it, ie]
                    opt_field = None
                    rho = None
                    opt_thresh = None

                labels, size_list, sum_list, com_list = \
                    identify_clouds(field, inargs.thresh, opt_field=opt_field,
                                    water=inargs.sep, rho=rho,
                                    dx=dx, neighborhood=inargs.footprint,
                                    return_com=True, opt_thresh=opt_thresh)

                # if com.shape[0] == 0:   # Accout for empty arrays, Need that?
                #    com = np.empty((0,2))
                com_ens_list.append(com_list)
                sum_ens_list.append(sum_list)

            # Compute the variances and means
            comp_var_mean(inargs, idate, it, rootgroup, com_ens_list,
                          sum_ens_list, raw_data)
    rootgroup.close()


def create_netcdf(inargs):
    """
    
    Parameters
    ----------
    inargs

    Returns
    -------

    """

    dimensions = {
        'date':  np.array(make_datelist(inargs, out_format='netcdf')),
        'time': np.arange(inargs.time_start, inargs.time_end + inargs.time_inc,
                          inargs.time_inc),
        'n': np.array([256, 128, 64, 32, 16, 8, 4]),
        'x': np.arange(get_config(inargs, 'domain', 'ana_irange')),
        'y': np.arange(get_config(inargs, 'domain', 'ana_jrange'))
    }

    variables = {
        'var_m': ['date', 'time', 'n', 'x', 'y'],
        'var_M': ['date', 'time', 'n', 'x', 'y'],
        'var_N': ['date', 'time', 'n', 'x', 'y'],
        'mean_m': ['date', 'time', 'n', 'x', 'y'],
        'mean_M': ['date', 'time', 'n', 'x', 'y'],
        'mean_N': ['date', 'time', 'n', 'x', 'y']
    }
    if inargs.var is 'm':
        variables.update({'var_TTENS': ['date', 'time', 'n', 'x', 'y'],
                          'mean_TTENS': ['date', 'time', 'n', 'x', 'y']})

    pp_fn = get_pp_fn(inargs)

    # Create NetCDF file
    rootgroup = Dataset(pp_fn, 'w', format='NETCDF4')
    rootgroup.log = create_log_str(inargs, 'Preprocessing')

    # Create root dimensions and variables
    for dim_name, dim_val in dimensions.items():
        rootgroup.createDimension(dim_name, dim_val.shape[0])
        tmp_var = rootgroup.createVariable(dim_name, 'f8', dim_name)
        tmp_var[:] = dim_val

    # Create variables
    for var_name, var_dims in variables.items():
        rootgroup.createVariable(var_name, 'f8', var_dims)

    return rootgroup


def comp_var_mean(inargs, idate, it, rootgroup, com_ens_list, sum_ens_list,
                  raw_data):
    """
    At this point, the incoming fields and lists are all ensemble members 
    for one date and one time.
    """

    # Loop over different coarsening sizes
    for i_n, n in enumerate(rootgroup.variables['n']):

        # Get size of coarse arrays
        nx = int(np.floor(get_config(inargs, 'domain', 'ana_irange') / n))
        ny = int(np.floor(get_config(inargs, 'domain', 'ana_jrange') / n))

        # Loop over coarse grid boxes
        for ico in range(nx):
            for jco in range(ny):
                # Get limits for each N box
                xmin = ico * n
                xmax = (ico + 1) * n
                ymin = jco * n
                ymax = (jco + 1) * n

                # Now loop over the ensemble members and save the relevant lists
                # The terminology follows the mass flux calculations, but
                # this works for prec as well (hopefully)
                ens_m_list = []
                ens_M_list = []
                ens_N_list = []
                if inargs.var is 'm':   # Also compute heating rate sum and var
                    ens_ttens_list = []
                for ie, com_list, sum_list in zip(range(inargs.nens),
                                                  com_ens_list,
                                                  sum_ens_list):

                    # Get the collapsed clouds for each box
                    bool_arr = ((com_list[:, 0] >= xmin) &
                                (com_list[:, 0] < xmax) &
                                (com_list[:, 1] >= ymin) &
                                (com_list[:, 1] < ymax))

                    # This is the array with all clouds for this box and member
                    box_cld_sum = sum_list[bool_arr]

                    # This lists contains all clouds for all members in a box
                    ens_m_list += list(box_cld_sum)

                    # If the array is empty set M to zero
                    if len(box_cld_sum) > 0:
                        ens_M_list.append(np.sum(box_cld_sum))
                    else:
                        ens_M_list.append(0.)

                    # This is the number of clouds
                    ens_N_list.append(box_cld_sum.shape[0])

                    if inargs.var is 'm':
                        # This is the MEAN heating rate
                        ens_ttens_list.append(np.mean(raw_data.
                                                      variables['TTENS_MPHY']
                                                      [idate, it, ie]
                                                      [ico * n:(ico + 1) * n,
                                                       jco * n:(jco + 1) * n]))
                    # End member loop

                # Now convert the list with all clouds for this box
                ens_m_list = np.array(ens_m_list)

                # Calculate statistics and save them in ncdf file
                # Check if x number of members have clouds in them

                if np.sum(np.array(ens_N_list) > 0) >= inargs.minobj:
                    rootgroup.variables['var_M'][idate, it, i_n, ico, jco] = \
                        np.var(ens_M_list, ddof=1)
                    rootgroup.variables['var_N'][idate, it, i_n, ico, jco] = \
                        np.var(ens_N_list, ddof=1)
                    rootgroup.variables['var_m'][idate, it, i_n, ico, jco] = \
                        np.var(ens_m_list, ddof=1)
                    rootgroup.variables['mean_M'][idate, it, i_n, ico, jco] = \
                        np.mean(ens_M_list)
                    rootgroup.variables['mean_N'][idate, it, i_n, ico, jco] = \
                        np.mean(ens_N_list)
                    rootgroup.variables['mean_m'][idate, it, i_n, ico, jco] = \
                        np.mean(ens_m_list)

                else:
                    rootgroup.variables['var_M'][idate, it, i_n, ico, jco] = \
                        np.nan
                    rootgroup.variables['var_N'][idate, it, i_n, ico, jco] = \
                        np.nan
                    rootgroup.variables['var_m'][idate, it, i_n, ico, jco] = \
                        np.nan
                    rootgroup.variables['mean_M'][idate, it, i_n, ico, jco] = \
                        np.nan
                    rootgroup.variables['mean_N'][idate, it, i_n, ico, jco] = \
                        np.nan
                    rootgroup.variables['mean_m'][idate, it, i_n, ico, jco] = \
                        np.nan
                # This means NaNs only appear when minmem criterion is not met

                if inargs.var is 'm':
                    rootgroup.variables['var_TTENS'][idate, it, i_n, ico, jco] = \
                        np.var(ens_ttens_list, ddof=1)
                    rootgroup.variables['mean_TTENS'][idate, it, i_n, ico, jco] = \
                        np.mean(ens_ttens_list)


################################################################################
# PLOTTING FUNCTIONS
################################################################################
def diurnal(inargs):
    """
    
    Parameters
    ----------
    inargs

    Returns
    -------

    """

    # Load dataset
    rootgroup = read_netcdf_dataset(inargs)
    # The variables have dimensions [date, time, n, x[n], y[n]]

    # Do some further calculations to get daily composite
    for i_n, n in enumerate(rootgroup.variables['n']):
        nx = int(np.floor(get_config(inargs, 'domain', 'ana_irange') / n))
        ny = int(np.floor(get_config(inargs, 'domain', 'ana_jrange') / n))

        mean_M = rootgroup.variables['mean_M'][:, :, i_n, :nx, :ny]

        print mean_M.shape
        # Flatten x and y dimensions
        mean_M.reshape(mean_M.shape[0], mean_M.shape[1],
                       mean_M.shape[2] * mean_M.shape[3])
        print mean_M.shape




################################################################################
# MAIN FUNCTION
################################################################################
def main(inargs):
    """
    Runs the main program

    Parameters
    ----------
    inargs : argparse object
      Argparse object with all input arguments
    """

    # Check if pre-processed file exists
    if (pp_exists(inargs) is False) or (inargs.recompute is True):
        print('Compute preprocessed file: ' + get_pp_fn(inargs))
        # Call preprocessing routine with arguments
        compute_variance(inargs)
    else:
        print('Found pre-processed file:' + get_pp_fn(inargs))

    # Plotting
    diurnal(inargs)


if __name__ == '__main__':

    description = __doc__

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--date_start',
                        type=str,
                        help='Start date of analysis in yyyymmddhh')
    parser.add_argument('--date_end',
                        type=str,
                        help='End date of analysis in yyyymmddhh')
    parser.add_argument('--time_start',
                        type=int,
                        default=1,
                        help='Analysis start time in hrs [including]. \
                              Default = 1')
    parser.add_argument('--time_end',
                        type=int,
                        default=24,
                        help='Analysis end time in hrs [including]. \
                              Default = 24')
    parser.add_argument('--time_inc',
                        type=float,
                        default=1,
                        help='Analysis increment in hrs. Default = 1')
    parser.add_argument('--nens',
                        type=int,
                        default=50,
                        help='Number of ensemble members')
    parser.add_argument('--var',
                        type=str,
                        default='m',
                        help='Type of variable to do calculation for.\
                             Options are [m, prec]')
    parser.add_argument('--lvl',
                        type=int,
                        default=30,
                        help='Vertical level for m analysis.')
    parser.add_argument('--minobj',
                        type=int,
                        default='1',
                        help='Minimum number of clouds in all ensemble members '
                             'for variance calcualtion')
    parser.add_argument('--thresh',
                        type=float,
                        default=1.,
                        help='Threshold for cloud object identification.')
    parser.add_argument('--sep',
                        dest='sep',
                        action='store_true',
                        help='If given, apply cloud separation.')
    parser.set_defaults(sep=False)
    parser.add_argument('--footprint',
                        type=int,
                        default=3,
                        help='Size of search matrix for cloud separation')

    parser.add_argument('--config_file',
                        type=str,
                        default='config.yml',
                        help='Config file in relative directory ../config. \
                              Default = config.yml')
    parser.add_argument('--sub_dir',
                        type=str,
                        default='variability',
                        help='Sub-directory for figures and pp_files')
    parser.add_argument('--plot_name',
                        type=str,
                        default='',
                        help='Custom plot name.')
    parser.add_argument('--pp_name',
                        type=str,
                        default='',
                        help='Custom name for preprocessed file.')
    parser.add_argument('--recompute',
                        dest='recompute',
                        action='store_true',
                        help='If True, recompute pre-processed file.')
    parser.set_defaults(recompute=False)

    args = parser.parse_args()

    main(args)