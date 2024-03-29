import os
import jax
import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from functools import partial

plot_params = {
    'font_size' : 20,
    'fig_size' : (10, 10)
}
gridspec = {
        'height_ratios' : [3, 0.2, 1],
        'hspace' : 0.,
        'left' : 0.15,
        'right' : 0.96,
        'top' : 0.95,
        'bottom' : 0.07,
    }


@partial(jax.jit, static_argnums=[0,1,2,3,4,6])
def eval_contour_vals(
    function,
    x_min,
    x_max,
    y_min,
    y_max,
    step_size=0.01,
    add_dof=False
):
    x_vals = jnp.arange(x_min, x_max, step_size)
    y_vals = jnp.arange(y_min, y_max, step_size)
    l,r = jnp.meshgrid(x_vals, y_vals)
    size = len(x_vals)
    args = jnp.reshape(jnp.stack([l,r],axis=2), (-1, 2))
    if add_dof:
        args = jnp.concatenate([args, jnp.zeros((args.shape[0], 1))], axis=1)
        #    jnp.array([x_vals, y_vals, jnp.zeros(len(x_vals))]).transpose()
        #)
        #trans_xy_vals = np.array(trans_xy_vals)
        #x_vals = jnp.expand_dims(trans_xy_vals[:,0], -1)
        #y_vals = jnp.expand_dims(trans_xy_vals[:,1], -1)
    z_vals = jax.vmap(function.evaluate, (0))(args)
    trans_xy_vals = jax.vmap(function.point_transform, (0))(args)
    return jnp.reshape(trans_xy_vals[:,0], (size, size)), jnp.reshape(trans_xy_vals[:,1], (size, size)), jnp.reshape(z_vals, (size, size))#jnp.apply_along_axis(function, 2, args)


def contour_2d(
        ax,
        function,
        plot_min_max,
        levels,
        contour_vals=None,
        return_contour_vals=False,
        add_dof=False,
    ):
    if contour_vals is not None:
        ax.contour(*contour_vals[:3], levels=contour_vals[3])
        return ax, contour_vals

    if plot_min_max is None:
        raise ValueError("Must specify max and min for x and y when plotting contours.")
    if levels is None:
        raise ValueError("Must specify contour levels when plotting pes_fxn countours.")
    x_min, x_max, y_min, y_max = plot_min_max
 
    x_vals, y_vals, z_vals = eval_contour_vals(
        function, x_min, x_max, y_min, y_max, add_dof=add_dof
    )
    ax.contour(x_vals, y_vals, z_vals, levels=levels)
    return ax, (x_vals, y_vals, z_vals, levels) 


def _plot_added_rot_dof(
        path,
        name,
        radius,
        pes_fxn=None,
        plot_min_max=None,
        levels=None,
        contour_vals=None,
    ):

    plot_min_max = (
        plot_min_max[0] + radius,        
        plot_min_max[1] + radius,        
        plot_min_max[2],        
        plot_min_max[3]
    )
    fig_size = (plot_params['fig_size'][0], plot_params['fig_size'][0]*1.2)
    _gridspec = dict(gridspec)
    _gridspec['height_ratios'] = _gridspec['height_ratios'][:] + [1]
    path_th = np.array(jnp.arctan2(path[:,0], path[:,-1]))
    time = np.linspace(0, 1, len(path_th))

    fig_xz, ax_xz = plt.subplots(4, 1, figsize=fig_size, gridspec_kw=_gridspec)
    _, contour_vals = _plot_path(
        ax_xz, path, pes_fxn, plot_min_max, levels,
        contour_vals=contour_vals, return_contour_vals=True, add_dof=True
    )
    ax_xz[3].plot(time, path_th)
    ax_xz[3].set_xlim(0,1)
    ax_xz[3].set_ylabel('Azimuthal [rad]', fontsize=plot_params['font_size'])
    
    
    fig_x, ax_x = plt.subplots(4, 1, figsize=fig_size, gridspec_kw=_gridspec)
    _, contour_vals = _plot_path(
        ax_x,
        jnp.concatenate([path[:,:-1], jnp.zeros((path.shape[0], 1))], axis=-1),
        pes_fxn, plot_min_max, levels,
        contour_vals=contour_vals, return_contour_vals=True, add_dof=True
    )
    ax_x[3].plot(time, path_th)
    ax_x[3].set_xlim(0,1)
    ax_x[3].set_ylabel('Azimuthal [rad]', fontsize=plot_params['font_size'])

    return [fig_xz, fig_x], [ax_xz, ax_x], ['', 'x'], contour_vals

 
