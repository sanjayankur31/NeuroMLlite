#
#
#   A class to write the network connectivity in matrix format...
#
#

from neuromllite.utils import print_v
from neuromllite.ConnectivityHandler import ConnectivityHandler

from neuromllite.utils import evaluate
            
from pyneuroml.pynml import convert_to_units
import numpy as np


class MatrixHandler(ConnectivityHandler):
        
    colormaps_used = []
    
    weight_arrays_to_show = {}
    
    def __init__(self, 
                 level=10, 
                 nl_network=None):
                     
        self.nl_network = nl_network
        self.level = level
        print_v("Initiating Matrix handler, level %i"%(level))
        self.scale_by_post_pop_cond = True
    
    
    def print_settings(self):
        print_v('**************************************')
        print_v('*')
        print_v('* Settings for MatrixHandler: ')
        print_v('*    level:                   %s'%self.level)
        print_v('*    is_cell_level:           %s'%self.is_cell_level())
        print_v('*    CUTOFF_INH_SYN_MV:       %s'%self.CUTOFF_INH_SYN_MV)
        #print_v('*    include_inputs:          %s'%self.include_inputs)
        #print_v('*    scale_by_post_pop_size:  %s'%self.scale_by_post_pop_size)
        #print_v('*    scale_by_post_pop_cond:  %s'%self.scale_by_post_pop_cond)
        #print_v('*    min_weight_to_show:      %s'%self.min_weight_to_show)
        #print_v('*    min_weight_to_show:      %s'%self.min_weight_to_show)
        print_v('*')
        print_v('* Used values: ')
        print_v('*    colormaps_used:          %s'%self.colormaps_used)
        print_v('*    zero_weight_color:       %s'%self.zero_weight_color)
        print_v('*')
        print_v('**************************************')
    
            
    def finalise_document(self):
        
        entries = []
        
        for pop in self.proj_pre_pops.values() + self.proj_post_pops.values():
            if self.is_cell_level():
                for i in range(self.pop_sizes[pop]):
                    pi = self.get_cell_identifier(pop, i) # '%s_%i'%(pop,i)
                    if not pi in entries: entries.append(pi)
            else:
                if not pop in entries:
                    entries.append(pop)
                
        entries = sorted(entries)
        
        matrix_per_cell = '%s (weight per indiv conn)'
        matrix_per_cell_cond = '%s (indiv conn weight*syn cond)'
        
        matrix_single_conns = '%s (avg weight per existant conn)'
        matrix_number_conns = '%s (number conns)'
        matrix_total_conns = '%s (sum of weights of conns)'
        matrix_total_conns_per_cell = '%s ((sum of weights)*cond/postpopsize)'
        
        cbar_labels = {}
        for proj_type in self.proj_types.values():
            pclass = self._get_proj_class(proj_type)
            
            all_matrices = [matrix_single_conns, matrix_number_conns,matrix_total_conns, matrix_total_conns_per_cell]
            
            if self.is_cell_level():
                all_matrices = [matrix_per_cell, matrix_per_cell_cond]
                
            for m in all_matrices:
                label = m%pclass
                
                self.weight_arrays_to_show[label] = np.zeros((len(entries),len(entries)))
                

            cbar_labels[matrix_per_cell%pclass] = 'weight'
            cbar_labels[matrix_per_cell_cond%pclass] = 'conductance (nS)'
            
            cbar_labels[matrix_number_conns%pclass] = 'number'
            cbar_labels[matrix_single_conns%pclass] = 'weight' # (red: exc; blue: inh)'
            cbar_labels[matrix_total_conns%pclass] = 'total weight' # (red: exc; blue: inh)'
            cbar_labels[matrix_total_conns_per_cell%pclass] = 'conductance (nS)'
            
                
        for projName in self.proj_weights:
            
            pre_pop = self.proj_pre_pops[projName] 
            post_pop = self.proj_post_pops[projName]
            proj_type = self.proj_types[projName]
            num_pre = self.get_size_pre_pop(projName)
            num_post = self.get_size_post_pop(projName)
            
            gbase_nS, gbase = self._get_gbase_nS(projName,return_orig_string_also=True)

            pclass = self._get_proj_class(proj_type)
            sign = -1 if 'inhibitory' in proj_type else 1

            print_v("MATRIX PROJ: %s (%s (%i) -> %s (%i), %s): w %s; wtot: %s; sign: %s; cond: %s nS (%s)"%(projName, pre_pop, num_pre, post_pop, num_post, proj_type, self.proj_weights[projName], self.proj_tot_weight[projName], sign, gbase_nS, gbase))

            if self.is_cell_level():
                
                for pre_i in range(self.pop_sizes[pre_pop]):
                    for post_i in range(self.pop_sizes[post_pop]):
                        pre_pop_i =  entries.index( self.get_cell_identifier(pre_pop,  pre_i))
                        post_pop_i = entries.index( self.get_cell_identifier(post_pop, post_i))
                        
                        self.weight_arrays_to_show[matrix_per_cell%pclass][pre_pop_i][post_pop_i] += self.proj_individual_weights[projName][pre_i][post_i]
                        if projName in self.proj_syn_objs:
                            self.weight_arrays_to_show[matrix_per_cell_cond%pclass][pre_pop_i][post_pop_i] += self.proj_individual_scaled_weights[projName][pre_i][post_i]

            else:
                pre_pop_i = entries.index(pre_pop)
                post_pop_i = entries.index(post_pop)

                self.weight_arrays_to_show[matrix_total_conns%pclass][pre_pop_i][post_pop_i] += \
                     abs(self.proj_tot_weight[projName]) * sign

                if abs(self.proj_tot_weight[projName])!=abs(self.proj_weights[projName]):

                    self.weight_arrays_to_show[matrix_single_conns%pclass][pre_pop_i][post_pop_i] += \
                         abs(self.proj_weights[projName]) * sign

                    self.weight_arrays_to_show[matrix_number_conns%pclass][pre_pop_i][post_pop_i] += \
                         abs(self.proj_conns[projName])
                         
                    cond_scale = gbase_nS if gbase_nS else 1.0
                    self.weight_arrays_to_show[matrix_total_conns_per_cell%pclass][pre_pop_i][post_pop_i] += \
                         abs(self.proj_tot_weight[projName]) * cond_scale / num_post
                
        
        import matplotlib.pyplot as plt
        import matplotlib
        
        for proj_type in self.weight_arrays_to_show:
            weight_array = self.weight_arrays_to_show[proj_type]
            
            print_v("Plotting proj_type: %s with values from %s to %s"%(proj_type, weight_array.min(), weight_array.max()))
            if not (weight_array.max()==0 and weight_array.min()==0):

                fig, ax = plt.subplots()
                title = 'Connections: %s'%(proj_type)
                plt.title(title)
                fig.canvas.set_window_title(title)

                max_abs_weight = max(weight_array.max(), -1.0*(weight_array.min()))
                min_abs_weight = np.min(abs(weight_array[np.nonzero(weight_array)]))
                
                if weight_array.min()<0:
                    cm = matplotlib.cm.get_cmap('bwr')
                    self.zero_weight_color = 'green'

                else:
                    #cm = matplotlib.cm.get_cmap('binary')
                    
                    #if 'indiv' in proj_type or 'number' in proj_type:
                    cm = matplotlib.cm.get_cmap('rainbow')
                    self.zero_weight_color = 'black'
                        
                #print dir(cm)
                if not cm.name in self.colormaps_used:
                    self.colormaps_used.append(str(cm.name))
                    
                print_v("  Plotting weight matrix [%s] (%s; 0=%s) with vals %s -> %s (max abs: %s, min nz abs: %s)"%(title, cm.name, self.zero_weight_color, weight_array.min(), weight_array.max(), max_abs_weight, min_abs_weight))
                #print weight_array

                im = plt.imshow(weight_array, cmap=cm, interpolation='nearest',norm=None)

                if weight_array.min()<0:
                    plt.clim(-1*max_abs_weight,max_abs_weight)
                elif min_abs_weight==max_abs_weight:
                    plt.clim(max_abs_weight*0.000001,max_abs_weight)
                else:
                    plt.clim(min_abs_weight*0.9999,max_abs_weight)
                    
                cm.set_under(self.zero_weight_color)

                ax = plt.gca();

                # Gridlines based on minor ticks
                if weight_array.shape[0]<40:
                    ax.grid(which='minor', color='grey', linestyle='-', linewidth=.3)

                xt = np.arange(weight_array.shape[1]) + 0
                ax.set_xticks(xt)
                ax.set_xticks(xt[:-1]+0.5,minor=True)
                ax.set_yticks(np.arange(weight_array.shape[0]) + 0)
                ax.set_yticks(np.arange(weight_array.shape[0]) + 0.5,minor=True)

                ax.set_yticklabels(entries)
                ax.set_xticklabels(entries)
                ax.set_ylabel('presynaptic')
                tick_size = 10 if weight_array.shape[0]<20 else (8 if weight_array.shape[0]<40 else 6)
                ax.tick_params(axis='y', labelsize=tick_size)
                ax.set_xlabel('postsynaptic')
                ax.tick_params(axis='x', labelsize=tick_size)
                fig.autofmt_xdate()
                
                for i in range(len(entries)):
                    alpha = 1
                    lwidth = 7
                    offset = -1*lwidth*len(entries)/500.
                    
                    if self.pop_colors[entries[i]]:
                        from matplotlib import lines
                        x,y = [[-0.5+offset,-0.5+offset], [i-0.5,i+0.5]]
                        line = lines.Line2D(x, y, lw=lwidth, color=self.pop_colors[entries[i]], alpha=alpha)
                        line.set_solid_capstyle('butt')
                        line.set_clip_on(False)
                        ax.add_line(line)
                        
                        x,y = [[i-0.5,i+0.5], [len(entries)-0.5-offset,len(entries)-0.5-offset]]
                        line = lines.Line2D(x, y, lw=lwidth, color=self.pop_colors[entries[i]], alpha=alpha)
                        line.set_solid_capstyle('butt')
                        line.set_clip_on(False)
                        ax.add_line(line)

                cbar = plt.colorbar(im)
                if proj_type in cbar_labels:
                    cbar.set_label(cbar_labels[proj_type])
                
        print_v("Generating matrix for: %s"%self.network_id)
        self.print_settings()
        
        plt.show()
        

    def handle_population(self, population_id, component, size=-1, component_obj=None, properties={}, notes=None):
        sizeInfo = " as yet unspecified size"
        
        if size>=0:
            sizeInfo = ", size: "+ str(size)+ " cells"
            
        if component_obj:
            compInfo = " (%s)"%component_obj.__class__.__name__
        else:
            compInfo=""
            
        print_v("Population: "+population_id+", component: "+component+compInfo+sizeInfo+", properties: %s"%properties)
        
        color = None 
        
        if properties and 'color' in properties:
            rgb = properties['color'].split()
            color = '#'
            for a in rgb:
                color = color+'%02x'%int(float(a)*255)
            
            # https://stackoverflow.com/questions/3942878
            if (float(rgb[0])*0.299 + float(rgb[1])*0.587 + float(rgb[2])*0.2) > .25:
                fcolor= '#000000'
            else:
                fcolor= '#ffffff'
                
            print_v('Color %s -> %s -> %s'%(properties['color'], rgb, color))
        
        pop_type = None
        if properties and 'type' in properties:
            pop_type = properties['type']
            
        self.pop_sizes[population_id] = size
        
        if not self.is_cell_level():
            self.pop_colors[population_id] = color
            if pop_type:
                self.pop_types[population_id] = pop_type
        else:
            for i in range(size):
                cell_pop = self.get_cell_identifier(population_id,i)
                self.pop_colors[cell_pop] = color
                if pop_type:
                    self.pop_types[cell_pop] = pop_type
        
        
    def handle_projection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):
            
        weight = 1.0
        self.proj_pre_pops[projName] = prePop
        self.proj_post_pops[projName] = postPop
        
        proj_type = 'excitatory'
        
        if prePop in self.pop_types:
            if 'I' in self.pop_types[prePop]:
                proj_type = 'inhibitory'
                
        if type=='electricalProjection':
            proj_type = 'gap_junction'
            
        if synapse_obj:
            self.proj_syn_objs[projName] = synapse_obj
            if hasattr(synapse_obj,'erev') and convert_to_units(synapse_obj.erev,'mV')<self.CUTOFF_INH_SYN_MV:
                proj_type = 'inhibitory'
                
        if self.nl_network:
            syn = self.nl_network.get_child(synapse,'synapses')
            if syn:
                if syn.parameters:
                    if 'e_rev' in syn.parameters and syn.parameters['e_rev']<self.CUTOFF_INH_SYN_MV:
                        proj_type = 'inhibitory'
            
            proj = self.nl_network.get_child(projName,'projections')  
            if proj:
                if proj.weight:
                    proj_weight = evaluate(proj.weight, self.nl_network.parameters)
                    if proj_weight<0:
                        proj_type = 'inhibitory'
                    weight = float(abs(proj_weight))
                    
        if type=='continuousProjection':
            proj_type += 'continuous'
                        
        
        self.proj_weights[projName] = float(weight)
        self.proj_types[projName] = proj_type
        self.proj_conns[projName] = 0
        self.proj_tot_weight[projName] = 0
        
        if self.is_cell_level():
            pre_size = self.pop_sizes[prePop]
            post_size = self.pop_sizes[postPop]
            self.proj_individual_weights[projName] = np.zeros((pre_size, post_size))
            self.proj_individual_conn_numbers[projName] = np.zeros((pre_size, post_size))
            self.proj_individual_scaled_weights[projName] = np.zeros((pre_size, post_size))
        
        print_v("New projection: %s, %s->%s, weights? %s, type: %s"%(projName, prePop, postPop, weight, proj_type))


    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):
   
        pass
        #print_v("Projection finalising: "+projName+" -> "+prePop+" to "+postPop+" completed (%s; w: %s, conns: %s, tot w: %s)" % \
        #           (self.proj_types[projName], self.proj_weights[projName], self.proj_conns[projName], self.proj_tot_weight[projName]))

    sizes_ils = {}
    pops_ils = {}
    weights_ils = {}
    input_comp_obj_ils = {}
    

    def finalise_input_source(self, inputListId):
        
        pass