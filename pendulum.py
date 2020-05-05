"""
Author:
    Arun Leander

More Info:
    github.com/LeanderSilur/Snippets/blob/master/pendulum/
"""

import math
import scipy.integrate
import numpy as np


"""
θ, φ            angles
dθ, dφ          velocities
l               length
m               mass
c_a             mechanical friction
c_d             drag friction
f               force
w               wind velocity
"""
class Pendulum(object):
    def __init__(self):
        # angles
        self.θ = math.pi / 2
        self.φ = 0

        # velocities
        self.dθ = 0
        self.dφ = 0

        # length, mass
        self.l = 1
        self.m = 1

        # mechanical friction, drag friction
        self.c_a = 0
        self.c_d = 0

        # force
        self.f = [0, 0, -10]

        # wind
        self.w = [0, 0, 0]
    
    # transform θ and φ to euler coordinates
    @staticmethod
    def sphere_to_cartesian(θ, φ):
        x = math.sin(θ) * math.cos(φ)
        y = math.sin(θ) * math.sin(φ)
        z = - math.cos(θ)
        return [x, y, z]
    @staticmethod
    def cartesian_to_sphere(direction):
        if (direction[0] == 0 or direction[1] == 0):
            φ = 0.0
            θ = 0.0 if direction[2] < 0 else math.pi
        else:
            φ = math.atan2(direction[1], direction[0])
            x2 = math.cos(-φ) * direction[0] - math.sin(-φ) * direction[1]
            θ = math.atan2(x2, -direction[2])
        return θ, φ
    
    def get_coords(self):
        return [self.l * c for c in Pendulum.sphere_to_cartesian(self.θ, self.φ)]

    def set_coords(self, direction):
        self.θ, self.φ = Pendulum.cartesian_to_sphere(direction)
        
    def do_steps(self, frame_step=0.1, frames=1):
        # the pendulum derivatives
        def pendulum_derivatives(y, t, l, m, c_a, c_d, f, w):
            fx, fy, fz = f
            wx, wy, wz = w
            θ, dθ, φ, dφ = y

            vw2 = math.pow(-l *math.sin(θ) *math.sin(φ) *dφ + l *math.cos(θ) *math.cos(φ) *dθ - wx, 2)
            vw2 += math.pow(l *math.sin(θ) *math.cos(φ) *dφ + l *math.cos(θ) *math.sin(φ) *dθ - wy, 2)
            vw2 += math.pow(l *math.sin(θ) *dθ - wz, 2)

            vw121 = math.sqrt(vw2)
            
            c_θ = 0
            c_φ = 0
            # Angular Friction [c_a]
            c_θ += c_a * l * l * dθ
            c_φ += c_a * l * l * dφ * math.pow(math.sin(θ), 2)
            # Drag Friction    [c_d]
            c_θ += c_d *m* vw121 * (
                    2 *l *math.cos(θ) * math.cos(φ) *(l * dθ * math.cos(θ) * math.cos(φ) -l * dφ * math.sin(θ) * math.sin(φ) - wx)
                + 2 *l *math.cos(θ) * math.sin(φ)* (l* dθ* math.cos(θ) *math.sin(φ) +l *dφ *math.sin(θ) *math.cos(φ) - wy)
                + 2 *l *math.sin(θ) *(l *dθ *math.sin(θ) - wz)
                )
            c_φ += c_d *m* vw121 * (
                2 *l *math.sin(θ) *(l* dφ* math.sin(θ)* (math.pow(math.sin(φ), 2)
                + math.pow(math.cos(φ), 2))
                + wx*math.sin(φ) - wy*math.cos(φ))
                )

            d_θ = dθ
            d_dθ = (math.pow(dφ, 2) / 2 * math.sin(2*θ)
                + math.sin(θ)/l * fz
                + math.cos(θ)/l * (fx * math.cos(φ) + fy * math.sin(φ))
                - c_θ / m / l / l)

            d_φ = dφ
            d_dφ =  ((-2) * dθ * dφ / math.tan(θ)
                + 1/(math.sin(θ) * l) * (-fx * math.sin(φ) + fy * math.cos(φ))
                - c_φ / m / l / l / math.pow(math.sin(θ), 2))

            return [dθ, d_dθ, d_φ, d_dφ]
        
        # intial values
        y0 = [self.θ, self.dθ, self.φ, self.dφ]
        t = np.arange(0, (frames + 1) * frame_step, frame_step)

        args = [self.l, self.m, self.c_a, self.c_d, self.f, self.w]
        # create the solver
        y = scipy.integrate.odeint(pendulum_derivatives, y0, t, args=tuple(args))

        [self.θ, self.dθ, self.φ, self.dφ] = y[-1]
        return t, y

