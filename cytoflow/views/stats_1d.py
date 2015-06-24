from __future__ import division

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasTraits, Str, provides, Callable, Enum
import matplotlib.pyplot as plt
from cytoflow.views.i_view import IView
import numpy as np
import seaborn as sns
import pandas as pd

@provides(IView)
class Stats1DView(HasTraits):
    """
    Plots a scatter plot of a numeric variable (or optionally a summary
    statistic of some data) on the x axis vs a summary statistic of the
    same data on the y axis.
    
    Attributes
    ----------
    name : Str
        The plot's name 
    
    variable : Str
        the name of the condition to put on the X axis
        
    xchannel : None or Str
        If not None, apply *xfunction* to *xchannel* for each value of
        *xvariable*.  If None, then use values of *variable* on the x axis.
        
    xfunction : Callable
        What summary function to apply if *xchannel* is not None
    
    ychannel : Str
        Apply *yfunction* to *ychannel* for each value of *variable*
        
    yfunction : Callable
        What summary function to apply to *ychannel*
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        TODO - currently unimplemented
        
    yfacet : Str
        the conditioning variable for vertical subplots
        TODO - currently unimplemented
        
    huefacet : 
        the conditioning variable for color.
        TODO - currently unimplemented
        
    x_error_bars, y_error_bars : Enum(None, "data", "summary")
        draw error bars?  if "data", apply *{x,y}_error_function* to the same
        data that was summarized with *function*.  if "summary", apply
        *{x,y}_error_function* to subsets defined by *{x,y}_error_var* 
        TODO - unimplemented
        
    x_error_var, y_error_var : Str
        the conditioning variable used to determine summary subsets.  take the
        data that was used to draw the bar; subdivide it further by 
        {x,y}_error_var; compute the summary statistic for each subset, then 
        apply {x,y}_error_function to the resulting list.
        TODO - unimplemented
        
    x_error_function, y_error_function : Callable (1D numpy.ndarray --> float)
        for each group/subgroup subset, call this function to compute the 
        error bars.  whether it is called on the data or the summary function
        is determined by the value of *{x,y}_error_bars*
        TODO - unimplemented
        
    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats1d"
    friendly_id = "1D Statistics View" 
    
    name = Str
    variable = Str
    xchannel = Str
    xfunction = Callable
    ychannel = Str
    yfunction = Callable
    xfacet = Str
    yfacet = Str
    huefacet = Str
#     x_error_bars = Enum(None, "data", "summary")
#     x_error_function = Callable
#     x_error_var = Str
#     y_error_bars = Enum(None, "data", "summary")
#     y_error_function = Callable
#     y_error_var = Str
    subset = Str
    
    # TODO - return the un-transformed values?  is this even valid?
    # ie, if we transform with Hlog, take the mean, then return the reverse
    # transformed mean, is that the same as taking the ... um .... geometric
    # mean of the untransformed data?  hm.
    
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)
        
        if self.subset:
            data = experiment.query(self.subset)
        else:
            data = experiment.data
            
        group_vars = [self.variable]
        if self.xfacet:
            group_vars.append(self.xfacet)
        if self.yfacet:
            group_vars.append(self.yfacet)
        if self.huefacet:
            group_vars.append(self.huefacet)
            
        g = data.groupby(by = group_vars)

        y = g[self.ychannel].aggregate(self.yfunction)        
        if self.xchannel:
            x = g[self.xchannel].aggregate(self.xfunction)
            x_name = self.xchannel
            plot_data = pd.DataFrame({x_name : x, self.ychannel : y}).reset_index()
        else:
            plot_data = y.reset_index()
            x_name = self.variable
            
        # TODO - handle log-scale variables
            
        grid = sns.FacetGrid(plot_data,
                             col = (self.xfacet if self.xfacet else None),
                             row = (self.yfacet if self.yfacet else None),
                             hue = (self.huefacet if self.huefacet else None),
                             legend_out = False)
        
        grid.map(plt.scatter, x_name, self.ychannel, **kwargs)
        grid.map(plt.plot, x_name, self.ychannel, **kwargs)
        grid.add_legend()
        
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        if not experiment:
            return False
        
        if not self.variable in experiment.metadata:
            return False
        
        # TODO - check that self.variable is NUMERIC, not categorical
        
        if self.xchannel and self.channel not in experiment.channels:
            return False
        
        if self.xchannel and not self.xfunction:
            return False
        
        if not self.ychannel or self.ychannel not in experiment.channels:
            return False
        
        if not self.yfunction:
            return False
        
        if self.xfacet and self.xfacet not in experiment.metadata:
            return False
        
        if self.yfacet and self.yfacet not in experiment.metadata:
            return False
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            return False
        
        if self.subset:
            try:
                experiment.query(self.subset)
            except:
                return False
        
        return True
    
if __name__ == '__main__':
    import cytoflow as flow
    import FlowCytometryTools as fc

    tube1 = fc.FCMeasurement(ID='Test 1', 
                             datafile='../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube2 = fc.FCMeasurement(ID='Test 2', 
                           datafile='../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    tube3 = fc.FCMeasurement(ID='Test 3', 
                             datafile='../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube4 = fc.FCMeasurement(ID='Test 4', 
                           datafile='../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
#     ex.add_tube(tube3, {"Dox" : 10.0, "Repl" : 2})
#     ex.add_tube(tube4, {"Dox" : 1.0, "Repl" : 2})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A', 'B1-A', 'FSC-A', 'SSC-A']
    ex2 = hlog.apply(ex)
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex3 = thresh.apply(ex2)
    
    s = flow.Stats1DView()
    s.variable = "Dox"
#    s.xchannel = "V2-A"
#    s.xfunction = np.mean
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"
#    s.group = "Dox"
#    s.subgroup = "Y2-A+"
#    s.error_bars = "data"
    #s.error_var = "Repl"
#    s.error_function = np.std
    
    plt.ioff()
    s.plot(ex3)
    plt.show()