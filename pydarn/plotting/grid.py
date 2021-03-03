# Copyright (C) 2020 SuperDARN Canada, University of Saskatchewan
# Author: Daniel Billett, Marina Schmidt
#
# Modifications:
#
# Disclaimer:
# pyDARN is under the LGPL v3 license found in the root directory LICENSE.md
# Everyone is permitted to copy and distribute verbatim copies of this license
# document, but changing it is not allowed.
#
# This version of the GNU Lesser General Public License incorporates the terms
# and conditions of version 3 of the GNU General Public License,
# supplemented by the additional permissions listed below.


"""
Fan plots, mapped to AACGM coordinates in a polar format
"""

import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import cmocean

from matplotlib import ticker, cm, colors
from typing import List

# Third party libraries
import aacgmv2

from pydarn import PyDARNColormaps, Fan


class Grid():
    """
        Fan plots for SuperDARN data
        This class inherits from matplotlib to generate the figures
        Methods
        -------
        plot_fan
        """

    def __str__(self):
        return "This class is static class that provides"\
                " the following methods: \n"\
                "   - plot_fan()\n"\
                "   - return_beam_pos()\n"

    @classmethod
    def plot_grid(cls, dmap_data: List[dict], record: int = 0,
                  start_time: dt.datetime = None,
                  ax=None, fov: bool = True, parameter: str = 'vel',
                  lowlat: int = 50, cmap: str = None, zmin: int = None,
                  zmax: int = None, colorbar: bool = True,
                  colorbar_label: str = '', title: str = '', len_factor: float = 150.0,
                  ref_vector: int = 300):
        """
        Plots a radar's Field Of View (FOV) fan plot for the
        given data and scan number

        Parameters
        -----------
            dmap_data: List[dict]
                Named list of dictionaries obtained from SDarn_read
            record: int
                record number to plot
                default: 0
            start_time: datetime.datetime
                datetime object as the start time of the record to plot
                if none then record will be used
                default: none
            ax: matplotlib.pyplot axis
                Pre-defined axis object to pass in, must currently
                be polar projection
                Default: Generates a polar projection for the user
                with MLT/latitude labels
            parameter: str
                Key name indicating which parameter to plot.
                Default: vel (Velocity). Alternatives: 'pwr', 'wdt'
            lowlat: int
                Lower AACGM latitude boundary for the polar plot
                Default: 50
            fov: bool
                Set to false to not plot the outline of the FOV
                Default: True
            cmap: matplotlib.cm
                matplotlib colour map
                https://matplotlib.org/tutorials/colors/colormaps.html
                Default: Official pyDARN colour map for given parameter
            zmin: int
                The minimum parameter value for coloring
                Default: {'pwr': [0], 'vel': [0], 'wdt': [0]}
            zmax: int
                The maximum parameter value for  coloring
                Default: {'pwr': [50], 'vel': [1000], 'wdt': [250]}
            colorbar: bool
                Draw a colourbar if True
                Default: True
            colorbar_label: str
                The label that appears next to the colour bar.
                Requires colorbar to be true
                Default: ''
            title: str
                Adds a title to the plot. If no title is specified,
                one will be provided
                Default: ''
            len_factor: float
                Normalisation factor for the vectors, to control size on plot
                Larger number means smaller vectors on plot
                Default: 150.0   
            ref_vector: int
                Velocity value to be used for the reference vector, in m/s
                Default: 300
        Returns
        -----------
        if parameter is vector.vel.median:
        thetas - list of data point longitudes in polar coordinates shifted
        rs - list of data point latitudes
        else:
        thetas - list of data point longitudes in polar coordinates shifted
        rs - list of data point latitudes

        """
        # Short hand for the parameters in GRID files
        if parameter == 'vel' or parameter == 'pwr' or parameter == 'wdt':
            parameter = "vector.{param}.median".format(param=parameter)

        # Find the record corresponding to the start time
        if start_time is not None:
            for record in range(len(dmap_data)):
                dtime = dt.datetime(dmap_data[record]['start.year'],
                                    dmap_data[record]['start.month'],
                                    dmap_data[record]['start.day'],
                                    dmap_data[record]['start.hour'],
                                    dmap_data[record]['start.minute'])
                if dtime == start_time:
                    break

        _, aacgm_lons, _, _, ax = Fan.plot_fov(dmap_data[record]['stid'][0],
                                               dtime, boundary=fov,
                                               lowlat=lowlat)

        data_lons = dmap_data[record]['vector.mlon']
        data_lats = dmap_data[record]['vector.mlat']
        
        # Hold the beam positions
        shifted_mlts = aacgm_lons[0, 0] - \
            (aacgmv2.convert_mlt(aacgm_lons[0, 0], dtime) * 15)
        shifted_lons = data_lons - shifted_mlts
        thetas = np.radians(shifted_lons)
        rs = data_lats
        
        # Colour table and max value selection depending on parameter plotted
        # Load defaults if none given
        if cmap is None:
            cmap = {'vector.pwr.median': 'plasma',
                    'vector.vel.median': cmocean.cm.haline_r,
                    'vector.wdt.median': PyDARNColormaps.PYDARN_VIRIDIS}
            cmap = plt.cm.get_cmap(cmap[parameter])

        # Setting zmin and zmax
        defaultzminmax = {'vector.pwr.median': [0, 50],
                          'vector.vel.median': [0, 1000],
                          'vector.wdt.median': [0, 250]}
        if zmin is None:
            zmin = defaultzminmax[parameter][0]
        if zmax is None:
            zmax = defaultzminmax[parameter][1]

        norm = colors.Normalize
        norm = norm(zmin, zmax)

        data = dmap_data[record][parameter]
        
        # Plot the magnitude of the parameter
        ax.scatter(thetas, rs, c=data,
                   s=2.0, vmin=zmin, vmax=zmax, zorder=5, cmap=cmap)
                   
        # If the parameter is velocity then plot the LOS vectors
        if parameter == "vector.vel.median":
        
            # Get the azimuths from the data
            azm_v = dmap_data[record]['vector.kvect']
            
            # Number of data points
            num_pts = range(len(data))

            # Angle to "rotate" each vector by to get into same reference frame
            # Controlled by longitude, or "mltitude"
            alpha=thetas

            # Convert initial positions to cartesian
            start_pos_x=(90-rs)*np.cos(thetas) 
            start_pos_y=(90-rs)*np.sin(thetas)
        
            # Resolve LOS vector in x and y directions, with respect to mag pole
            # Gives zonal and meridional components of LOS vector
            los_x=-data*np.cos(np.radians(-azm_v))
            los_y=-data*np.sin(np.radians(-azm_v))
            
            # Rotate each vector into same reference frame following vector rotation matrix
            # https://en.wikipedia.org/wiki/Rotation_matrix
            vec_x=(los_x*np.cos(alpha))-(los_y*np.sin(alpha))
            vec_y=(los_x*np.sin(alpha))+(los_y*np.cos(alpha))
            
            # New vector end points, in cartesian
            end_pos_x=start_pos_x+(vec_x/len_factor)
            end_pos_y=start_pos_y+(vec_y/len_factor)
            
            # Convert back to polar for plotting
            end_rs=90-(np.sqrt(end_pos_x**2+end_pos_y**2))
            end_thetas=np.arctan2(end_pos_y,end_pos_x)
            
            # Plot the vectors
            for i in num_pts:
                plt.polar([thetas[i], end_thetas[i]], [rs[i], end_rs[i]],
                          c=cmap(norm(data[i])), linewidth=0.5)
                          
            # TODO: Add a velocity reference vector          

        if colorbar is True:
            mappable = cm.ScalarMappable(norm=norm, cmap=cmap)
            locator = ticker.MaxNLocator(symmetric=True, min_n_ticks=3,
                                         integer=True, nbins='auto')
            ticks = locator.tick_values(vmin=zmin, vmax=zmax)

            cb = ax.figure.colorbar(mappable, ax=ax,
                                    extend='both', ticks=ticks)

            if colorbar_label != '':
                cb.set_label(colorbar_label)

        if title == '':
            title = "{year} {month} {day} {start_hour}:{start_minute} -"\
                " {end_hour}:{end_minute}"\
                    "".format(year=dtime.year,
                              month=dtime.month,
                              day=dtime.day,
                              start_hour=dtime.hour,
                              start_minute=dtime.minute,
                              end_hour=dmap_data[record]['end.hour'],
                              end_minute=dmap_data[record]['end.minute'])
        plt.title(title)
        if parameter == 'vector.vel.median':
            return thetas, end_thetas, rs, end_rs, data
        return thetas, rs, data
