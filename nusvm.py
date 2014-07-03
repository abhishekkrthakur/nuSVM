"""
nuSVM 

__author__ : Abhishek Thakur
__credits__ : Mathieu Blondel
"""

import cvxopt
import cvxopt.solvers
import numpy as np
from numpy import linalg

def linear_kernel(x1, x2):
    return np.dot(x1, x2)

def polynomial_kernel(x, y, p=3):
    return (1 + np.dot(x, y)) ** p

def gaussian_kernel(x, y, sigma=5.0):
    return np.exp(-linalg.norm(x-y)**2 / (2 * (sigma ** 2)))

class nuSVM(object):

    def __init__(self, kernel=linear_kernel, nu=None, verbose = False, threshold = 1e-5):
        self.kernel = kernel
        self.nu = float(nu)
        self.verbose = verbose
        self.threshold = threshold
        assert self.nu >= 0 and self.nu <= 1.0

    def fit(self, X, y):
        n_samples, n_features = X.shape
        # Gram matrix
        #print X
        K = np.zeros((n_samples, n_samples))
        for i in range(n_samples):
            for j in range(n_samples):
                K[i,j] = self.kernel(X[i], X[j])

        P = cvxopt.matrix(np.outer(y,y) * K)

        q = cvxopt.matrix(np.ones(n_samples) * -1)
        A = cvxopt.matrix(y, (1,n_samples))
        b = cvxopt.matrix(0.0)

        tmp1 = np.diag(np.ones(n_samples) * -1)
        tmp2 = np.identity(n_samples)
        tmp3 = np.ones((1, n_samples))
        G = cvxopt.matrix(np.vstack((tmp1, tmp2, tmp3)))
        tmp1 = np.zeros(n_samples)
        tmp2 = np.ones(n_samples) * 1./n_samples
        tmp3 = self.nu
        h = cvxopt.matrix(np.hstack((tmp1, tmp2, tmp3)))

        solution = cvxopt.solvers.qp(P, q, G, h, A, b)
        if self.verbose: "nu =", self.nu

        # Lagrange multipliers
        a = np.ravel(solution['x'])

        # Support vectors have non zero lagrange multipliers
        sv = a > self.threshold
        ind = np.arange(len(a))[sv]
        self.a = a[sv]
        self.sv = X[sv]
        self.sv_y = y[sv]
        if self.verbose: print "%d support vectors out of %d points" % (len(self.a), n_samples)

        # Intercept
        self.b = 0
        for n in range(len(self.a)):
            self.b += self.sv_y[n]
            self.b -= np.sum(self.a * self.sv_y * K[ind[n],sv])
        self.b /= len(self.a)

        # Weight vector
        if self.kernel == linear_kernel:
            self.w = np.zeros(n_features)
            for n in range(len(self.a)):
                self.w += self.a[n] * self.sv_y[n] * self.sv[n]
        else:
            self.w = None

    def project(self, X):
        if self.w is not None:
            return np.dot(X, self.w) + self.b
        else:
            y_predict = np.zeros(len(X))
            for i in range(len(X)):
                s = 0
                for a, sv_y, sv in zip(self.a, self.sv_y, self.sv):
                    s += a * sv_y * self.kernel(X[i], sv)
                y_predict[i] = s
            return y_predict + self.b

    def predict(self, X):
        return np.sign(self.project(X))