def _plot_path(
        ax,
        path,
        pes_fxn=None,
        plot_min_max=None,
        levels=None,
        contour_vals=None,
        return_contour_vals=False,
        add_dof=False
    ):

    if pes_fxn is not None:
        _, contour_vals = contour_2d(
            ax[0],
            pes_fxn,
            plot_min_max,
            levels,
            contour_vals=contour_vals,
            add_dof=add_dof
        )
    else:
        contour_vals = None
    
    path = jax.vmap(pes_fxn.point_transform, (0))(path)
    ax[0].plot(path[:,0], path[:,1], color='r', linestyle='-')
    velocity = np.sqrt(np.sum((path[:-1] - path[1:])**2, axis=-1))
    ax[2].plot(np.linspace(0, 1, len(path)-1), velocity)

    return ax, contour_vals


def plot_path(
        path,
        name,
        pes_fxn=None,
        plot_min_max=None,
        levels=None,
        contour_vals=None,
        return_contour_vals=False,
        add_translation_dof=False,
        add_azimuthal_dof=False,
        plot_dir="./plots/",
    ):

   
    if add_azimuthal_dof:
        figs, axes, suffixes, contour_vals = _plot_added_rot_dof(
            path, name, add_azimuthal_dof, pes_fxn,
            plot_min_max=plot_min_max, levels=levels, contour_vals=contour_vals
        )
    elif add_translation_dof:
        ax.plot(path[:,0] + path[:,-1], path[:,1], color='r', linestyle='-')
        ax.plot(path[:,0], path[:,1], color='r', linestyle='-')
    else:
        fig, ax = plt.subplots(
            3, 1, figsize=plot_params['fig_size'], gridspec_kw=gridspec
        )
        ax, contour_vals = _plot_path(
            ax, path, pes_fxn,
            plot_min_max=plot_min_max, levels=levels, contour_vals=contour_vals
        )
        figs = [fig]
        axes = [ax]
        suffixes = ['']

    
    for fig, ax, suffix in zip(figs, axes, suffixes):
        plot_name = name
        if suffix != '':
            plot_name += "_" + suffix
        ax[0].set_title(plot_name, fontsize=plot_params['font_size']*1.5)
        ax[1].set_visible(False)
        ax[2].set_xlim(0, 1)
        if len(ax) > 2:
            for idx in range(1, len(ax)-1):
                ax[idx].xaxis.set_visible(False)
        ax[2].set_ylabel(
            r'$\dot{X}(t)$ [arb]', fontsize=plot_params['font_size']
        )
        ax[-1].set_xlabel('Time [arb]', fontsize=plot_params['font_size'])
        for idx in range(len(ax)):
            if idx == 1:
                continue
            ax[idx].xaxis.set_tick_params(labelsize=plot_params['font_size']*0.8)
            ax[idx].yaxis.set_tick_params(labelsize=plot_params['font_size']*0.8)
        fig.savefig(os.path.join(plot_dir, plot_name+".png"))
        print("Plotted", os.path.join(plot_dir, plot_name+".png"))
    
    if len(figs) == 1:
        figs = figs[0]
        axes = axes[0]
    if return_contour_vals:
        return figs, axes, contour_vals
    else:
        return figs, axes


def animate_optimization_2d(
        paths,
        title,
        contour_file,
        pes_fxn=None,
        plot_min_max=None,
        levels=None,
        contour_vals=None,
        add_translation_dof=False,
        add_azimuthal_dof=False,
        plot_dir='./plots/'
    ):


    fig, ax = plt.subplots()
    if pes_fxn is not None:
        ax = contour_2d(ax, pes_fxn, plot_min_max, levels, add_translation_dof=add_translation_dof)
    #ax = contour_2d(function, x_min, x_max, y_min, y_max, levels)
    ax.set_title(title)
    fig.savefig(contour_file + '.png')
    plot_artist = ax.plot([], [], color='red', linestyle='-')[0]


    def animation_function(path):
        if add_translation_dof:
            plot_artist.set_data(path[:,0] - path[:,-1], path[:,1])
        else:
            plot_artist.set_data(path[:,0], path[:,1])
        return plot_artist


    print("Plotting animation", len(paths), paths[0].shape)
    ani = animation.FuncAnimation(fig, animation_function, frames=paths)
    ani.save(os.path.join(plot_dir, contour_file + ".gif"))

