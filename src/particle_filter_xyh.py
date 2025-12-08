import numpy as np


'''
heavily inspired by: https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python
https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python/blob/master/12-Particle-Filters.ipynb

'''

X = 0
Y = 1
H = 2
V = 3
W = 4

def gen_gaussian_particles(num=50, std=(10,10,10,10),init=(0,0,0,0)):
    '''
    Generate a set of random particles centered on an initial guess
    of X,Y and heading
    
    :param num: Number of particles
    :param std: Standard deviation for each dimension
    :param init: Initial guess (mean)
    '''
    dims = len(std)
    particles = np.empty((num,dims + 1))
    particles[:,X] = init[X] + (np.random.randn(num) * std[X])
    particles[:,Y] = init[Y] + (np.random.randn(num) * std[Y])
    particles[:,H] = init[H] + (np.random.randn(num) * std[H])
    particles[:,V] = np.abs(init[V] + (np.random.randn(num) * std[V]))
    
    particles[:,H] = (particles[:,H] + 180.)%360. - 180.
    particles[:,W] = 1./num
    return particles



def predict_particles(particles):
    particles[:,X] += particles[:,V] * np.cos(np.radians(particles[:,H]))
    particles[:,Y] += particles[:,V] * np.cos(np.radians(particles[:,H]))
    return particles


def jitter_particles(particles, std=[0.25,0.25,0.25,0.25]):
    '''
    Move particles randomly.
    This can be used in lieu of an update step, if no control input is known
    Can also be used to help avoid particle starvation.
    Larger std will make filter more robust, but less accurate
    
    :param particles: particle set to be jitterd
    :param std: standard deviation
    '''
    num = particles.shape[0]
    # Update heading
    particles[:,H] += np.random.randn(num) * std[H]
    particles[:,H] = (particles[:,H] + 180.)%360. - 180.

    # Move particles
    particles[:,X] += np.random.randn(num) * std[X]
    particles[:,Y] += np.random.randn(num) * std[Y]
    particles[:,V] += np.random.randn(num) * std[V]

    return particles
    

def update_particles(particles, likelihood):
    '''
    Docstring for update_particles
    
    :param particles: Description
    :param likelihood: Description
    '''
    particles[:,W] *= likelihood
    particles[:,W] += 1.e-300
    particles[:,W] /= sum(particles[:,W])
    return particles


def resample_particles(particles):
    '''
    Multinomial Resampling
    
    :param particles: Description
    '''
    cum_sum = np.cumsum(particles[:,W])
    cum_sum[-1] = 1
    i = np.searchsorted(cum_sum, np.random.random(particles.shape[0]))

    particles[:] = particles[i]
    particles[:,W] = 1./particles.shape[0]

    return particles


def estimate(particles):
    '''
    Docstring for estimate
    
    :param particles: Description
    '''
    mean = np.average(particles[:,X:W],weights=particles[:,W],axis=0)
    var = np.average((particles[:,X:W] - mean)**2, weights=particles[:,W],axis=0)

    #i = np.argmax(particles[:,W])
    #mean = particles[i,:]
    return mean,var


if __name__ == '__main__':
    p = gen_gaussian_particles()
    p = jitter_particles(p)
    p = update_particles(p, np.ones_like(p[:,W])*.1)
    p = resample_particles(p)
    print(p)
    print(estimate(p))