if __name__ == "__main__":
    pen = Pendulum()

    pen.θ = math.pi/2
    pen.f = [0, 0, -10]
    pen.do_steps(0.04)

    print(pen.θ)

def testing():

    # import plotting functions
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import mpl_toolkits.mplot3d.axes3d as p3

    # create 2d graphs
    def plt_2d(t, y):
        y = np.swapaxes(y, 0, 1)
        fig = plt.figure()
        ax = plt.gca()
        for name, values in zip(['θ(t)' ,'dθ(t)', 'φ(t)', 'dφ(t)'], y):
            ax.plot(t, values, label=name)
        ax.legend(loc='best')
        ax.set_xlabel('t'), ax.grid()
        ax.axis([None, None, -5, 5])

    def plt_3d(frame_step, y, use_grid=True):
        # plot the animation
        fig = plt.figure()
        ax = p3.Axes3D(fig)

        string, = ax.plot(*np.zeros((3, 2)), color='k', lw=1, zorder=3)
        bob, = ax.plot([0], [0], 'ro', color='#dd5500', zorder=4)
        projx, = ax.plot(*np.zeros((3, 2)), color='r', alpha=0.3, lw=1)
        projy, = ax.plot(*np.zeros((3, 2)), color='g', alpha=0.3, lw=1)
        projz, = ax.plot(*np.zeros((3, 2)), color='b', alpha=0.3, lw=1)
        positions = [Pendulum.sphere_to_cartesian(x[0], x[2]) for x in y]
        positions = np.array(positions).reshape(-1, 3, 1)
        swapped = np.swapaxes(positions, 0, 1).reshape((3, -1))
        trace = plt.plot(*swapped, color='#cccccc', lw=1)[0]

        def drawPendulum(i):
            x, y, z = positions[i,:,0]
            bob.set_data(positions[i][:2])
            bob.set_3d_properties(positions[i][2])
            string_data = np.concatenate([np.zeros((3, 1)), positions[i]], axis = 1)
            string.set_data(string_data[:2])
            string.set_3d_properties(string_data[2])
            projx.set_data([0, x], [y, y])
            projx.set_3d_properties([z, z])
            projy.set_data([x, x], [0, y])
            projy.set_3d_properties([z, z])
            projz.set_data([x, x], [y, y])
            projz.set_3d_properties([0, z])
            return bob, string, trace, projx, projy, projz

        #create a grid
        if use_grid:
            divisions = 5
            def grid(pmin, pmax, other = 0, pdiv=5):
                if other: return np.repeat(np.linspace(pmin, pmax, pdiv).reshape(-1, 1), pdiv, axis = 1)
                return np.repeat(np.linspace(pmin, pmax, pdiv).reshape(1, -1), pdiv, axis = 0)
            ax.plot_wireframe(grid(0, 0), grid(-1, 1), grid(-1, 1, 1), colors='r', alpha=0.05)
            ax.plot_wireframe(grid(-1, 1), grid(0, 0), grid(-1, 1, 1), colors='g', alpha=0.05)
            ax.plot_wireframe(grid(-1, 1, 1), grid(-1, 1), grid(0, 0), colors='b', alpha=0.05)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        ax.auto_scale_xyz
        pendAnim = animation.FuncAnimation(fig, drawPendulum, frames= len(positions),
                                            interval=float(1000*frame_step), blit=False, repeat=False)
        plt.show(pendAnim)
        return pendAnim

    pen = Pendulum()

    pen.set_coords([1, 1, -2])
    pen.dφ = 1
    pen.c_d = 0.5
    pen.w[0] = 1
    
    print(pen.w)

    fps = 24
    frame_step = 1/fps
    t, y = pen.do_steps(frame_step, 120)
    plt_3d(frame_step, y)
    plt.show()
    plt_2d(t, y)